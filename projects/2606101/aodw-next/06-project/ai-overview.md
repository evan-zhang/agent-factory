# AI System Overview  
（本文件列出 AI 理解本系统所需的全局信息）

> ⚠️ **项目特化文件**：本文件描述当前项目的技术栈与架构，是 AODW skill 的项目层配置。
> 在新项目中安装 AODW 时，必须完整重写本文件。
>
> 说明：本文件是骨架模板，AI 可以在后续 RT 中逐步补全。  
> 修改架构或模块职责时，AI 必须同步更新本文件。

---

## 1. 技术栈

<!-- AUTO-DETECTED: 以下内容由 AI 自动检测 -->
- **前端**：HTML/CSS/JavaScript（原生，无框架），Tauri API 1.5.0
- **后端**：Rust (Edition 2021) + Tauri 1.5
- **数据库**：无（本地配置文件存储）
- **消息系统**：无
- **缓存**：内存缓存（TTS 缓存、配置缓存）
- **运维 / 部署**：Tauri 构建系统，支持 macOS (Apple Silicon/Intel) 和 Windows
- **其他**：
  - 语音识别（STT）：火山引擎豆包、阿里云、腾讯云
  - 语音合成（TTS）：火山引擎豆包、阿里云、腾讯云
  - AI 能力：LLM（火山引擎豆包、内部LLM）、Agent系统（仅Pro版）
  - 音频处理：cpal 0.15
  - 热键管理：global-hotkey 0.4
  - 剪贴板/输入模拟：clipboard 0.5, enigo 0.1.2
<!-- END AUTO-DETECTED -->

---

## 2. 整体架构概览

<!-- AUTO-DETECTED: 以下内容由 AI 自动检测 -->
VoiceX 是一个基于 Tauri 的桌面应用，采用 Mono-repo 架构，支持两个产品版本：

```text
┌─────────────────────────────────────────────────────────────┐
│                    VoiceX Mono-repo                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  VoiceX (基础版) │         │  VoiceX Pro      │          │
│  │                  │         │                  │          │
│  │  - 语音输入法    │         │  - 语音输入法    │          │
│  │  - STT + 自动粘贴│         │  - STT + 自动粘贴│          │
│  │                  │         │  - AI 助手模式   │          │
│  │                  │         │  - Agent 系统    │          │
│  │                  │         │  - 训练系统      │          │
│  └──────────────────┘         └──────────────────┘          │
│           │                              │                    │
│           └──────────┬───────────────────┘                   │
│                      │                                       │
│           ┌──────────▼──────────┐                            │
│           │  共享 Crates        │                            │
│           │  - voicex-utils     │                            │
│           │  - voicex-config   │                            │
│           └────────────────────┘                            │
│                      │                                       │
│           ┌──────────▼──────────┐                            │
│           │  Tauri Runtime      │                            │
│           │  - 系统托盘         │                            │
│           │  - 全局热键         │                            │
│           │  - 窗口管理        │                            │
│           └────────────────────┘                            │
│                      │                                       │
│           ┌──────────▼──────────┐                            │
│           │  外部服务 API        │                            │
│           │  - 火山引擎豆包 STT │                            │
│           │  - 火山引擎豆包 TTS │                            │
│           │  - 火山引擎豆包 LLM │                            │
│           │  - 阿里云 STT/TTS   │                            │
│           │  - 腾讯云 STT/TTS   │                            │
│           └────────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

**架构特点**：
- **多供应商抽象**：STT、TTS、LLM 均支持多供应商切换，通过 Trait 抽象实现
- **共享代码库**：两个应用共享 `voicex-utils` 和 `voicex-config` crates
- **本地优先**：无数据库依赖，配置和状态存储在本地文件系统
- **单实例运行**：通过锁文件机制确保只有一个实例运行
<!-- END AUTO-DETECTED -->

---

## 3. 目录结构（只列关键部分）

<!-- AUTO-DETECTED: 以下内容由 AI 自动检测 -->
- `/apps/voicex/` - VoiceX 基础版应用
  - `src/` - 前端 HTML/CSS/JavaScript 文件
  - `src-tauri/` - Rust 后端代码（Tauri）
- `/apps/voicex-pro/` - VoiceX Pro 应用（包含 AI 助手和 Agent 系统）
  - `src/` - 前端 HTML/CSS/JavaScript 文件
  - `src-tauri/` - Rust 后端代码（Tauri）
- `/crates/voicex-utils/` - 共享工具库（错误类型、通用工具）
- `/crates/voicex-config/` - 配置管理库（配置结构定义和管理）
- `/RT/` - AODW Request Ticket 知识库（每个 RT 的文档和代码）
- `/.aodw-next/` - AODW-Next 配置与规则文件
- `/scripts/` - 构建和部署脚本
- `/website/` - 项目官网（静态站点）
<!-- END AUTO-DETECTED -->

---

## 4. 核心业务模块

<!-- AUTO-DETECTED: 以下内容由 AI 自动检测 -->

### 4.1 音频管理模块（Audio Module）

- **职责**：音频录制、播放、音频流处理
- **关键路径**：
  - `apps/*/src-tauri/src/services/audio_manager.rs` - 音频管理器
  - `apps/*/src-tauri/src/services/audio_recorder.rs` - 音频录制器
  - `apps/*/src-tauri/src/services/audio_worker.rs` - 音频工作线程
  - `apps/*/src-tauri/src/utils/audio_utils.rs` - 音频工具函数
- **依赖关系**：
  - 被调用：STT 模块、TTS 模块、热键模块
  - 依赖：cpal（跨平台音频库）
- **关键约束**：
  - 音频录制必须通过 AudioRecorder trait 实现
  - 音频播放必须通过 AudioManager 统一管理
  - 不得直接操作底层音频设备

### 4.2 语音识别模块（STT Module）

- **职责**：语音转文字，支持多供应商切换
- **关键路径**：
  - `apps/*/src-tauri/src/services/stt/mod.rs` - STT 模块入口
  - `apps/*/src-tauri/src/services/stt/doubao.rs` - 火山引擎豆包 STT
  - `apps/*/src-tauri/src/services/stt/aliyun.rs` - 阿里云 STT
  - `apps/*/src-tauri/src/services/stt/tencent.rs` - 腾讯云 STT
- **依赖关系**：
  - 被调用：命令层（commands/stt.rs）
  - 依赖：音频管理模块、HTTP 客户端（reqwest）
- **关键约束**：
  - 必须实现 SttProvider trait
  - 必须支持异步调用
  - 不得在 STT 调用中阻塞主线程

### 4.3 语音合成模块（TTS Module）

- **职责**：文字转语音，支持多供应商切换
- **关键路径**：
  - `apps/*/src-tauri/src/services/tts/mod.rs` - TTS 模块入口
  - `apps/*/src-tauri/src/services/tts/doubao.rs` - 火山引擎豆包 TTS
  - `apps/*/src-tauri/src/services/tts/aliyun.rs` - 阿里云 TTS
  - `apps/*/src-tauri/src/services/tts/tencent.rs` - 腾讯云 TTS
  - `apps/voicex-pro/src-tauri/src/services/tts_cache.rs` - TTS 缓存（仅Pro版）
- **依赖关系**：
  - 被调用：Agent 模块、训练模块（仅Pro版）
  - 依赖：HTTP 客户端（reqwest）、音频管理模块
- **关键约束**：
  - 必须实现 TtsProvider trait
  - 必须支持流式音频返回
  - Pro 版必须使用 TTS 缓存避免重复请求

### 4.4 热键管理模块（Hotkey Module）

- **职责**：全局热键注册、监听、事件处理
- **关键路径**：
  - `apps/*/src-tauri/src/services/hotkey_v2/listener.rs` - 热键监听器
  - `apps/*/src-tauri/src/commands/hotkey.rs` - 热键命令
- **依赖关系**：
  - 被调用：主程序入口（main.rs）
  - 依赖：global-hotkey 库
- **关键约束**：
  - 热键注册必须在应用启动时完成
  - 热键事件必须异步处理，不得阻塞
  - 必须支持热键配置的动态更新

### 4.5 自动粘贴模块（Auto Paste Module）

- **职责**：将识别结果自动输入到当前光标位置
- **关键路径**：
  - `apps/*/src-tauri/src/services/auto_paste.rs` - 自动粘贴服务
  - `apps/*/src-tauri/src/commands/paste.rs` - 粘贴命令
- **依赖关系**：
  - 被调用：STT 模块（基础版）
  - 依赖：enigo（输入模拟库）
- **关键约束**：
  - 必须检查辅助功能权限（macOS）
  - 不得在无权限时静默失败，必须提示用户
  - 粘贴操作必须异步执行

### 4.6 配置管理模块（Config Module）

- **职责**：应用配置的读取、保存、验证
- **关键路径**：
  - `crates/voicex-config/` - 配置管理库
  - `apps/*/src-tauri/src/services/config_manager.rs` - 配置管理器
  - `apps/voicex-pro/src-tauri/src/services/cached_config.rs` - 缓存配置（仅Pro版）
- **依赖关系**：
  - 被调用：所有需要配置的模块
  - 依赖：serde（序列化）、文件系统
- **关键约束**：
  - 配置必须通过 ConfigManager 统一管理
  - 配置变更必须持久化到文件
  - 不得在配置文件中硬编码敏感信息

### 4.7 Agent 系统模块（Agent Module，仅 Pro 版）

- **职责**：AI Agent 运行时、工具调用、记忆管理、场景加载
- **关键路径**：
  - `apps/voicex-pro/src-tauri/src/services/agent/runtime.rs` - Agent 运行时
  - `apps/voicex-pro/src-tauri/src/services/agent/tools/` - Agent 工具（如 Tavily 搜索）
  - `apps/voicex-pro/src-tauri/src/services/agent/memory.rs` - 记忆管理
  - `apps/voicex-pro/src-tauri/src/services/agent/scene_loader.rs` - 场景加载器
  - `apps/voicex-pro/src-tauri/src/services/agent/knowledge.rs` - 知识库管理
- **依赖关系**：
  - 被调用：训练模块、智能助手模式
  - 依赖：LLM 模块、TTS 模块、STT 模块
- **关键约束**：
  - Agent 必须通过 AgentRuntime 统一管理
  - 工具调用必须通过 Tool trait 实现
  - 记忆管理必须支持持久化

### 4.8 LLM 模块（LLM Module，仅 Pro 版）

- **职责**：大语言模型调用、流式响应处理
- **关键路径**：
  - `apps/voicex-pro/src-tauri/src/services/llm.rs` - LLM 服务
  - `apps/voicex-pro/src-tauri/src/services/ark_llm.rs` - 火山引擎豆包 LLM
  - `apps/voicex-pro/src-tauri/src/services/internal_llm.rs` - 内部 LLM
- **依赖关系**：
  - 被调用：Agent 模块、训练模块
  - 依赖：HTTP 客户端（reqwest）
- **关键约束**：
  - 必须支持流式响应
  - 必须实现 LlmProvider trait
  - 不得在 LLM 调用中阻塞主线程

### 4.9 训练系统模块（Training Module，仅 Pro 版）

- **职责**：医药代表陪练系统、场景管理、教练评分
- **关键路径**：
  - `apps/voicex-pro/src-tauri/src/commands/training.rs` - 训练命令
  - `apps/voicex-pro/src-tauri/src/services/agent/best_practice.rs` - 最佳实践
  - `apps/voicex-pro/src-tauri/src/services/agent/drug_search.rs` - 药品搜索
- **依赖关系**：
  - 被调用：前端训练界面
  - 依赖：Agent 模块、LLM 模块、TTS 模块、STT 模块
- **关键约束**：
  - 场景配置必须通过 YAML 文件管理
  - 训练记录必须持久化
  - 合规检测必须在对话过程中实时进行

<!-- END AUTO-DETECTED -->

---

## 5. 系统级 Invariants（不可破坏原则）

<!-- AUTO-DETECTED: 以下内容由 AI 自动检测 -->
AI 在修改任何代码前必须确认不会违反以下约束：

- **多供应商抽象原则**：不得破坏 STT/TTS/LLM 的 Trait 抽象，新增供应商必须实现对应 Trait
- **异步非阻塞原则**：不得在 STT/TTS/LLM 调用中阻塞主线程，所有网络请求必须异步
- **配置统一管理原则**：不得绕过 ConfigManager 直接读写配置文件
- **权限检查原则**：不得在无权限时静默失败，必须明确提示用户（如辅助功能权限、麦克风权限）
- **单实例运行原则**：不得破坏单实例锁机制，确保只有一个应用实例运行
- **音频资源管理原则**：不得泄漏音频资源，录制/播放完成后必须正确释放
- **热键事件处理原则**：热键事件必须异步处理，不得阻塞事件循环
- **API 兼容性原则**：不得无故更改 Tauri 命令的返回格式（除非走 Spec-Full 流程）
- **性能约束原则**：不得在热路径（如热键响应、音频处理）引入明显的性能退化
- **安全约束原则**：不得引入明显的安全风险（如明文存储 API Key、绕过权限检查）

根据系统演进，这些 Invariants 可以在 RT 中进行讨论与更新。
<!-- END AUTO-DETECTED -->

---

## 6. 模块 README 映射表

为 AI 提供“代码目录 → 模块文档”的索引示例：

<!-- AUTO-DETECTED: 以下内容由 AI 自动检测 -->
为 AI 提供"代码目录 → 模块文档"的索引：

```text
apps/*/src-tauri/src/services/audio_*.rs      → docs/modules/audio.md
apps/*/src-tauri/src/services/stt/**         → docs/modules/stt.md
apps/*/src-tauri/src/services/tts/**          → docs/modules/tts.md
apps/*/src-tauri/src/services/hotkey_v2/**    → docs/modules/hotkey.md
apps/*/src-tauri/src/services/auto_paste.rs   → docs/modules/auto-paste.md
apps/*/src-tauri/src/services/config_manager.rs → docs/modules/config.md
apps/voicex-pro/src-tauri/src/services/agent/** → docs/modules/agent.md
apps/voicex-pro/src-tauri/src/services/llm.rs → docs/modules/llm.md
apps/voicex-pro/src-tauri/src/commands/training.rs → docs/modules/training.md
crates/voicex-utils/**                        → docs/modules/voicex-utils.md
crates/voicex-config/**                        → docs/modules/voicex-config.md
```

**注意**：当前项目尚未创建模块 README 文档，AI 在创建新模块或重构模块结构时，应同步创建和维护对应的模块文档。
<!-- END AUTO-DETECTED -->


---

## 7. 历史关键变更（可选）

<!-- AUTO-DETECTED: 以下内容由 AI 自动检测 -->
可记录一些对架构或业务影响较大的里程碑：

- **2024-XX**：VoiceX 基础版发布，支持语音输入法和自动粘贴
- **2024-XX**：引入 Mono-repo 架构，支持 VoiceX 和 VoiceX Pro 双产品
- **2024-XX**：VoiceX Pro 发布，新增 AI 助手模式和 Agent 系统
- **2024-XX**：引入多供应商抽象（STT/TTS/LLM），支持火山引擎、阿里云、腾讯云
- **2024-XX**：实现医药代表陪练系统（训练模块）

这些信息便于 AI 理解系统随时间的演进。
<!-- END AUTO-DETECTED -->
