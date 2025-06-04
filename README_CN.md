# ComfyUI-JM-MiniMax-API

一个集成 MiniMax API 服务的 ComfyUI 自定义节点集合。

[English Document](README.md)

## 功能

### 语音节点 (JM-MiniMax-API/Speech)

- **文本转语音**: 使用 MiniMax 的高级文本转语音 API 将文本转换为自然的语音
- **声音克隆**: 从音频样本中克隆声音
- **加载音频**: 加载和预览用于声音克隆的音频文件

### 视频节点 (JM-MiniMax-API/Video)

- **视频生成**: 使用 MiniMax 的统一视频生成 API 生成视频（支持文生视频、图生视频和视频主体参考）
- **检查视频状态**: 检查视频生成任务的状态
- **下载视频**: 将生成的视频下载到本地存储

### 视频生成节点

此节点使用 MiniMax 的统一视频生成 API 从文本提示词、图像或主体参考创建视频。

#### 输入参数：
- **api_key**: MiniMax API 密钥
- **model**: 视频生成模型选择：
  - **T2V-01-Director**, **T2V-01**: 文生视频模型（需要文本提示词）
  - **I2V-01-Director**, **I2V-01**, **I2V-01-live**: 图生视频模型（需要图像输入）
  - **S2V-01**: 视频主体参考模型
- **prompt**: 视频生成描述（最多 2000 字符，支持运镜指令）
- **prompt_optimizer**: 是否自动优化提示词以获得更好质量（true/false）
- **image**（可选）: I2V 模型的图像输入（I2V-01-Director, I2V-01, I2V-01-live 必需）
- **callback_url**（可选）: 状态更新回调 URL

#### 模型使用指南：
- **文生视频（T2V 模型）**: 只需要文本提示词。图像输入是可选的。
- **图生视频（I2V 模型）**: 需要图像输入，文本提示词可选。如果提示词为空，模型将根据图像自动生成视频内容。
- **视频主体参考（S2V 模型）**: 目前支持 S2V-01 模型进行主体参考视频生成。

#### 运镜指令：
使用 T2V-01-Director 或 I2V-01-Director 模型时，可以在提示词中使用运镜指令：
- 移动：[左移], [右移], [推进], [拉远], [上升], [下降]
- 旋转：[左摇], [右摇], [上摇], [下摇]
- 变焦：[变焦推近], [变焦拉远]
- 其他：[晃动], [跟随], [固定]

#### 图像要求（适用于 I2V 模型）：
- 格式：JPG/JPEG/PNG
- 长宽比：2:5 到 5:2 之间
- 短边：最少 300px
- 文件大小：最大 20MB

#### 输出：
- **task_id**: 视频生成任务的任务 ID

### 检查视频状态节点

此节点检查视频生成任务的状态。

#### 输入参数：
- **api_key**: MiniMax API 密钥
- **task_id**: 来自视频生成节点的任务 ID

#### 输出：
- **status**: 任务状态（processing, success, failed）
- **file_id**: 生成视频的文件 ID
- **video_url**: 生成视频的下载 URL
- **cover_image_url**: 视频封面图像的 URL

### 下载视频节点

此节点将生成的视频从 URL 下载到本地存储。

#### 输入参数：
- **video_url**: 来自检查视频状态节点的视频 URL
- **filename_prefix**: 下载视频文件的前缀

#### 输出：
- **video_path**: 下载视频文件的绝对路径

## 视频工作流示例

### 文生视频工作流：
1. 使用**视频生成**节点选择 T2V-01-Director 或 T2V-01 模型
2. 输入您的 API 密钥并编写详细的文本提示词
3. 运行以获取 task_id
4. 使用**检查视频状态**节点监控进度
5. 状态为 "success" 后，使用**下载视频**节点保存视频

### 图生视频工作流：
1. 在 ComfyUI 中加载图像（使用加载图像节点）
2. 将其连接到**视频生成**节点
3. 选择 I2V 模型（推荐 I2V-01-Director）
4. 输入 API 密钥，可选择性地编写带有运镜指令的提示词
5. 运行以获取 task_id
6. 使用**检查视频状态**节点监控进度
7. 状态为 "success" 后，使用**下载视频**节点保存视频

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