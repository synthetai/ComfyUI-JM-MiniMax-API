import os
import json
import time
import binascii
import requests
import folder_paths
import urllib.parse

class TextToSpeech:
    """
    MiniMax Text to Speech node for ComfyUI
    """
    def __init__(self):
        self.api_base = "https://api.minimaxi.chat/v1/t2a_v2"
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"multiline": False}),
                "group_id": ("STRING", {"multiline": False}),
                "text": ("STRING", {"multiline": True}),
                "model": (["speech-02-hd", "speech-02-turbo", "speech-01-hd", "speech-01-turbo"], {"default": "speech-02-hd"}),
                "voice_id": ("STRING", {
                    "multiline": False, 
                    "default": "", 
                    "placeholder": "Voice ID for text-to-speech"
                }),
                "speed": ("FLOAT", {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.1}),
                "volume": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.1}),
                "pitch": ("INT", {"default": 0, "min": -12, "max": 12, "step": 1}),
                "emotion": (["", "happy", "sad", "angry", "fearful", "disgusted", "surprised", "neutral"], {"default": ""}),
                "subtitle_enable": ("BOOLEAN", {"default": False}),
                "filename_prefix": ("STRING", {"default": "tts_output", "multiline": False}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
            },
            "optional": {
                "custom_voice_id": ("STRING", {
                    "multiline": False, 
                    "default": "", 
                    "placeholder": "Custom voice ID from voice cloning"
                }),
                "language_boost": (["auto", "Chinese", "Chinese,Yue", "English", "Arabic", "Russian", "Spanish", 
                                  "French", "Portuguese", "German", "Turkish", "Dutch", "Ukrainian", "Vietnamese", 
                                  "Indonesian", "Japanese", "Italian", "Korean", "Thai", "Polish", "Romanian", 
                                  "Greek", "Czech", "Finnish", "Hindi"], {"default": "auto"}),
                "output_format": (["hex", "url"], {
                    "default": "hex", 
                    "tooltip": "hex: 返回十六进制编码的音频数据; url: 返回音频下载链接(有效期24小时)"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("audio_path", "subtitle_path")
    FUNCTION = "generate_speech"
    CATEGORY = "JM-MiniMax-API/Speech"

    def generate_speech(self, api_key, group_id, text, model, voice_id, speed, volume, pitch, emotion, subtitle_enable, filename_prefix, seed, custom_voice_id="", language_boost="auto", output_format="hex"):
        if not api_key or not group_id:
            raise ValueError("API Key and Group ID must be provided")
        
        # Handle seed parameter type conversion and validation
        try:
            if seed is None or seed == "" or seed == "":
                seed = 0  # Default to 0 for random seed
            else:
                seed = int(seed)  # Ensure it's an integer
        except (ValueError, TypeError):
            print(f"⚠️ 无效的seed值: {seed}，使用默认值 0")
            seed = 0
        
        # Log seed for execution tracking (seed is not sent to API, just for ComfyUI execution control)
        print(f"🎲 执行种子 (Seed): {seed}")
        
        # Generate random seed if seed is 0
        if seed == 0:
            import random
            actual_seed = random.randint(1, 0xffffffffffffffff)
            print(f"🎯 自动生成随机种子: {actual_seed}")
        else:
            actual_seed = seed
            print(f"🎯 使用指定种子: {actual_seed}")

        url = f"{self.api_base}?GroupId={group_id}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "accept": "application/json, text/plain, */*"
        }

        # Use custom_voice_id if provided, otherwise use voice_id
        selected_voice_id = custom_voice_id if custom_voice_id else voice_id
        print(f"Using voice_id: {selected_voice_id} {'(custom)' if custom_voice_id else '(predefined)'}")

        # Build voice_setting
        voice_setting = {
            "voice_id": selected_voice_id,
            "speed": speed,
            "vol": volume,
            "pitch": pitch
        }
        
        # Only add emotion if it's not empty
        if emotion and emotion.strip():
            voice_setting["emotion"] = emotion
            print(f"Adding emotion parameter: {emotion}")
        else:
            print("Emotion parameter not provided, using default voice emotion")

        payload = {
            "model": model,
            "text": text,
            "voice_setting": voice_setting,
            "language_boost": language_boost,
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1
            },
            "subtitle_enable": subtitle_enable,
            "output_format": output_format
        }

        try:
            print(f"Sending request to {url}")
            print(f"Output format: {output_format}")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(url, headers=headers, json=payload)
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
            
            try:
                resp_data = response.json()
                print(f"Response data: {json.dumps(resp_data, indent=2)}")
            except json.JSONDecodeError:
                print(f"Raw response content: {response.content}")
                raise RuntimeError("Failed to decode JSON response")
            
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
            
            # Create output directory
            output_dir = folder_paths.get_output_directory()
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate timestamp for filenames
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            
            # Clean filename prefix (remove any invalid characters)
            clean_prefix = "".join(c for c in filename_prefix if c.isalnum() or c in ('-', '_'))
            if not clean_prefix:
                clean_prefix = "tts_output"
            
            # Process audio based on output format
            audio_filename = f"{clean_prefix}_{timestamp}.mp3"
            audio_filepath = os.path.join(output_dir, audio_filename)
            
            if output_format == "url":
                # Handle URL format response
                audio_url = data.get("audio", "")
                if not audio_url:
                    raise RuntimeError("No audio URL returned")
                
                # Decode Unicode escapes in the URL (\u0026 -> &)
                audio_url = audio_url.encode().decode('unicode_escape')
                print(f"Audio download URL: {audio_url}")
                
                # Download audio from URL
                print(f"Downloading audio from URL...")
                audio_response = requests.get(audio_url)
                audio_response.raise_for_status()
                
                with open(audio_filepath, "wb") as f:
                    f.write(audio_response.content)
                print(f"Downloaded and saved audio file to: {audio_filepath}")
                
            else:
                # Handle hex format response (original logic)
                audio_hex = data.get("audio", "")
                if not audio_hex:
                    raise RuntimeError("No audio data returned")
                
                print(f"Received audio hex data length: {len(audio_hex)}")
                audio_data = binascii.unhexlify(audio_hex)
                print(f"Decoded audio data length: {len(audio_data)}")
                
                with open(audio_filepath, "wb") as f:
                    f.write(audio_data)
                print(f"Saved audio file to: {audio_filepath}")
            
            # Save subtitle file if available
            subtitle_filepath = ""
            if subtitle_enable and data.get("subtitle_file"):
                subtitle_filename = f"{clean_prefix}_subtitle_{timestamp}.json"
                subtitle_filepath = os.path.join(output_dir, subtitle_filename)
                subtitle_response = requests.get(data["subtitle_file"])
                subtitle_response.raise_for_status()
                with open(subtitle_filepath, "wb") as f:
                    f.write(subtitle_response.content)
                print(f"Saved subtitle file to: {subtitle_filepath}")
            
            return (
                os.path.abspath(audio_filepath),
                os.path.abspath(subtitle_filepath) if subtitle_filepath else ""
            )

        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Error response status code: {e.response.status_code}")
                print(f"Error response headers: {json.dumps(dict(e.response.headers), indent=2)}")
                try:
                    error_data = e.response.json()
                    print(f"Error response data: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Error response content: {e.response.content}")
            raise RuntimeError(f"Error calling MiniMax API: {str(e)}")
        except (ValueError, binascii.Error) as e:
            print(f"Data processing error: {str(e)}")
            raise RuntimeError(f"Error processing API response: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise RuntimeError(f"Unexpected error: {str(e)}") 