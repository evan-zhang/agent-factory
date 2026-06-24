import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

type Usage = {
  provider?: string;
  model?: string;
  input?: number;
  output?: number;
  total?: number;
  ts: number;
  sessionKey?: string;
  contextTokenBudget?: number;
};

type Quota = {
  percent?: number;
  weeklyPercent?: number;
  resetLabel?: string;
  ts: number;
};

type Config = {
  enabled?: boolean;
  enabledChannels?: string[];
  disabledConversations?: string[];
  disabledChannels?: string[];
  cacheMs?: number;
  quotaCacheMs?: number;
  contextReserveTokens?: number;
  appendSubagents?: boolean;
};

const recentBySession = new Map<string, Usage>();
const recentOutputs: Usage[] = [];
let quotaCache: Quota | null = null;
let quotaFetchInFlight: Promise<Quota | null> | null = null;

// Track whether footer has already been appended for the current AI turn, per-session.
// Reset on each llm_output (new turn boundary), set after first footer append.
// Includes a timeout fallback: if no llm_output fires (error/fallback),
// the flag auto-expires after FOOTER_TURN_TIMEOUT_MS so footer is not stuck forever.
const footerConsumedPerSession = new Map<string, number>(); // sessionKey → timestamp
const FOOTER_TURN_TIMEOUT_MS = 120000; // 2 min fallback

function isFooterConsumed(sessionKey?: string): boolean {
  if (!sessionKey) return false;
  const ts = footerConsumedPerSession.get(sessionKey);
  if (!ts) return false;
  if (Date.now() - ts > FOOTER_TURN_TIMEOUT_MS) {
    footerConsumedPerSession.delete(sessionKey);
    return false;
  }
  return true;
}

function markFooterConsumed(sessionKey?: string) {
  const key = sessionKey ?? "_default";
  footerConsumedPerSession.set(key, Date.now());
}

function resetFooterForSession(sessionKey?: string) {
  if (sessionKey) footerConsumedPerSession.delete(sessionKey);
  else footerConsumedPerSession.clear();
}

// MODEL_CONTEXT is a fallback table used only when runtime doesn't pass contextTokenBudget.
// Values aligned with the recommended 256k sweet-spot config (see docs/compaction-config.md).
// Runtime-provided contextTokenBudget always takes priority and is more accurate.
const MODEL_CONTEXT: Record<string, number> = {
  "openai-codex/gpt-5.5": 256000,
  "gpt-5.5": 256000,
  "openai-codex/gpt-5.4-mini": 256000,
  "gpt-5.4-mini": 256000,
  "ollama/kimi-k2.6:cloud": 250000,
  "kimi-k2.6:cloud": 250000,
  "ollama/qwen3.5:397b-cloud": 250000,
  "qwen3.5:397b-cloud": 250000,
  "evan-openai/glm-5.2": 256000,
  "vip-newapi/glm-5.2": 256000,
  "glm-5.2": 256000,
  "glm-5.2[1m]": 256000,
  "evan-openai/glm-5.2[1m]": 256000,
  "evan-openai/glm-4.7": 128000,
  "glm-4.7": 128000,
  "newapi-openai/MiniMax-M3": 256000,
  "MiniMax-M3": 256000,
  "vip-newapi/glm-latest-cloud": 256000,
  "newapi-openai/glm-latest-cloud": 256000,
  "glm-latest-cloud": 256000,
  "newapi-openai/deepseek-v4-flash": 256000,
  "deepseek-v4-flash": 256000,
  "newapi-openai/gemini-3.5-flash": 256000,
  "gemini-3.5-flash": 256000,
  "newapi-anthropic/claude-sonnet-4-6": 200000,
  "claude-sonnet-4-6": 200000,
  "newapi-anthropic/claude-opus-4-8": 200000,
  "claude-opus-4-8": 200000,
  "newapi-anthropic/claude-haiku-4-5": 200000,
  "claude-haiku-4-5": 200000,
};

// Cache for primary model config (per agent)
let primaryCache: { value: string; ts: number } | null = null;
const PRIMARY_CACHE_MS = 30000;

function readPrimaryModel(): string {
  if (primaryCache && Date.now() - primaryCache.ts < PRIMARY_CACHE_MS) {
    return primaryCache.value;
  }
  try {
    const configPath = path.join(os.homedir(), ".openclaw", "gateways", "life", "openclaw.json");
    const raw = JSON.parse(fs.readFileSync(configPath, "utf8"));
    // Use global defaults.primary — applies to all agents unless overridden
    const primary = raw?.agents?.defaults?.model?.primary ?? "";
    primaryCache = { value: primary, ts: Date.now() };
    return primary;
  } catch {
    return primaryCache?.value ?? "";
  }
}

function n(v: unknown): number | undefined {
  return typeof v === "number" && Number.isFinite(v) ? v : undefined;
}

function fmt(v?: number): string {
  if (!Number.isFinite(v)) return "n/a";
  const x = Number(v);
  if (x >= 1_000_000) return `${Math.round(x / 100_000) / 10}m`;
  if (x >= 10_000) return `${Math.round(x / 1000)}k`;
  if (x >= 1000) return `${Math.round(x / 100) / 10}k`;
  return String(Math.round(x));
}

function colorForUsage(percent?: number): string {
  if (!Number.isFinite(percent)) return "⚪";
  if (Number(percent) >= 70) return "🔴"; // aligned with preflight trigger (~73%)
  if (Number(percent) >= 50) return "🟡";
  return "🟢";
}

function colorForRemaining(percent?: number): string {
  if (!Number.isFinite(percent)) return "⚪";
  if (Number(percent) < 20) return "🔴";
  if (Number(percent) <= 50) return "🟡";
  return "🟢";
}

function worst(...colors: string[]): string {
  if (colors.includes("🔴")) return "🔴";
  if (colors.includes("🟡")) return "🟡";
  if (colors.includes("🟢")) return "🟢";
  return "⚪";
}

function modelLabel(provider?: string, model?: string): string {
  const m = model || "model";
  if (!provider || m.includes("/")) return m;
  return `${provider}/${m}`;
}

function contextWindow(model?: string, provider?: string): number | undefined {
  const label = modelLabel(provider, model);
  return MODEL_CONTEXT[label] ?? MODEL_CONTEXT[model || ""] ?? undefined;
}

function latestUsage(sessionKey?: string): Usage | undefined {
  // P0 fix: strict session isolation. Only return usage for the requesting session.
  // If no sessionKey or no data for this session, return undefined (show nothing, not wrong data).
  if (!sessionKey) return undefined;
  return recentBySession.get(sessionKey);
}

function aggregateSubagents(root?: Usage, cacheMs = 120000): { input: number; output: number } | null {
  if (!root) return null;
  const cutoff = Date.now() - cacheMs;
  let input = 0;
  let output = 0;
  for (const u of recentOutputs) {
    if (u === root || u.ts < cutoff) continue;
    if (Math.abs(root.ts - u.ts) > cacheMs) continue;
    if (u.sessionKey && root.sessionKey && u.sessionKey === root.sessionKey) continue;
    input += u.input ?? 0;
    output += u.output ?? 0;
  }
  return input || output ? { input, output } : null;
}

function authProfilesPath(): string {
  return path.join(os.homedir(), ".openclaw", "agents", "main", "agent", "auth-profiles.json");
}

function findCodexAccessToken(): string | null {
  try {
    const raw = JSON.parse(fs.readFileSync(authProfilesPath(), "utf8"));
    for (const profile of Object.values(raw.profiles ?? {}) as any[]) {
      if (profile?.provider !== "openai-codex" || profile?.type !== "oauth") continue;
      if (typeof profile.access === "string") return profile.access;
      if (typeof profile.access?.accessToken === "string") return profile.access.accessToken;
    }
  } catch {
    return null;
  }
  return null;
}

function resetLabelFromNow(resetAt?: unknown): string | undefined {
  if (typeof resetAt !== "number") return undefined;
  const ms = resetAt > 10_000_000_000 ? resetAt - Date.now() : resetAt * 1000 - Date.now();
  if (!Number.isFinite(ms) || ms <= 0) return undefined;
  const h = Math.max(1, Math.round(ms / 3600000));
  return `${h}h`;
}

function parseQuota(data: any): Quota {
  const candidates = [
    data?.rate_limit?.primary_window,
    data?.codex,
    data?.plus,
    data?.pro,
    data?.usage,
    data
  ];
  let percent: number | undefined;
  let weeklyPercent: number | undefined;
  let resetLabel: string | undefined;
  for (const c of candidates) {
    if (!c || typeof c !== "object") continue;
    percent ??= n(c.remaining_percent) ?? n(c.remainingPercent) ?? n(c.percent_remaining) ?? n(c.percentRemaining);
    const usedPercent = n(c.used_percent) ?? n(c.usedPercent);
    if (percent == null && usedPercent != null) percent = Math.max(0, Math.min(100, 100 - usedPercent));
    weeklyPercent ??= n(c.weekly_remaining_percent) ?? n(c.weeklyRemainingPercent);
    const secondaryUsedPercent = n(data?.rate_limit?.secondary_window?.used_percent) ?? n(data?.rate_limit?.secondary_window?.usedPercent);
    if (weeklyPercent == null && secondaryUsedPercent != null) weeklyPercent = Math.max(0, Math.min(100, 100 - secondaryUsedPercent));
    resetLabel ??= resetLabelFromNow(c.reset_at ?? c.resetAt);
    if (percent == null && Number.isFinite(c.requests_used) && Number.isFinite(c.requests_limit)) {
      percent = Math.round(((c.requests_limit - c.requests_used) / c.requests_limit) * 100);
    }
  }
  return { percent, weeklyPercent, resetLabel: resetLabel ?? "5h", ts: Date.now() };
}

async function fetchCodexQuota(cacheMs: number): Promise<Quota | null> {
  if (quotaCache && Date.now() - quotaCache.ts < cacheMs) return quotaCache;
  if (quotaFetchInFlight) return quotaFetchInFlight;
  quotaFetchInFlight = (async () => {
    const token = findCodexAccessToken();
    if (!token) return quotaCache;
    try {
      const res = await fetch("https://chatgpt.com/backend-api/wham/usage", {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/json"
        },
        signal: AbortSignal.timeout(4000)
      });
      if (!res.ok) return quotaCache;
      quotaCache = parseQuota(await res.json());
      return quotaCache;
    } catch {
      return quotaCache;
    } finally {
      quotaFetchInFlight = null;
    }
  })();
  return quotaFetchInFlight;
}

function appendFooter(content: string, footer: string): string {
  const line = `\n\n_${footer}_`;
  if (content.includes("↑") && content.includes("%ctx")) return content;
  if (content.length + line.length > 3800) return content;
  return `${content}${line}`;
}

function buildFooterParts(usage: Usage | undefined, opts: { quota: Quota | null; appendSubagents: boolean; cacheMs: number; reserve: number }): string[] | null {
  if (!usage) return null;
  const label = modelLabel(usage.provider, usage.model);
  // Priority: runtime contextTokenBudget (accurate) > MODEL_CONTEXT table (fallback)
  const tableWin = contextWindow(usage.model, usage.provider);
  const win = (usage.contextTokenBudget && usage.contextTokenBudget > 0) ? usage.contextTokenBudget : tableWin;
  const total = (usage.input ?? 0) + (usage.output ?? 0);
  const effectiveTotal = Math.max(0, total + opts.reserve);
  const ctxPct = win ? Math.round((effectiveTotal / win) * 100) : undefined;
  const status = worst(colorForUsage(ctxPct), colorForRemaining(opts.quota?.percent));
  const parts = [
    `${status} ↑${fmt(usage.input)} ↓${fmt(usage.output)}`,
    `${Number.isFinite(ctxPct) ? ctxPct : "n/a"}%ctx`
  ];
  if (opts.quota?.percent != null) parts.push(`${opts.quota.resetLabel ?? "5h"} ${opts.quota.percent}%`);
  parts.push(label);

  // Fallback detection: compare actual model vs configured global primary
  const primary = readPrimaryModel().toLowerCase();
  if (primary && label.toLowerCase() !== primary) {
    const reason = Number.isFinite(ctxPct) && ctxPct >= 100 ? 'context overflow' : 'provider error/timeout';
    parts.unshift(`⚠️ 降级：${primary} → ${label}（${reason}）`);
  }

  if (opts.appendSubagents) {
    const sub = aggregateSubagents(usage, opts.cacheMs);
    if (sub) parts.push(`sub ↑${fmt(sub.input)} ↓${fmt(sub.output)}`);
  }

  return parts;
}

export default definePluginEntry({
  id: "openclaw-output-metrics-footer",
  name: "OpenClaw Output Metrics Footer",
  description: "Append compact context/token/quota metrics to OpenClaw channel outputs.",
  register(api) {
    const cfg = (api.pluginConfig ?? {}) as Config;
    if (cfg.enabled === false) return;
    const cacheMs = cfg.cacheMs ?? 120000;
    const quotaCacheMs = cfg.quotaCacheMs ?? 60000;
    const reserve = cfg.contextReserveTokens ?? 40000;

    api.on("llm_output", async (event: any, ctx: any) => {
      // lastAssistant.usage is the single last API call's usage (not accumulated).
      // event.usage (getUsageTotals) accumulates input across all model calls in a turn,
      // which inflates the context percentage when there are multiple tool calls.
      // We prefer lastCallUsage for accurate context-occupancy calculation.
      const lastCallUsage = event.lastAssistant?.usage;
      const singleInput = lastCallUsage
        ? n(lastCallUsage.input ?? lastCallUsage.input_tokens ?? lastCallUsage.prompt_tokens ?? lastCallUsage.promptTokens)
        : undefined;
      const singleOutput = lastCallUsage
        ? n(lastCallUsage.output ?? lastCallUsage.output_tokens ?? lastCallUsage.completion_tokens ?? lastCallUsage.completionTokens)
        : undefined;

      const usage: Usage = {
        provider: event.provider ?? ctx.modelProviderId,
        model: event.model ?? ctx.modelId,
        // Prefer single-call input for accurate %ctx; fall back to accumulated only if no lastAssistant
        input: singleInput ?? n(event.usage?.input),
        output: singleOutput ?? n(event.usage?.output),
        total: n(event.usage?.total),
        ts: Date.now(),
        sessionKey: ctx.sessionKey,
        contextTokenBudget: n(event.contextTokenBudget ?? ctx.contextTokenBudget)
      };
      recentOutputs.push(usage);
      if (usage.sessionKey) recentBySession.set(usage.sessionKey, usage);
      while (recentOutputs.length > 80) recentOutputs.shift();
      // New LLM output → reset footer flag for this session so next message_sending can append.
      resetFooterForSession(ctx.sessionKey);
    }, { name: "openclaw-output-metrics-footer-llm-output" });

    api.on("message_sending", async (event: any, ctx: any) => {
      const channel = String(ctx.channelId ?? event.metadata?.channel ?? "");
      if ((cfg.enabledChannels ?? []).length > 0 && !(cfg.enabledChannels ?? []).includes(channel)) return;
      if ((cfg.disabledChannels ?? []).includes(ctx.channelId)) return;
      if ((cfg.disabledConversations ?? []).includes(ctx.conversationId)) return;
      if (!event.content || typeof event.content !== "string") return;
      // Only append footer once per AI turn (first chunk wins), per-session.
      if (isFooterConsumed(ctx.sessionKey)) return;

      const usage = latestUsage(ctx.sessionKey);
      const quota = await fetchCodexQuota(quotaCacheMs);
      const parts = buildFooterParts(usage, { quota, appendSubagents: cfg.appendSubagents !== false, cacheMs, reserve });
      if (!parts) return;
      markFooterConsumed(ctx.sessionKey);
      return { content: appendFooter(event.content, parts.join(" · ")) };
    }, { name: "openclaw-output-metrics-footer-message-sending" });

    // Also hook before_dispatch for sessions that bypass message_sending (e.g. a2a-forward)
    api.on("before_dispatch", async (event: any, ctx: any) => {
      if (!event.content || typeof event.content !== "string") return;
      // Skip if already has footer
      if (event.content.includes("↑") && event.content.includes("%ctx")) return;
      // Only append footer once per AI turn (first chunk wins), per-session.
      if (isFooterConsumed(ctx.sessionKey)) return;

      const usage = latestUsage(ctx.sessionKey);
      if (!usage) return;
      const quota = await fetchCodexQuota(quotaCacheMs);
      const parts = buildFooterParts(usage, { quota, appendSubagents: cfg.appendSubagents !== false, cacheMs, reserve });
      if (!parts) return;
      markFooterConsumed(ctx.sessionKey);
      return { content: appendFooter(event.content, parts.join(" · ")) };
    }, { name: "openclaw-output-metrics-footer-before-dispatch" });
  }
});
