import os
import json
import time
import binascii
import requests
import folder_paths

class MusicGeneration:
    """
    MiniMax Music Generation node for ComfyUI
    Generates music based on prompt description and lyrics using MiniMax API
    """
    def __init__(self):
        self.api_base = "https://api.minimaxi.com/v1/music_generation"
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"multiline": False}),
                "prompt": ("STRING", {
                    "multiline": True,
                    "placeholder": "音乐描述，例如：流行音乐, 难过, 适合在下雨的晚上",
                    "tooltip": "音乐的描述，用于指定风格、情绪和场景。长度限制为10-300个字符"
                }),
                "lyrics": ("STRING", {
                    "multiline": True,
                    "placeholder": "歌曲歌词，使用\\n分隔每行，可加入[Intro], [Verse], [Chorus]等结构标签",
                    "tooltip": "歌曲的歌词，使用\\n分隔每行。长度限制为10-600个字符"
                }),
                "model": (["music-1.5"], {"default": "music-1.5"}),
                "filename_prefix": ("STRING", {"default": "music_output", "multiline": False}),
            },
            "optional": {
                "stream": ("BOOLEAN", {"default": False, "tooltip": "是否使用流式传输"}),
                "output_format": (["hex", "url"], {
                    "default": "hex", 
                    "tooltip": "hex: 返回十六进制编码的音频数据; url: 返回音频下载链接(有效期24小时)"
                }),
                "sample_rate": ([16000, 24000, 32000, 44100], {"default": 44100}),
                "bitrate": ([32000, 64000, 128000, 256000], {"default": 256000}),
                "format": (["mp3", "wav", "pcm"], {"default": "mp3"}),
                "aigc_watermark": ("BOOLEAN", {"default": False, "tooltip": "是否在音频末尾添加水印"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("audio_path", "audio_url")
    FUNCTION = "generate_music"
    CATEGORY = "JM-MiniMax-API/Music"

    def generate_music(self, api_key, prompt, lyrics, model, filename_prefix, stream=False, output_format="hex", 
                     sample_rate=44100, bitrate=256000, format="mp3", aigc_watermark=False):
        """
        Generate music using MiniMax API
        
        Args:
            api_key: MiniMax API key
            prompt: Music description (10-300 characters)
            lyrics: Song lyrics (10-600 characters)
            model: Model name (music-1.5)
            filename_prefix: Output filename prefix
            stream: Whether to use streaming
            output_format: Output format (hex or url)
            sample_rate: Audio sample rate
            bitrate: Audio bitrate
            format: Audio format (mp3, wav, pcm)
            aigc_watermark: Whether to add watermark
        """
        if not api_key:
            raise ValueError("API Key must be provided")
        
        # Validate prompt length (10-300 characters)
        if not prompt or len(prompt.strip()) < 10:
            raise ValueError("Prompt must be at least 10 characters long")
        if len(prompt) > 300:
            raise ValueError("Prompt must not exceed 300 characters")
        
        # Validate lyrics length (10-600 characters)
        if not lyrics or len(lyrics.strip()) < 10:
            raise ValueError("Lyrics must be at least 10 characters long")
        if len(lyrics) > 600:
            raise ValueError("Lyrics must not exceed 600 characters")
        
        # Validate stream and output_format combination
        if stream and output_format == "url":
            raise ValueError("When stream is true, only hex format is supported")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Build audio_setting
        audio_setting = {
            "sample_rate": sample_rate,
            "bitrate": bitrate,
            "format": format
        }

        payload = {
            "model": model,
            "prompt": prompt.strip(),
            "lyrics": lyrics.strip(),
            "stream": stream,
            "output_format": output_format,
            "audio_setting": audio_setting,
            "aigc_watermark": aigc_watermark
        }

        try:
            print(f"🎵 Generating music with MiniMax API...")
            print(f"📝 Prompt: {prompt[:50]}...")
            print(f"🎶 Lyrics preview: {lyrics[:50]}...")
            print(f"⚙️ Audio settings: {audio_setting}")
            print(f"📤 Output format: {output_format}")
            
            response = requests.post(self.api_base, headers=headers, json=payload)
            print(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                response.raise_for_status()
            
            resp_data = response.json()
            print(f"Response data keys: {list(resp_data.keys())}")
            
            # Check for API error response
            base_resp = resp_data.get("base_resp", {})
            status_code = base_resp.get("status_code")
            status_msg = base_resp.get("status_msg", "Unknown error")
            
            if status_code is not None and status_code != 0:
                raise RuntimeError(f"API Error {status_code}: {status_msg}")
            
            data = resp_data.get("data", {})
            if not data:
                print(f"Full response: {json.dumps(resp_data, indent=2)}")
                raise RuntimeError("No data returned from API")
            
            # Check music generation status
            status = data.get("status")
            if status == 1:
                print("⚠️ Music is still being generated, but API returned partial data")
            elif status == 2:
                print("✅ Music generation completed")
            
            # Create output directory
            output_dir = folder_paths.get_output_directory()
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate timestamp for filename
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            
            # Clean filename prefix
            clean_prefix = "".join(c for c in filename_prefix if c.isalnum() or c in ('-', '_'))
            if not clean_prefix:
                clean_prefix = "music_output"
            
            # Process audio based on output format
            audio_filename = f"{clean_prefix}_{timestamp}.{format}"
            audio_filepath = os.path.join(output_dir, audio_filename)
            processed_audio_url = ""  # Initialize audio_url variable
            
            if output_format == "url":
                # Handle URL format response
                audio_url = data.get("audio", "")
                if not audio_url:
                    raise RuntimeError("No audio URL returned")
                
                processed_audio_url = audio_url
                print(f"Audio download URL: {processed_audio_url}")
                
                # Download audio from URL
                print(f"Downloading audio from URL...")
                audio_response = requests.get(processed_audio_url)
                audio_response.raise_for_status()
                
                with open(audio_filepath, "wb") as f:
                    f.write(audio_response.content)
                print(f"Downloaded and saved audio file to: {audio_filepath}")
                
            else:
                # Handle hex format response
                audio_hex = data.get("audio", "")
                if not audio_hex:
                    raise RuntimeError("No audio data returned")
                
                print(f"Received audio hex data length: {len(audio_hex)}")
                try:
                    audio_data = binascii.unhexlify(audio_hex)
                    print(f"Decoded audio data length: {len(audio_data)}")
                    
                    with open(audio_filepath, "wb") as f:
                        f.write(audio_data)
                    print(f"Saved audio file to: {audio_filepath}")
                except binascii.Error as e:
                    raise RuntimeError(f"Failed to decode hex audio data: {str(e)}")
            
            # Log extra info if available
            extra_info = resp_data.get("extra_info", {})
            if extra_info:
                print(f"📊 Music info:")
                print(f"   Duration: {extra_info.get('music_duration', 'N/A')} ms")
                print(f"   Sample rate: {extra_info.get('music_sample_rate', 'N/A')} Hz")
                print(f"   Channels: {extra_info.get('music_channel', 'N/A')}")
                print(f"   Bitrate: {extra_info.get('bitrate', 'N/A')} bps")
                print(f"   File size: {extra_info.get('music_size', 'N/A')} bytes")
            
            return (
                os.path.abspath(audio_filepath),
                processed_audio_url
            )

        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Error response status code: {e.response.status_code}")
                print(f"Error response content: {e.response.text}")
            raise RuntimeError(f"Error calling MiniMax API: {str(e)}")
        except (ValueError, binascii.Error) as e:
            print(f"Data processing error: {str(e)}")
            raise RuntimeError(f"Error processing API response: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise RuntimeError(f"Unexpected error: {str(e)}")
