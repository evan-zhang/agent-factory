import fs from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";

const HOOK_KEY = "instinct-learner";

function safeNumber(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) return undefined;
  return value;
}

function safePositiveInt(value, fallback) {
  const n = typeof value === "number" && Number.isFinite(value) ? Math.floor(value) : NaN;
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

function parseUsedInstinctIdsFromAssistantText(text) {
  const s = String(text || "");
  const ids = new Set();
  const re = /<!--\s*instinct:([a-zA-Z0-9][a-zA-Z0-9_.:-]{0,200})\s*-->/g;
  let m = re.exec(s);
  while (m) {
    if (m[1]) ids.add(m[1]);
    m = re.exec(s);
  }
  return Array.from(ids);
}

function hasCorrectionSignal(text) {
  const s = String(text || "");
  return /你说错|不对|应该|正确|别这样|不要这样|不是/.test(s);
}

export default async function instinctLearnerHook(event) {
  const ctx = event?.context;
  if (!ctx || typeof ctx !== "object") return;

  const cfg = ctx.cfg ?? {};
  const hookCfg =
    cfg?.hooks?.internal?.entries?.[HOOK_KEY] && typeof cfg.hooks.internal.entries[HOOK_KEY] === "object"
      ? cfg.hooks.internal.entries[HOOK_KEY]
      : undefined;
  if (!hookCfg || hookCfg.enabled === false) return;

  const workspaceDir = ctx.workspaceDir;
  if (typeof workspaceDir !== "string" || workspaceDir.trim().length === 0) return;

  const outDir = path.join(workspaceDir, ".openclaw", "instinct-learner");
  const statePath = path.join(outDir, "state.json");
  const sessionLogPath = path.join(outDir, "session.jsonl");

  const skillDir = path.join(workspaceDir, "skills", "instinct-learner");
  // Store instinct data under the workspace (not inside the skill code dir),
  // so validate/prune operate on the same runtime dataset even if the skill is read-only.
  const dataDir = path.join(workspaceDir, "instincts");
  const scriptsDir = path.join(skillDir, "scripts");
  const loaderScript = path.join(scriptsDir, "load_instincts.py");
  const extractScript = path.join(scriptsDir, "extract_instinct.py");
  const validateScript = path.join(scriptsDir, "validate_instinct.py");
  const pruneScript = path.join(scriptsDir, "prune_instincts.py");

  async function readState() {
    try {
      const raw = await fs.readFile(statePath, "utf-8");
      const v = JSON.parse(raw);
      return v && typeof v === "object" ? v : {};
    } catch {
      return {};
    }
  }
  async function writeState(state) {
    await fs.mkdir(path.dirname(statePath), { recursive: true });
    await fs.writeFile(statePath, JSON.stringify(state, null, 2), "utf-8");
  }
  async function appendJsonl(obj) {
    await fs.mkdir(path.dirname(sessionLogPath), { recursive: true });
    await fs.appendFile(sessionLogPath, JSON.stringify(obj) + "\n", "utf-8");
  }

  if (event?.type === "agent" && event.action === "bootstrap" && Array.isArray(ctx.bootstrapFiles)) {
    await fs.mkdir(outDir, { recursive: true });
    const outPath = path.join(outDir, "MEMORY.md");
    const k = safeNumber(hookCfg.k);
    const args = [loaderScript, "--base-dir", skillDir, "--data-dir", dataDir, "--query", "", "--format", "markdown"];
    if (k !== undefined) args.push("--k", String(Math.max(0, Math.min(10, k))));
    const res = spawnSync("python3", args, { encoding: "utf-8", timeout: 4000 });
    if (res.status !== 0) return;
    const md = (res.stdout ?? "").trim();
    if (!md) return;
    const content = [
      "# Active Instincts (auto-injected)",
      "",
      "## 使用约定（用于自动验证）",
      "",
      "- 如果你在本轮回复中**实际参考/应用**了某条 instinct，请在回复末尾追加一个 HTML 注释标记：",
      "  - 形如：`<!-- instinct:<instinct_id> -->`",
      "  - 可多条（每条一行）。",
      "",
      md,
      "",
    ].join("\n");
    await fs.writeFile(outPath, content, "utf-8");
    ctx.bootstrapFiles.push({ name: "MEMORY.md", path: outPath, content, missing: false });
    return;
  }

  if (event?.type === "message" && (event.action === "received" || event.action === "sent")) {
    const content = String(event?.context?.content ?? "");
    if (content.trim()) {
      await appendJsonl({
        sessionKey: String(event?.sessionKey ?? ""),
        ts: Date.now(),
        role: event.action === "received" ? "user" : "assistant",
        content,
      });
    }
    const state = await readState();

    if (event.action === "sent") {
      state.pendingValidateIds = parseUsedInstinctIdsFromAssistantText(content);
      await writeState(state);
      return;
    }

    if (event.action === "received") {
      const pending = Array.isArray(state.pendingValidateIds) ? state.pendingValidateIds : [];
      if (pending.length > 0) {
        const outcome = hasCorrectionSignal(content) ? "corrected" : "success";
        spawnSync(
          "python3",
          [validateScript, "--base-dir", skillDir, "--data-dir", dataDir],
          { input: JSON.stringify({ used_ids: pending, outcome }), encoding: "utf-8", timeout: 4000 },
        );
        state.pendingValidateIds = [];
      }

      state.inboundCount = safePositiveInt(state.inboundCount, 0) + 1;
      const everyN = safePositiveInt(hookCfg.extractEveryNMessages, 1);
      if (state.inboundCount % everyN === 0) {
        try {
          const text = await fs.readFile(sessionLogPath, "utf-8");
          const lines = text.trim().split("\n").filter(Boolean).slice(-30);
          const msgs = lines
            .map((l) => {
              try {
                return JSON.parse(l);
              } catch {
                return null;
              }
            })
            .filter(Boolean)
            .map((m) => ({ role: m.role, content: m.content, timestamp: new Date(m.ts).toISOString() }));
          spawnSync(
            "python3",
            [extractScript, "--base-dir", skillDir, "--data-dir", dataDir],
            {
              input: JSON.stringify({ sessionKey: String(event?.sessionKey ?? ""), messages: msgs }),
              encoding: "utf-8",
              timeout: 4000,
            },
          );
        } catch {
          // ignore
        }
      }

      await writeState(state);
      return;
    }
  }

  if (event?.type === "gateway" && event.action === "startup") {
    const state = await readState();
    const intervalHours = safePositiveInt(hookCfg.pruneIntervalHours, 24);
    const last = typeof state.lastPruneAtMs === "number" ? state.lastPruneAtMs : 0;
    if (Date.now() - last > intervalHours * 3600 * 1000) {
      spawnSync("python3", [pruneScript, "--base-dir", skillDir, "--data-dir", dataDir], { encoding: "utf-8", timeout: 8000 });
      state.lastPruneAtMs = Date.now();
      await writeState(state);
    }
  }
}

