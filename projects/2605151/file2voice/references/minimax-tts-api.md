# MiniMax Speech TTS API 参考文档（已验证）

> **验证日期**：2026-05-15
> **官方文档**：https://platform.minimax.io/docs/api-reference/speech-t2a-http

---

## API 调用

**Endpoint**：`POST https://api.minimax.io/v1/t2a_v2`

**Header**：
```
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

**请求体**：
```json
{
  "model": "speech-02-turbo",
  "text": "要转换的文本",
  "stream": false,
  "output_format": "hex",
  "voice_setting": {
    "voice_id": "Chinese (Mandarin)_Male_Announcer",
    "speed": 1,
    "vol": 1,
    "pitch": 0
  },
  "audio_setting": {
    "sample_rate": 32000,
    "bitrate": 128000,
    "format": "mp3",
    "channel": 1
  }
}
```

## 可用模型

| 模型 | 说明 |
|------|------|
| `speech-02-turbo` | 推荐，速度快，Token Plan 额度内 |
| `speech-02-hd` | 高质量 |
| `speech-2.8-hd` | 最新版，高质量（推荐，Max-Highspeed 套餐额度） |
| `speech-2.8-turbo` | 最新版，速度快 |

## 中文音色列表（精选）

| Voice ID | 说明 |
|----------|------|
| `Chinese (Mandarin)_Male_Announcer` | 男声-播音员 |
| `Chinese (Mandarin)_News_Anchor` | 男声-新闻主播 |
| `Chinese (Mandarin)_Reliable_Executive` | 男声-可靠主管 |
| `Chinese (Mandarin)_Gentleman` | 男声-绅士 |
| `Chinese (Mandarin)_Radio_Host` | 男声-电台主持人 |
| `Chinese (Mandarin)_Warm_Girl` | 女声-温暖少女 |
| `Chinese (Mandarin)_Sweet_Lady` | 女声-甜美女声 |
| `Chinese (Mandarin)_Mature_Woman` | 女声-成熟女性 |
| `Chinese (Mandarin)_Crisp_Girl` | 女声-清脆少女 |
| `Chinese (Mandarin)_Kind-hearted_Antie` | 女声-善良阿姨 |

完整列表：https://platform.minimax.io/docs/faq/system-voice-id

## 响应格式（非流式）

```json
{
  "data": {
    "audio": "<hex编码音频数据>",
    "status": 2
  },
  "extra_info": {
    "audio_length": 11124,
    "audio_sample_rate": 32000,
    "audio_size": 179926,
    "word_count": 163,
    "usage_characters": 163,
    "audio_format": "mp3"
  },
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  }
}
```

**重要**：非流式返回的是 JSON（不是二进制），音频数据在 `data.audio` 字段，hex 编码，需解码为二进制保存。

## 文本限制

- 单次最长 **10,000 字符**
- 超过 3,000 字符建议用流式
- 用 `<#x#>` 控制停顿（x 为秒数，如 `<#0.5#>`）

## 额度

Token Plan 按天配额，每日 UTC 零点重置。

---

*本文件基于 2026-05-15 实际 API 验证更新，原始参考文档有误（model/voice_id/响应格式均不同）。*
