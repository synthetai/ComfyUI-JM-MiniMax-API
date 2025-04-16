# ComfyUI-JM-MiniMax-API

一个集成 MiniMax API 服务的 ComfyUI 自定义节点集合。

[English Document](README.md)

## 功能

### 语音节点 (JM-MiniMax-API/Speech)

- **文本转语音**: 使用 MiniMax 的高级文本转语音 API 将文本转换为自然的语音
- **声音克隆**: 从音频样本中克隆声音
- **加载音频**: 加载和预览用于声音克隆的音频文件

## 安装

1. 克隆此仓库到你的 ComfyUI custom_nodes 文件夹:
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/yourusername/ComfyUI-JM-MiniMax-API.git
```

2. 安装依赖:
```bash
pip install -r requirements.txt
```

3. 重启 ComfyUI

## 使用方法

### LoadAudio 节点

此节点允许您加载和预览用于声音克隆的音频文件。

#### 输入参数:
- **audio_path**: 从输入目录中选择现有的音频文件
- **上传按钮**: 点击上传新的音频文件（支持 .mp3、.wav、.m4a）

#### 输出:
- **audio_file**: 所选音频文件的绝对路径

### VoiceCloning 节点

此节点使用 MiniMax 的声音克隆 API 从音频样本中克隆声音。

#### 输入参数:
- **api_key**: MiniMax API 密钥
- **group_id**: MiniMax 组 ID
- **audio_file**: 要克隆的音频文件路径（连接自 LoadAudio 节点）
- **voice_id**: 克隆声音的 ID（至少 8 个字符，以字母开头，包含数字）
- **need_noise_reduction**: 是否应用噪声降低（true/false）
- **need_volume_normalization**: 是否规范化音量（true/false）
- **preview_text**: 可选的预览克隆声音的文本（最多 300 个字符）
- **model**: 用于预览的 TTS 模型
- **accuracy**: 克隆准确度阈值（0.0-1.0）

#### 输出:
- **voice_id**: 克隆声音的 ID（可以连接到 TextToSpeech 节点）

### TextToSpeech 节点

此节点使用 MiniMax 的 API 将文本转换为语音。

#### 输入参数:
- **api_key**: MiniMax API 密钥
- **group_id**: MiniMax 组 ID
- **text**: 要转换的文本（最多 5000 个字符）
- **model**: TTS 模型选择（speech-02-hd、speech-02-turbo 等）
- **voice_id**: 声音选择（有多种选项可用）
- **custom_voice_id**（可选）: 来自声音克隆的自定义声音 ID（如果提供，将覆盖 voice_id）
- **speed**: 语速（0.5 到 2.0）
- **volume**: 音量（0.1 到 10.0）
- **pitch**: 音调调整（-12 到 12）
- **emotion**: 情感选择（happy、sad 等）
- **subtitle_enable**: 是否生成字幕文件（true/false）
- **filename_prefix**: 输出文件名前缀
- **language_boost**（可选）: 语言增强

#### 输出:
- **audio_path**: 生成的音频文件的绝对路径
- **subtitle_path**: 生成的字幕文件的绝对路径（如果启用了字幕）

#### 输出文件说明:
1. 音频文件 (audio_path):
   - 格式: MP3
   - 文件名格式: prefix_YYYYMMDD-HHMMSS.mp3
   
2. 字幕文件 (subtitle_path):
   - 格式: JSON
   - 文件名格式: prefix_subtitle_YYYYMMDD-HHMMSS.json
   - 包含精确到毫秒的句子级别时间戳

## 工作流示例

1. 使用 **LoadAudio** 节点上传或选择音频文件
2. 将输出连接到 **VoiceCloning** 节点以克隆声音
3. 将 voice_id 输出连接到 **TextToSpeech** 节点的 custom_voice_id 输入
4. 在 TextToSpeech 节点中输入文本并配置其他参数
5. 运行工作流以使用克隆的声音生成语音

## 许可证

MIT License 