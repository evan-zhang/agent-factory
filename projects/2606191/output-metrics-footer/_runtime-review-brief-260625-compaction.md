# Factory Review Brief: OpenClaw Compaction Scheme

Date: 2026-06-25
Project: 2606191 output-metrics-footer

## Goal

Review whether an engineer's proposed OpenClaw compaction configuration should be incorporated into our maintained context-management scheme.

## Our Current Intended Scheme

Relevant effective settings:

```json
{
  "contextTokens": 300000,
  "compaction": {
    "mode": "safeguard",
    "reserveTokensFloor": 60000,
    "reserveTokens": 760000,
    "keepRecentTokens": 60000,
    "maxHistoryShare": 0.65,
    "recentTurnsPreserve": 4,
    "maxActiveTranscriptBytes": "50mb",
    "midTurnPrecheck": { "enabled": true },
    "memoryFlush": {
      "enabled": true,
      "softThresholdTokens": 50000
    },
    "timeoutSeconds": 120,
    "model": "newapi-anthropic-vip/deepseek-latest-cloud"
  },
  "contextPruning": {
    "mode": "cache-ttl",
    "ttl": "8turns",
    "keepLastAssistants": 3,
    "softTrimRatio": 0.6,
    "hardClearRatio": 0.8,
    "minPrunableToolChars": 2000
  },
  "plugins.openclaw-output-metrics-footer.config": {
    "contextReserveTokens": 60000
  }
}
```

Design target: effective model prompt budget should be about 240K tokens:

- `contextTokens - reserveTokensFloor = 300K - 60K = 240K`
- Because model-level `contextWindow` is 1M, prior analysis set `reserveTokens = 760K` so `contextWindow - reserveTokens = 240K`

## Engineer Proposal To Review

Suggested config:

```json
{
  "contextTokens": 300000,
  "contextLimits": {
    "toolResultMaxChars": 32000
  },
  "compaction": {
    "reserveTokensFloor": 60000,
    "reserveTokens": 32768,
    "keepRecentTokens": 40000,
    "maxHistoryShare": 0.6,
    "midTurnPrecheck": {
      "enabled": true
    }
  }
}
```

Original config note:

```json
{
  "contextTokens": 256000,
  "compaction": {
    "reserveTokensFloor": 60000,
    "reserveTokens": 32768,
    "keepRecentTokens": 80000,
    "maxHistoryShare": 0.6,
    "memoryFlush": {
      "enabled": true,
      "softThresholdTokens": 120000
    }
  }
}
```

Engineer's mechanism claims:

- `reserveTokens` actual effective value is `max(reserveTokens, reserveTokensFloor)`.
- `memoryFlush.softThresholdTokens` participates in preflight trigger line:
  `preflight = contextTokens - reserveTokensFloor - softThresholdTokens`.
- With 256K context and 120K soft threshold: `256K - 60K - 120K = 76K`, causing frequent compression.
- Without midTurnPrecheck, tool loops can add large outputs without another pre-prompt check.
- With midTurnPrecheck, every tool return is checked before the next model call.

## Main Questions

1. Should we incorporate `contextLimits.toolResultMaxChars: 32000`?
2. Should we adjust `keepRecentTokens` from 60000 to 40000 or 50000?
3. Should we adjust `maxHistoryShare` from 0.65 to 0.6?
4. Should `memoryFlush.softThresholdTokens` remain 50000, be removed, or changed?
5. Is our `reserveTokens: 760000` correct for 1M model context, or should we follow engineer's `32768`?
6. What exact question should we ask the engineer if the runtime formulas differ?

## Requested Output

Return a concise review with:

- PASS / CONDITIONAL_PASS / FAIL on our current scheme
- Items to adopt now
- Items to reject or defer
- Questions to ask engineer
- Suggested final config delta, if any
