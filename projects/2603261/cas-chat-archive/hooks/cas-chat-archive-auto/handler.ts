import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import fs from "node:fs/promises";

const execFileAsync = promisify(execFile);

function gatewayNameFromEnv(): string {
  const direct = process.env.OPENCLAW_GATEWAY_NAME?.trim();
  if (direct) return direct;

  const cfg = process.env.OPENCLAW_CONFIG_PATH ?? "";
  const m = cfg.match(/\/gateways\/([^/]+)\//);
  if (m?.[1]) return m[1];

  return "default";
}

function isoFromEvent(event: any): string {
  try {
    const t = event?.timestamp;
    if (t && typeof t.toISOString === "function") return t.toISOString();
    if (typeof t === "string") return new Date(t).toISOString();
    if (typeof t === "number") return new Date(t).toISOString();
  } catch {}
  return new Date().toISOString();
}

// 动态解析：相对于 handler.ts 所在目录（hooks/cas-chat-archive-auto/），
// 向上两级到 Skill 根目录，再进入 scripts/cas_archive.py
// 兼容任意 clawhub 安装路径，无需配置 CAS_ARCHIVE_SCRIPT 环境变量
function defaultCasScriptPath(): string {
  const here = path.dirname(fileURLToPath(import.meta.url));
  return path.resolve(here, "..", "..", "scripts", "cas_archive.py");
}

function allowedRoots(gateway: string): string[] {
  const gwRoot = path.join(os.homedir(), ".openclaw", "gateways", gateway);
  const roots = [
    path.resolve(path.join(gwRoot, "uploads")),
    path.resolve(path.join(gwRoot, "state", "media", "inbound")),
    path.resolve(path.join(gwRoot, "state", "media", "outbound")),
  ];

  const extra = (process.env.CAS_ALLOWED_ATTACHMENT_ROOTS ?? "").trim();
  if (extra) {
    for (const p of extra.split(path.delimiter).map((s) => s.trim()).filter(Boolean)) {
      roots.push(path.resolve(p));
    }
  }
  return roots;
}

function isPathAllowed(filePath: string, roots: string[]): boolean {
  try {
    const abs = path.resolve(filePath);
    return roots.some((root) => abs === root || abs.startsWith(root + path.sep));
  } catch {
    return false;
  }
}

async function fileExists(p: string): Promise<boolean> {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

function agentIdFromEvent(event: any): string {
  const raw = String(event?.sessionKey || event?.context?.sessionKey || "").trim();
  if (!raw) return "unknown-agent";
  if (raw.startsWith("agent:")) {
    const parts = raw.split(":");
    if (parts.length >= 2 && parts[1]) return parts[1];
  }
  return raw;
}

async function runCasSetupIfNeeded(archiveRoot: string, scriptPath: string): Promise<void> {
  // 检查标志文件
  const flagPath = path.join(
    archiveRoot.replace(/^~/, os.homedir()),
    ".cas_initialized"
  );
  try {
    await fs.access(flagPath);
    return; // 已初始化，跳过
  } catch {
    // 未初始化，继续
  }

  // 找 cas_setup.py（与 cas_archive.py 同目录）
  const setupScript = path.join(path.dirname(scriptPath), "cas_setup.py");
  try {
    await fs.access(setupScript);
  } catch {
    return; // setup 脚本不存在，跳过
  }

  try {
    await execFileAsync("python3", [setupScript, "--auto",
      "--archive-root", archiveRoot]);
    console.log("[cas-chat-archive] 首次运行：已自动初始化复盘体系");
  } catch {
    // 静默失败，不阻断主流程
  }
}

async function runCasRecordBundle(payload: any, gateway: string, scopeMode: string, agentId: string): Promise<void> {
  const script = process.env.CAS_ARCHIVE_SCRIPT || defaultCasScriptPath();
  if (!(await fileExists(script))) {
    throw new Error(`CAS script not found: ${script}`);
  }

  const archiveRoot = process.env.CAS_ARCHIVE_ROOT || "~/.openclaw/chat-archive";
  const diskWarn = process.env.CAS_DISK_WARN_MB || "500";
  const diskMin = process.env.CAS_DISK_MIN_MB || "200";
  const maxAsset = process.env.CAS_MAX_ASSET_MB || "100";

  const tmp = path.join(os.tmpdir(), `cas-hook-${process.pid}-${Date.now()}.json`);
  await fs.writeFile(tmp, JSON.stringify(payload), "utf-8");

  try {
    const args = [
      script,
      "--archive-root",
      archiveRoot,
      "record-bundle",
      "--gateway",
      gateway,
      "--payload-file",
      tmp,
      "--scope-mode",
      scopeMode,
      "--disk-warn-mb",
      diskWarn,
      "--disk-min-mb",
      diskMin,
      "--max-asset-mb",
      maxAsset,
    ];

    if (scopeMode === "agent") {
      args.push("--agent", agentId);
    }

    await execFileAsync("python3", args);
  } finally {
    await fs.rm(tmp, { force: true });
  }
}

function strictMode(): boolean {
  const raw = (process.env.CAS_STRICT_MODE ?? "false").trim().toLowerCase();
  return ["1", "true", "yes", "on"].includes(raw);
}

export default async function handler(event: any): Promise<void> {
  try {
    if (!event || event.type !== "message") return;

    const gateway = gatewayNameFromEnv();
    const ts = isoFromEvent(event);
    const roots = allowedRoots(gateway);
    const blocked: string[] = [];
    const scopeMode = (process.env.CAS_SCOPE_MODE || "gateway").trim().toLowerCase() === "agent" ? "agent" : "gateway";
    const agentId = agentIdFromEvent(event);

    const inbound = { sender: "User", text: "", attachments: [] as string[] };
    const outbound = { sender: "Assistant", text: "", attachments: [] as string[] };

    if (event.action === "preprocessed") {
      const ctx = event.context || {};
      inbound.sender = ctx.senderName || ctx.from || "User";
      inbound.text = ctx.bodyForAgent || ctx.content || ctx.body || ctx.transcript || "";

      const candidate = ctx.mediaPath;
      if (typeof candidate === "string" && candidate) {
        if (isPathAllowed(candidate, roots)) inbound.attachments.push(candidate);
        else blocked.push(candidate);
      }
    } else if (event.action === "sent") {
      const ctx = event.context || {};
      if (ctx.success === false) return;
      outbound.sender = "Assistant";
      outbound.text = ctx.content || "";

      const candidate = ctx.mediaPath;
      if (typeof candidate === "string" && candidate) {
        if (isPathAllowed(candidate, roots)) outbound.attachments.push(candidate);
        else blocked.push(candidate);
      }
    } else {
      return;
    }

    const hasArchiveContent = Boolean(inbound.text || outbound.text || inbound.attachments.length > 0 || outbound.attachments.length > 0);
    if (!hasArchiveContent) {
      if (blocked.length > 0) {
        const msg = `[cas-chat-archive-auto] blocked attachments outside allowlist: ${blocked.join(", ")}`;
        if (strictMode()) throw new Error(msg);
        console.error(msg);
      }
      return;
    }

    const payload = {
      timestamp: ts,
      agent: agentId,
      inbound,
      outbound,
    };

    await runCasRecordBundle(payload, gateway, scopeMode, agentId);

    // 首次运行自动初始化复盘体系
    const casScript = process.env.CAS_ARCHIVE_SCRIPT || defaultCasScriptPath();
    const casArchiveRoot = (process.env.CAS_ARCHIVE_ROOT || "~/.openclaw/chat-archive");
    await runCasSetupIfNeeded(casArchiveRoot, casScript).catch(() => {});

    if (blocked.length > 0) {
      const msg = `[cas-chat-archive-auto] blocked attachments outside allowlist: ${blocked.join(", ")}`;
      if (strictMode()) throw new Error(msg);
      console.error(msg);
    }
  } catch (err: any) {
    const msg = err?.message || String(err);
    if (strictMode()) throw err;
    console.error(`[cas-chat-archive-auto] fail-soft: ${msg}`);
  }
}
