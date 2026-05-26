---
name: minimax-tts
description: Use MiniMax speech-02-hd model for high-quality text-to-speech synthesis. Supports 58 Mandarin Chinese + 16 English voices (74 total). Install when needed.
homepage: https://platform.minimax.io
metadata: {"clawdbot":{"emoji":"🔊","requires":{"bins":["python"]}}}
---

# MiniMax Text-to-Speech

调用方式：`python scripts/minimax_media.py tts "<文本>" [选项]`

## 基本用法

```bash
python scripts/minimax_media.py tts "你好，这是语音测试。" --voice female-shaonv --speed 1.0
```

## 选项说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--voice` | 音色 ID（见下方列表） | female-tianmei |
| `--speed` | 语速，范围 0.5 ~ 2.0 | 1.0 |
| `--output` | 输出文件路径 | media/tts_output.mp3 |

返回：`{"audio_path": "...", "size_bytes": ..., "duration_hint": "..."}`

---

## 完整音色列表（来源：官方 /faq/system-voice-id）

> 共 **74 个**（58 中文普通话 + 16 英文）。其他语言（粤语/日文/韩文/西班牙文/葡萄牙文）见官方页面。

### 中文普通话（58 个）

| Voice ID | 音色名称 |
|----------|---------|
| `male-qn-qingse` | 青涩青年音色 |
| `male-qn-jingying` | 精英青年音色 |
| `male-qn-badao` | 霸道青年音色 |
| `male-qn-daxuesheng` | 青年大学生音色 |
| `female-shaonv` | 少女音色 |
| `female-yujie` | 御姐音色 |
| `female-chengshu` | 成熟女性音色 |
| `female-tianmei` | 甜美女性音色 |
| `male-qn-qingse-jingpin` | 青涩青年音色-beta |
| `male-qn-jingying-jingpin` | 精英青年音色-beta |
| `male-qn-badao-jingpin` | 霸道青年音色-beta |
| `male-qn-daxuesheng-jingpin` | 青年大学生音色-beta |
| `female-shaonv-jingpin` | 少女音色-beta |
| `female-yujie-jingpin` | 御姐音色-beta |
| `female-chengshu-jingpin` | 成熟女性音色-beta |
| `female-tianmei-jingpin` | 甜美女性音色-beta |
| `clever_boy` | 聪明男童 |
| `cute_boy` | 可爱男童 |
| `lovely_girl` | 萌萌女童 |
| `cartoon_pig` | 卡通猪小琪 |
| `bingjiao_didi` | 病娇弟弟 |
| `junlang_nanyou` | 俊朗男友 |
| `chunzhen_xuedi` | 纯真学弟 |
| `lengdan_xiongzhang` | 冷淡学长 |
| `badao_shaoye` | 霸道少爷 |
| `tianxin_xiaoling` | 甜心小玲 |
| `qiaopi_mengmei` | 俏皮萌妹 |
| `wumei_yujie` | 妩媚御姐 |
| `diadia_xuemei` | 嗲嗲学妹 |
| `danya_xuejie` | 淡雅学姐 |
| `Chinese (Mandarin)_Reliable_Executive` | 沉稳高管 |
| `Chinese (Mandarin)_News_Anchor` | 新闻女声 |
| `Chinese (Mandarin)_Mature_Woman` | 傲娇御姐 |
| `Chinese (Mandarin)_Unrestrained_Young_Man` | 不羁青年 |
| `Arrogant_Miss` | 嚣张小姐 |
| `Robot_Armor` | 机械战甲 |
| `Chinese (Mandarin)_Kind-hearted_Antie` | 热心大婶 |
| `Chinese (Mandarin)_HK_Flight_Attendant` | 港普空姐 |
| `Chinese (Mandarin)_Humorous_Elder` | 搞笑大爷 |
| `Chinese (Mandarin)_Gentleman` | 温润男声 |
| `Chinese (Mandarin)_Warm_Bestie` | 温暖闺蜜 |
| `Chinese (Mandarin)_Male_Announcer` | 播报男声 |
| `Chinese (Mandarin)_Sweet_Lady` | 甜美女声 |
| `Chinese (Mandarin)_Southern_Young_Man` | 南方小哥 |
| `Chinese (Mandarin)_Wise_Women` | 阅历姐姐 |
| `Chinese (Mandarin)_Gentle_Youth` | 温润青年 |
| `Chinese (Mandarin)_Warm_Girl` | 温暖少女 |
| `Chinese (Mandarin)_Kind-hearted_Elder` | 花甲奶奶 |
| `Chinese (Mandarin)_Cute_Spirit` | 憨憨萌兽 |
| `Chinese (Mandarin)_Radio_Host` | 电台男主播 |
| `Chinese (Mandarin)_Lyrical_Voice` | 抒情男声 |
| `Chinese (Mandarin)_Straightforward_Boy` | 率真弟弟 |
| `Chinese (Mandarin)_Sincere_Adult` | 真诚青年 |
| `Chinese (Mandarin)_Gentle_Senior` | 温柔学姐 |
| `Chinese (Mandarin)_Stubborn_Friend` | 嘴硬竹马 |
| `Chinese (Mandarin)_Crisp_Girl` | 清脆少女 |
| `Chinese (Mandarin)_Pure-hearted_Boy` | 清澈邻家弟弟 |
| `Chinese (Mandarin)_Soft_Girl` | 柔和少女 |

### 英文（16 个）

| Voice ID | 音色名称 |
|----------|---------|
| `Santa_Claus` | Santa Claus |
| `Grinch` | Grinch |
| `Rudolph` | Rudolph |
| `Arnold` | Arnold |
| `Charming_Santa` | Charming Santa |
| `Charming_Lady` | Charming Lady |
| `Sweet_Girl` | Sweet Girl |
| `Cute_Elf` | Cute Elf |
| `Attractive_Girl` | Attractive Girl |
| `Serene_Woman` | Serene Woman |
| `English_Trustworthy_Man` | Trustworthy Man |
| `English_Graceful_Lady` | Graceful Lady |
| `English_Aussie_Bloke` | Aussie Bloke |
| `English_Whispering_girl` | Whispering girl |
| `English_Diligent_Man` | Diligent Man |
| `English_Gentle-voiced_man` | Gentle-voiced man |

---

## 进阶功能

### 情感控制（仅 Novita API 支持）

通过 `emotion` 参数控制情感：

| emotion 值 | 情感 |
|------------|------|
| `happy` | 开心 |
| `sad` | 悲伤 |
| `angry` | 愤怒 |
| `fearful` | 恐惧 |
| `disgusted` | 厌恶 |
| `surprised` | 惊讶 |
| `neutral` | 中性（默认） |

### 音色混音（仅 Novita API 支持）

通过 `timbre_weights` 混合多个音色（最多 4 个）：

```
timbre_weights = [
  {"voice_id": "Chinese (Mandarin)_Wise_Women", "weight": 70},
  {"voice_id": "Chinese (Mandarin)_Crisp_Girl", "weight": 30}
]
```

权重越高，合成声音越接近该音色。

---

## 音色切换记忆

faiz 当前偏好的音色：** female-shaonv **（少女音色）

切换音色时，直接在命令中指定新的 `--voice <ID>` 即可。

---

## 语音识别（ASR）

已配置 **本地 Whisper** 进行语音识别：
- 模型：`base`（中文优化）
- 准确率：~98%（比 Google 免费版高 10%）
- 依赖：`ffmpeg`（位于 `~/.local/bin/ffmpeg`）

处理流程：
1. 接收 Telegram 语音（.ogg 格式）
2. 转换采样率（soundfile + scipy）
3. 调用 Whisper 本地推理

## 环境变量

- `MINIMAX_API_KEY` — 必填，MiniMax API 密钥
- `MINIMAX_BASE_URL` — 可选，默认 `https://api.minimax.io`
