# File2Voice Skill 质量门控审查报告

> **审查日期**：2026-05-15
> **审查范围**：projects/2605151/file2voice/
> **审查员**：Validator Sub-Agent

---

## 1. SKILL.md 规范检查

| 检查项 | 结果 | 说明 |
|--------|------|------|
| frontmatter 完整（name/description/version/homepage/issues） | **PASS** | 6 个字段齐全 |
| 包含「配置与授权」节 | **PASS** | 含必填项、可选项、依赖说明、无需配置说明 |
| 包含「问题反馈」节 | **PASS** | 含 Issue 地址、标题格式、建议包含信息 |
| 触发判断逻辑清晰 | **PASS** | 树状判断结构，触发词明确 |
| 核心流程描述完整 | **PASS** | 5 步流程完整，每步有详细说明 |

**备注**：
- SKILL.md Step 4 默认参数中 `model` 写的是 `speech-02-turbo`，但同一节标题写的是「MiniMax Speech 2.8 API」，config.json 中 `api.model` 为 `speech-2.8-hd`。**存在矛盾**（见第 5 项详细说明）。
- Step 4 中 `响应: JSON 格式，音频在 data.audio 字段，hex 编码` 重复了两遍（复制粘贴遗留）。

---

## 2. 目录结构检查

| 检查项 | 结果 | 说明 |
|--------|------|------|
| SKILL.md 存在 | **PASS** | — |
| version.json 存在 | **PASS** | — |
| config.json 存在 | **PASS** | — |
| scripts/ 下脚本完整 | **PASS** | file2voice.sh、tts.sh、extract_text.sh、rewrite.py 齐全 |
| prompts/ 下有改写 prompt 模板 | **PASS** | prompts/rewrite-prompt.md 内容详尽 |
| references/ 下有 API 参考文档 | **PASS** | references/minimax-tts-api.md |

**备注**：
- scripts/ 下存在 `__pycache__/rewrite.cpython-314.pyc` 缓存文件，发布时应清理。

---

## 3. 版本号一致性检查

| 位置 | 版本号 | 结果 |
|------|--------|------|
| SKILL.md frontmatter version | `1.1.0` | — |
| version.json version | `1.1.0` | — |
| config.json（无 version 字段） | N/A | config.json 无 version 字段 |
| projects/2605151/VERSION | `1.1.0` | — |
| state.json version | `1.0.0` | ❌ 不一致 |

**结论：FAIL**

- state.json 中 version 为 `1.0.0`，与其余三处的 `1.1.0` 不一致。
- config.json 没有独立的 version 字段（TOOLS.md 规范要求 config.json 也有版本号），但 config.json 中确实没有。
- 需修正：state.json version → `1.1.0`；config.json 应补充 version 字段。

---

## 4. 代码质量检查

### extract_text.sh
| 检查项 | 结果 | 说明 |
|--------|------|------|
| set -euo pipefail | **PASS** | 第 3 行 |
| 错误处理完善 | **PASS** | 不支持类型有明确错误提示，输出为空有警告 |
| 临时文件使用 mktemp 并清理 | **WARN** | 本脚本不创建临时文件（由主脚本管理），无问题 |

### file2voice.sh
| 检查项 | 结果 | 说明 |
|--------|------|------|
| set -euo pipefail | **PASS** | 第 3 行 |
| 错误处理完善 | **PASS** | 输入验证、ffmpeg 检查、API Key 检查都有 |
| 临时文件使用 mktemp 并清理 | **PASS** | `mktemp -d /tmp/file2voice.XXXXXX` + `trap 'rm -rf "$TMPDIR"' EXIT` |
| config.json 加载安全性 | **WARN** | 用 `eval` 加载 python 输出，如果 config.json 被恶意修改可注入 shell 命令。风险较低（本地文件），但建议改用更安全的解析方式 |

### tts.sh
| 检查项 | 结果 | 说明 |
|--------|------|------|
| set -euo pipefail | **PASS** | 第 3 行 |
| 错误处理完善 | **PASS** | 参数验证、API Key 检查、分段失败统计 |
| 临时文件使用 mktemp 并清理 | **PASS** | `mktemp -d /tmp/file2voice_tts.XXXXXX` + trap |
| mmx-cli 降级逻辑 | **WARN** | mmx-cli 降级到 API 时调用了 `_tts_api` 函数，但该函数定义在文件末尾（bash 函数定义位置不影响执行，因为 bash 先解析整个文件，所以实际上没问题） |

**代码质量总体：PASS**（有 2 个 WARN 但不阻塞）

---

## 5. API 集成检查

| 检查项 | 结果 | 说明 |
|--------|------|------|
| TTS 使用正确模型 | **FAIL** | 存在矛盾（详见下方） |
| mmx-cli 优先 + API 降级双通道 | **PASS** | tts.sh 实现了完整的双通道逻辑 |
| 音色 ID 格式正确 | **PASS** | 使用 `Chinese (Mandarin)_XXX` 格式，与官方一致 |
| API Key 从环境变量读取 | **PASS** | `${MINIMAX_API_KEY:-}` |

### 模型矛盾详细说明

**SKILL.md 默认参数**中写：
> `model`: speech-02-turbo

**SKILL.md Step 4 标题**写：
> 调用 MiniMax Speech 2.8 API

**config.json api.model** 为：
> `speech-2.8-hd`

**tts.sh `_tts_api` 函数**中实际调用：
> `"model": "speech-2.8-hd"`

**references/minimax-tts-api.md 请求体示例**为：
> `"model": "speech-02-turbo"`

**结论**：SKILL.md 默认参数节和 references 示例用的 `speech-02-turbo`，但实际代码和 config.json 用的 `speech-2.8-hd`。**以代码为准，SKILL.md 默认参数和 references 示例需要统一为 `speech-2.8-hd`。**

---

## 6. 工厂规范一致性检查

| 检查项 | 结果 | 说明 |
|--------|------|------|
| config.json 包含 voices | **PASS** | 10 种中文音色 |
| config.json 包含 styles | **PASS** | 5 种风格及音色映射 |
| config.json 包含 supported_formats | **PASS** | 8 种格式 |
| 依赖说明完整 | **PASS** | SKILL.md 配置与授权节 + config.json requires 字段 |

---

## 总结论

### 统计
- **PASS**：18 项
- **FAIL**：2 项
- **WARN**：3 项

### FAIL 项（必须修复）

1. **版本号不一致**：state.json version = `1.0.0`，应为 `1.1.0`
2. **模型名称矛盾**：SKILL.md 默认参数和 references 示例中 model 为 `speech-02-turbo`，应统一为 `speech-2.8-hd`（与代码和 config.json 一致）

### WARN 项（建议修复）

1. **__pycache__**：发布前应清理 scripts/__pycache__/
2. **eval 安全性**：file2voice.sh 中用 eval 加载 config.json 解析结果，建议改用更安全方式
3. **SKILL.md 重复行**：Step 4 中 `响应: JSON 格式，音频在 data.audio 字段，hex 编码` 重复了两遍
4. **config.json 缺 version 字段**：TOOLS.md 规范要求 config.json 也有版本号

### 判定：❌ FAIL

存在 2 个 FAIL 项，需要修复后重新验证。
