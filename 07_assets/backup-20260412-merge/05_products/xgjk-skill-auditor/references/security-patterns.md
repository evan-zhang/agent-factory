# 安全扫描 Pattern 表

## 快速扫描命令

对目标 Skill 目录执行，发现任意 CRITICAL 命中 → D4 强制 REVISE：

```bash
SKILL_DIR="/path/to/skill"

# C1: 硬编码 Token/Key（排除注释行）
grep -rn --include="*.ts" --include="*.js" --include="*.py" \
  -E "(api[_-]?key|token|secret|password)\s*=\s*['\"][a-zA-Z0-9_\-]{16,}" \
  "$SKILL_DIR" | grep -v "^\s*//"

# C2: 直接写 process.env
grep -rn "process\.env\." "$SKILL_DIR" | grep -v "process\.env\." | \
  grep -v "// " | head -10

# C3: eval/exec 动态执行
grep -rn -E "\beval\(|\bexec\(" "$SKILL_DIR" --include="*.ts" --include="*.js"

# C4: 未声明的外部 URL（检查是否在 setup.md 里有对应 External Endpoints）
grep -rn -E "https?://[a-zA-Z0-9.-]+\.[a-z]{2,}" "$SKILL_DIR" \
  --include="*.ts" --include="*.js" --include="*.md" | \
  grep -v "setup\.md" | grep -v "example\.com"

# C5: 敏感词扫描
grep -rn -iE "\b(silently|secretly|automatically monitor|track user|exfiltrate)\b" \
  "$SKILL_DIR" --include="*.md"
```

## 严重问题扫描

```bash
# S1: 检查 metadata.requires.env 是否声明
grep -A5 "requires:" "$SKILL_DIR/SKILL.md" | grep -i "env"

# S2: setup.md 是否存在（有 API 调用的 Skill 必须有）
ls "$SKILL_DIR/setup.md" 2>/dev/null || echo "MISSING setup.md"

# S3: appKey 字段名检查（建议改为 apiKey）
grep -rn "appKey" "$SKILL_DIR" --include="*.ts" --include="*.md"
```

## 轻微问题扫描

```bash
# M1: LLM 凭证是否由调用方注入（检查是否有内部存储）
grep -rn "llmClient\|openaiKey\|claudeKey" "$SKILL_DIR" --include="*.ts"

# M2: ClawHub suspicious 状态查询
curl -s "https://clawhub.com/api/v1/skills/{slug}" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); \
  m=d.get('moderation',{}); \
  print('suspicious:', m.get('isSuspicious')); \
  print('codes:', m.get('reasonCodes'))"
```

## 工厂已知误报白名单

| 误报代码 | 原因 | 处理方式 |
|---------|------|---------|
| `env_credential_access` | API Key 必须随请求头发送，结构性触发 | 记录为已知误报，不扣 D4 分，确认 confidence 为 medium 而非 high |
| `suspicious.llm_suspicious` | systemPrompt 含 JSON 输出指令 | 若已将 "直接返回JSON" 改为 "输出格式：JSON对象" 则视为已修复 |

## 判定流程

```
1. 运行 C1-C5 CRITICAL 扫描
   → 任意命中 → D4 = 1，强制 REVISE，停止后续维度评分

2. 运行 S1-S3 严重问题扫描
   → 每项命中 -2

3. 运行 M1-M2 轻微问题扫描
   → 每项命中 -1

4. 对照白名单，已知误报不扣分，但在报告中注明
```
