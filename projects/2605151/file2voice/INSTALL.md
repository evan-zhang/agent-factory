# File2Voice 安装说明

> 产品介绍页：https://doc.20100706.xyz/raw/cd90970cb901
> GitHub 仓库：https://github.com/evan-zhang/agent-factory/tree/master/projects/2605151/file2voice/

## 前置条件

- macOS 或 Linux
- `ffmpeg` 已安装（音频拼接必须）
- `python3` 已安装
- MiniMax 国际版 Token Plan（含 Speech HD 额度）

## 安装方式

### 方式一：git sparse-checkout（推荐）

```bash
git clone --depth 1 --sparse https://github.com/evan-zhang/agent-factory.git
cd agent-factory
git sparse-checkout set projects/2605151/file2voice
```

Skill 目录：`agent-factory/projects/2605151/file2voice/`

### 方式二：复制到 OpenClaw Skills 目录

```bash
# 克隆后复制到 skills 目录
cp -r agent-factory/projects/2605151/file2voice ~/.agents/skills/file2voice
```

## 配置

### 1. API Key

设置环境变量：

```bash
export MINIMAX_API_KEY="sk-cp-xxxxx"
```

建议写入 `~/.zshrc` 或 `~/.bashrc` 持久化。

### 2. mmx-cli（可选，推荐）

mmx-cli 是 MiniMax 官方 CLI 工具，File2Voice 会优先使用它调用 TTS：

```bash
npm install -g mmx-cli
mmx auth login --api-key $MINIMAX_API_KEY
```

验证安装：

```bash
mmx quota
```

如果看到 `speech-hd` 有额度，说明配置成功。

**不安装 mmx-cli 也能用**——File2Voice 会自动降级到直接 API 调用。

### 3. ffmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### 4. 文件解析依赖（可选）

- PDF：`brew install poppler`（pdftotext）或 `pip3 install PyPDF2`
- Word：macOS 自带 `textutil`，Linux 需 `pip3 install python-docx`

## 验证安装

```bash
cd ~/.agents/skills/file2voice  # 或你的安装路径
bash scripts/file2voice.sh --help
```

看到帮助信息说明安装成功。

## 快速测试

创建一个测试文件：

```bash
echo "你好，这是 File2Voice 的测试。将这段文字转为语音。" > /tmp/test.txt
bash scripts/file2voice.sh /tmp/test.txt --auto
```

成功后会在 `/tmp/` 下生成 `test._file2voice.mp3`。
