# ComfyUI-JM-MiniMax-API

A collection of ComfyUI custom nodes that integrate with MiniMax API services.

[中文文档](README_CN.md)

## Features

### Speech Nodes (JM-MiniMax-API/Speech)

- **Text to Speech**: Convert text to natural-sounding speech using MiniMax's advanced text-to-speech API
- **Voice Cloning**: Clone voices from audio samples
- **Load Audio**: Load and preview audio files for voice cloning

## Installation

1. Clone this repository to your ComfyUI custom_nodes folder:
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/yourusername/ComfyUI-JM-MiniMax-API.git
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Restart ComfyUI

## Usage

### Load Audio Node

This node allows you to load and preview audio files for voice cloning.

#### Input Parameters:
- **audio_path**: Select an existing audio file from the input directory
- **Upload Button**: Click to upload a new audio file (supports .mp3, .wav, .m4a)

#### Output:
- **audio_file**: Absolute path to the selected audio file

### Voice Cloning Node

This node uses MiniMax's voice cloning API to clone voices from audio samples.

#### Input Parameters:
- **api_key**: MiniMax API key
- **group_id**: MiniMax group ID
- **audio_file**: Path to the audio file to clone (connect from Load Audio node)
- **voice_id**: ID for the cloned voice (at least 8 characters, start with a letter, include numbers)
- **need_noise_reduction**: Whether to apply noise reduction (true/false)
- **need_volume_normalization**: Whether to normalize volume (true/false)
- **preview_text**: Optional text to preview the cloned voice (max 300 characters)
- **model**: TTS model to use for preview
- **accuracy**: Cloning accuracy threshold (0.0-1.0)

#### Output:
- **voice_id**: ID of the cloned voice (can be connected to TextToSpeech node)

### Text to Speech Node

This node uses MiniMax's API to convert text to speech.

#### Input Parameters:
- **api_key**: MiniMax API key
- **group_id**: MiniMax group ID
- **text**: Text to convert (up to 5000 characters)
- **model**: TTS model selection (speech-02-hd, speech-02-turbo, etc.)
- **voice_id**: Voice selection (multiple options available)
- **custom_voice_id** (optional): Custom voice ID from voice cloning (overrides voice_id if provided)
- **speed**: Speech rate (0.5 to 2.0)
- **volume**: Volume (0.1 to 10.0)
- **pitch**: Pitch adjustment (-12 to 12)
- **emotion**: Emotion selection (happy, sad, etc.)
- **subtitle_enable**: Whether to generate subtitle file (true/false)
- **filename_prefix**: Prefix for output filenames
- **language_boost** (optional): Language enhancement

#### Output:
- **audio_path**: Absolute path to the generated audio file
- **subtitle_path**: Absolute path to the generated subtitle file (if subtitles enabled)

#### Output File Details:
1. Audio File (audio_path):
   - Format: MP3
   - Filename format: prefix_YYYYMMDD-HHMMSS.mp3
   
2. Subtitle File (subtitle_path):
   - Format: JSON
   - Filename format: prefix_subtitle_YYYYMMDD-HHMMSS.json
   - Contains sentence-level timestamps accurate to milliseconds

## Workflow Example

1. Use **Load Audio** node to upload or select an audio file
2. Connect the output to a **Voice Cloning** node to clone the voice
3. Connect the voice_id output to a **Text to Speech** node's custom_voice_id input
4. Enter text and configure other parameters in the Text to Speech node
5. Run the workflow to generate speech using the cloned voice

## License

MIT License
