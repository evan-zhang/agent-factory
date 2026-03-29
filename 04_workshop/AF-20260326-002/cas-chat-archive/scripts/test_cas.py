#!/usr/bin/env python3
"""CAS Chat Archive - Test Script"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


def run_test(name: str, cmd: list[str], expect_success: bool = True, env: dict | None = None) -> bool:
    print(f"\n=== Test: {name} ===")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    ok = (result.returncode == 0)

    if expect_success and not ok:
        print(f"✗ Failed: {result.stderr}")
        return False
    if not expect_success and ok:
        print("✗ Failed: expected failure but command succeeded")
        return False

    print("✓ Passed")
    if result.stdout:
        print(f"Output: {result.stdout[:200]}")
    if result.stderr and not expect_success:
        print(f"Expected error: {result.stderr[:200]}")
    return True


def run_internal_hook(handler_path: Path, event_payload: dict, env: dict) -> subprocess.CompletedProcess:
    node_code = r'''
const fs = require("fs");
const path = require("path");
const ts = require("typescript");
const Module = require("module");

(async () => {
  const handlerPath = process.argv[1];
  const payloadJson = process.argv[2];
  const source = fs.readFileSync(handlerPath, "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      esModuleInterop: true,
      moduleResolution: ts.ModuleResolutionKind.NodeJs,
    },
    fileName: handlerPath,
  }).outputText;

  const m = new Module(handlerPath, module);
  m.filename = handlerPath;
  m.paths = Module._nodeModulePaths(path.dirname(handlerPath));
  m._compile(compiled, handlerPath + ".compiled.js");
  const fn = m.exports.default || m.exports;
  await fn(JSON.parse(payloadJson));
})().catch((err) => {
  console.error(err && (err.stack || err.message) || String(err));
  process.exit(1);
});
'''
    return subprocess.run(
        ["node", "-e", node_code, str(handler_path), json.dumps(event_payload, ensure_ascii=False)],
        capture_output=True,
        text=True,
        env=env,
    )


def main() -> int:
    temp_dir = tempfile.mkdtemp(prefix="cas-test-")
    print(f"Test directory: {temp_dir}")

    try:
        script_dir = Path(__file__).parent
        cas_script = script_dir / "cas_archive.py"
        hook_script = script_dir / "cas_hook.py"
        internal_hook_handler = script_dir.parent / "hooks" / "cas-chat-archive-auto" / "handler.ts"

        if not cas_script.exists():
            print(f"Error: cas_archive.py not found at {cas_script}", file=sys.stderr)
            return 1
        if not internal_hook_handler.exists():
            print(f"Error: internal hook handler not found at {internal_hook_handler}", file=sys.stderr)
            return 1

        base_cmd = [sys.executable, str(cas_script), "--archive-root", temp_dir]
        tests_passed = 0
        tests_failed = 0

        tests = [
            ("Initialize archive", base_cmd + ["init", "--gateway", "test-gateway"], True),
            (
                "Record inbound message",
                base_cmd + [
                    "record-message",
                    "--gateway",
                    "test-gateway",
                    "--direction",
                    "inbound",
                    "--sender",
                    "TestUser",
                    "--text",
                    "Test message 1",
                ],
                True,
            ),
            (
                "Record outbound message",
                base_cmd + [
                    "record-message",
                    "--gateway",
                    "test-gateway",
                    "--direction",
                    "outbound",
                    "--sender",
                    "Assistant",
                    "--text",
                    "Test response 1",
                ],
                True,
            ),
            (
                "Reject invalid gateway traversal",
                base_cmd + ["init", "--gateway", "../escape"],
                False,
            ),
        ]

        for name, cmd, expected_ok in tests:
            if run_test(name, cmd, expect_success=expected_ok):
                tests_passed += 1
            else:
                tests_failed += 1

        # RFC3339 Z timestamp compatibility (py3.10 regression coverage)
        bundle_payload_z_path = Path(temp_dir) / "bundle-z.json"
        bundle_payload_z_path.write_text(
            json.dumps(
                {
                    "timestamp": "2026-03-27T03:22:00.000Z",
                    "inbound": {"sender": "Evan", "text": "bundle-z-in", "attachments": []},
                    "outbound": {"sender": "Assistant", "text": "bundle-z-out", "attachments": []},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        if run_test(
            "Record bundle with Z timestamp",
            base_cmd
            + [
                "record-bundle",
                "--gateway",
                "test-gateway",
                "--payload-file",
                str(bundle_payload_z_path),
            ],
        ):
            tests_passed += 1
        else:
            tests_failed += 1

        # asset test
        test_file = Path(temp_dir) / "test-asset.txt"
        test_file.write_text("This is a test asset")
        if run_test(
            "Record asset",
            base_cmd
            + [
                "record-asset",
                "--gateway",
                "test-gateway",
                "--direction",
                "inbound",
                "--source",
                str(test_file),
            ],
        ):
            tests_passed += 1
        else:
            tests_failed += 1

        # Hook long text test (argv overflow regression)
        payload = {
            "inbound": {"text": "x" * 300000, "attachments": []},
            "outbound": {"text": "ok", "attachments": []},
            "timestamp": "2026-03-27T06:00:00+08:00",
        }
        env = os.environ.copy()
        env["OPENCLAW_GATEWAY_NAME"] = "hook-test"
        env["CAS_ARCHIVE_ROOT"] = temp_dir
        print("\n=== Test: Hook handles long message ===")
        res = subprocess.run([sys.executable, str(hook_script)], input=json.dumps(payload), text=True, capture_output=True, env=env)
        if res.returncode == 0:
            print("✓ Passed")
            tests_passed += 1
        else:
            print(f"✗ Failed: {res.stderr}")
            tests_failed += 1

        # record-bundle test (single-process turn archive)
        bundle_payload_path = Path(temp_dir) / "bundle.json"
        bundle_payload_path.write_text(
            json.dumps(
                {
                    "timestamp": "2026-03-27T06:00:00+08:00",
                    "inbound": {"sender": "Evan", "text": "bundle-in", "attachments": []},
                    "outbound": {"sender": "Assistant", "text": "bundle-out", "attachments": []},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        if run_test(
            "Record bundle",
            base_cmd
            + [
                "record-bundle",
                "--gateway",
                "test-gateway",
                "--payload-file",
                str(bundle_payload_path),
            ],
        ):
            tests_passed += 1
        else:
            tests_failed += 1

        # Hook attachment allowlist test (must block /etc/hosts)
        blocked_payload = {
            "inbound": {"text": "probe", "attachments": ["/etc/hosts"]},
            "outbound": {"text": "ok", "attachments": []},
            "timestamp": "2026-03-27T06:00:00+08:00",
        }
        env_block = os.environ.copy()
        env_block["OPENCLAW_GATEWAY_NAME"] = "hook-test"
        env_block["CAS_ARCHIVE_ROOT"] = temp_dir
        print("\n=== Test: Hook blocks attachment outside allowlist (fail-soft) ===")
        res_block = subprocess.run(
            [sys.executable, str(hook_script)],
            input=json.dumps(blocked_payload),
            text=True,
            capture_output=True,
            env=env_block,
        )
        hook_asset_dir = Path(temp_dir) / "hook-test" / "assets" / datetime.now().strftime('%Y-%m-%d') / "inbound"
        leaked = list(hook_asset_dir.glob("*hosts*")) if hook_asset_dir.exists() else []
        if res_block.returncode == 0 and not leaked:
            print("✓ Passed")
            tests_passed += 1
        else:
            print("✗ Failed: expected no leak and fail-soft rc=0")
            print("rc:", res_block.returncode, "leaked:", [p.name for p in leaked])
            tests_failed += 1

        # Internal hook (handler.ts) integration test: agent scope write path
        print("\n=== Test: Internal hook (handler.ts) agent scope archive ===")
        allowed_media = Path(temp_dir) / "internal-allowed.txt"
        allowed_media.write_text("internal hook allowed media", encoding="utf-8")

        env_internal = os.environ.copy()
        env_internal["OPENCLAW_GATEWAY_NAME"] = "internal-hook-test"
        env_internal["CAS_ARCHIVE_ROOT"] = temp_dir
        env_internal["CAS_ARCHIVE_SCRIPT"] = str(cas_script)
        env_internal["CAS_SCOPE_MODE"] = "agent"
        env_internal["CAS_ALLOWED_ATTACHMENT_ROOTS"] = temp_dir

        internal_event = {
            "type": "message",
            "action": "preprocessed",
            "timestamp": "2026-03-27T03:22:00.000Z",
            "sessionKey": "agent:factory-orchestrator:main",
            "context": {
                "senderName": "Evan",
                "bodyForAgent": "internal-hook-message",
                "mediaPath": str(allowed_media),
            },
        }
        res_internal = run_internal_hook(internal_hook_handler, internal_event, env_internal)
        internal_day = "2026-03-27"
        internal_log = Path(temp_dir) / "internal-hook-test" / "agents" / "factory-orchestrator" / "logs" / f"{internal_day}.md"
        if res_internal.returncode == 0 and internal_log.exists() and "internal-hook-message" in internal_log.read_text(encoding="utf-8", errors="replace"):
            print("✓ Passed")
            tests_passed += 1
        else:
            print("✗ Failed")
            print("rc:", res_internal.returncode)
            print("stdout:", res_internal.stdout[:200])
            print("stderr:", res_internal.stderr[:200])
            tests_failed += 1

        # Internal hook allowlist block test (fail-soft)
        print("\n=== Test: Internal hook blocks out-of-root attachment (fail-soft) ===")
        blocked_event = {
            "type": "message",
            "action": "preprocessed",
            "timestamp": "2026-03-27T03:22:00.000Z",
            "sessionKey": "agent:factory-orchestrator:main",
            "context": {
                "senderName": "Evan",
                "bodyForAgent": "blocked-probe",
                "mediaPath": "/etc/hosts",
            },
        }
        res_internal_block = run_internal_hook(internal_hook_handler, blocked_event, env_internal)
        internal_asset_dir = Path(temp_dir) / "internal-hook-test" / "agents" / "factory-orchestrator" / "assets" / internal_day / "inbound"
        leaks = list(internal_asset_dir.glob("*hosts*")) if internal_asset_dir.exists() else []
        if res_internal_block.returncode == 0 and not leaks:
            print("✓ Passed")
            tests_passed += 1
        else:
            print("✗ Failed")
            print("rc:", res_internal_block.returncode, "leaks:", [p.name for p in leaks])
            print("stderr:", res_internal_block.stderr[:200])
            tests_failed += 1

        # Concurrency regression test for session-state write
        print("\n=== Test: Concurrent record-message stability ===")
        stress_cmd = base_cmd + [
            "record-message",
            "--gateway",
            "test-gateway",
            "--direction",
            "inbound",
            "--text",
            "stress",
        ]
        procs = [subprocess.Popen(stress_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(20)]
        errs = []
        for p in procs:
            out, err = p.communicate()
            if p.returncode != 0:
                errs.append((p.returncode, err.strip(), out.strip()))
        if not errs:
            print("✓ Passed")
            tests_passed += 1
        else:
            print(f"✗ Failed: {len(errs)} process(es) returned non-zero")
            print(errs[:3])
            tests_failed += 1

        # Verify log content
        log_file = Path(temp_dir) / "test-gateway" / "logs" / f"{datetime.now().strftime('%Y-%m-%d')}.md"
        if log_file.exists():
            content = log_file.read_text()
            if "Test message 1" in content and "Test response 1" in content:
                print("\n=== Test: Verify log content ===")
                print("✓ Passed")
                tests_passed += 1
            else:
                print("\n=== Test: Verify log content ===")
                print("✗ Failed: Expected content not found")
                tests_failed += 1
        else:
            print("\n=== Test: Verify log file ===")
            print(f"✗ Failed: Log file not found at {log_file}")
            tests_failed += 1

        # Verify asset archive
        asset_dir = Path(temp_dir) / "test-gateway" / "assets" / datetime.now().strftime('%Y-%m-%d') / "inbound"
        if asset_dir.exists() and list(asset_dir.glob("in-*-test-asset.txt")):
            print("\n=== Test: Verify asset archive ===")
            print("✓ Passed")
            tests_passed += 1
        else:
            print("\n=== Test: Verify asset archive ===")
            print(f"✗ Failed: Asset not found in {asset_dir}")
            tests_failed += 1

        print(f"\n{'=' * 50}")
        print(f"Tests passed: {tests_passed}")
        print(f"Tests failed: {tests_failed}")
        print(f"{'=' * 50}")

        return 0 if tests_failed == 0 else 1

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\nCleaned up test directory: {temp_dir}")


if __name__ == "__main__":
    sys.exit(main())
