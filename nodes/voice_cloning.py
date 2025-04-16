import os
import json
import requests
import folder_paths

class VoiceCloning:
    """
    MiniMax Voice Cloning node for ComfyUI
    """
    def __init__(self):
        self.base_url = "https://api.minimaxi.chat/v1"
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"multiline": False}),
                "group_id": ("STRING", {"multiline": False}),
                "audio_file": ("STRING", {"multiline": False}),  # Path to audio file
                "voice_id": ("STRING", {
                    "multiline": False,
                    "default": "MiniMax001",
                    "placeholder": "At least 8 chars, start with letter, include numbers"
                }),
                "need_noise_reduction": ("BOOLEAN", {"default": False}),
                "need_volume_normalization": ("BOOLEAN", {"default": False}),
                "preview_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Optional: Enter text to preview the cloned voice (max 300 chars)"
                }),
                "model": (["speech-02-hd", "speech-02-turbo", "speech-01-hd", "speech-01-turbo"], {
                    "default": "speech-02-hd"
                }),
                "accuracy": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1
                }),
            }
        }

    RETURN_TYPES = ("STRING",)  # Returns voice_id
    RETURN_NAMES = ("voice_id",)
    FUNCTION = "clone_voice"
    CATEGORY = "JM-MiniMax-API/Speech"

    def clone_voice(self, api_key, group_id, audio_file, voice_id, need_noise_reduction, need_volume_normalization, 
                   preview_text, model, accuracy):
        if not api_key:
            raise ValueError("API Key must be provided")
            
        if not group_id:
            raise ValueError("Group ID must be provided")
            
        if not os.path.exists(audio_file):
            raise ValueError(f"Audio file not found: {audio_file}")
            
        if len(voice_id) < 8 or not voice_id[0].isalpha() or not any(c.isdigit() for c in voice_id):
            raise ValueError("Voice ID must be at least 8 characters, start with a letter, and include numbers")

        try:
            # Step 1: Upload audio file
            print(f"Uploading audio file: {audio_file}")
            upload_url = f"{self.base_url}/files/upload?GroupId={group_id}"
            
            headers = {
                'authority': 'api.minimaxi.chat',
                'Authorization': f'Bearer {api_key}'
            }
            
            data = {
                'purpose': 'voice_clone'
            }
            
            files = {
                'file': open(audio_file, 'rb')
            }

            upload_response = requests.post(
                upload_url,
                headers=headers,
                data=data,
                files=files
            )
            upload_response.raise_for_status()
            upload_data = upload_response.json()
            
            print(f"Upload response: {json.dumps(upload_data, indent=2)}")
            
            # Get file_id from the correct path in response
            file_id = upload_data.get("file", {}).get("file_id")
            if not file_id:
                raise RuntimeError("No file_id returned from upload")

            # Step 2: Clone voice
            print(f"Cloning voice with file_id: {file_id}")
            clone_url = f"{self.base_url}/voice_clone?GroupId={group_id}"
            
            clone_payload = {
                "file_id": file_id,
                "voice_id": voice_id,
                "need_noise_reduction": need_noise_reduction,
                "need_volume_normalization": need_volume_normalization,
                "accuracy": accuracy
            }
            
            # Add optional preview text and model if preview text is provided
            if preview_text.strip():
                if len(preview_text) > 300:
                    print("Warning: Preview text exceeds 300 characters, it will be truncated")
                    preview_text = preview_text[:300]
                clone_payload["text"] = preview_text
                clone_payload["model"] = model

            clone_headers = {
                'authorization': f'Bearer {api_key}',
                'content-type': 'application/json'
            }

            clone_response = requests.post(
                clone_url,
                headers=clone_headers,
                data=json.dumps(clone_payload)
            )
            clone_response.raise_for_status()
            clone_data = clone_response.json()
            
            print(f"Clone response: {json.dumps(clone_data, indent=2)}")
            
            if clone_data.get("base_resp", {}).get("status_code") != 0:
                raise RuntimeError(f"Voice cloning failed: {clone_data.get('base_resp', {}).get('status_msg', 'Unknown error')}")
                
            if clone_data.get("input_sensitive", False):
                print(f"Warning: Input audio triggered sensitivity check (type: {clone_data.get('input_sensitive_type', 'unknown')})")

            return (voice_id,)

        except requests.exceptions.RequestException as e:
            print(f"API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"Error response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Error response content: {e.response.content}")
            raise RuntimeError(f"API request failed: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise RuntimeError(f"Voice cloning failed: {str(e)}") 