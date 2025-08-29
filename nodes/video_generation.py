import os
import json
import base64
import requests
from PIL import Image
import folder_paths

class MiniMaxVideoGeneration:
    """
    MiniMax Video Generation node for ComfyUI
    Supports text-to-video, image-to-video, and subject-referenced video generation
    """
    def __init__(self):
        self.api_url = "https://api.minimaxi.chat/v1/video_generation"
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"multiline": False}),
                "model": (["T2V-01-Director", "T2V-01", "I2V-01-Director", "I2V-01", "I2V-01-live", "S2V-01", "MiniMax-Hailuo-02"], {
                    "default": "I2V-01-Director"
                }),
                "prompt": ("STRING", {
                    "multiline": True, 
                    "default": "",
                    "placeholder": "Describe the video generation (max 2000 characters). Leave empty for I2V models if you want auto-generation."
                }),
                "prompt_optimizer": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "first_frame_image": ("IMAGE", {
                    "tooltip": "Required for I2V models (I2V-01-Director, I2V-01, I2V-01-live) and MiniMax-Hailuo-02 with 512P resolution. Optional for other cases."
                }),
                "last_frame_image": ("IMAGE", {
                    "tooltip": "Only supported by MiniMax-Hailuo-02 model. Model will generate video ending with this frame. Not supported with 512P resolution."
                }),
                "duration": (["6", "10"], {
                    "default": "6",
                    "tooltip": "Video duration in seconds. 01 series: only 6s. MiniMax-Hailuo-02: 6s or 10s (10s only available for 512P and 768P resolution)."
                }),
                "resolution": (["512P", "768P", "1080P"], {
                    "default": "768P", 
                    "tooltip": "Video resolution. Only applicable to MiniMax-Hailuo-02 model. 01 series uses fixed 720P resolution."
                }),
                "callback_url": ("STRING", {
                    "multiline": False, 
                    "default": "",
                    "placeholder": "Optional: Callback URL for status updates"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("task_id",)
    FUNCTION = "generate_video"
    CATEGORY = "JM-MiniMax-API/Video"

    def generate_video(self, api_key, model, prompt, prompt_optimizer, first_frame_image=None, last_frame_image=None, duration="6", resolution="768P", callback_url=""):
        if not api_key:
            raise ValueError("API Key must be provided")

        # Check model requirements
        i2v_models = ["I2V-01-Director", "I2V-01", "I2V-01-live"]
        t2v_models = ["T2V-01-Director", "T2V-01"]
        s2v_models = ["S2V-01"]
        hailuo_models = ["MiniMax-Hailuo-02"]
        
        # Validate model-specific requirements
        if model in i2v_models and first_frame_image is None:
            raise ValueError(f"Model {model} requires a first frame image input. Please connect an image to the 'first_frame_image' input.")
        
        if model in t2v_models and not prompt.strip():
            raise ValueError(f"Model {model} requires a text prompt. Please provide a description in the 'prompt' field.")

        # Validate MiniMax-Hailuo-02 specific requirements
        if model in hailuo_models:
            duration_int = int(duration)
            
            # Check duration and resolution combinations
            if duration_int == 10 and resolution == "1080P":
                raise ValueError("MiniMax-Hailuo-02 model does not support 10s duration with 1080P resolution. Please use 512P or 768P for 10s duration or 6s for 1080P.")
            
            # Check 512P resolution requirements
            if resolution == "512P" and first_frame_image is None:
                raise ValueError("MiniMax-Hailuo-02 model with 512P resolution requires a first frame image. Please connect an image to the 'first_frame_image' input.")
            
            # Check last_frame_image with 512P
            if resolution == "512P" and last_frame_image is not None:
                raise ValueError("MiniMax-Hailuo-02 model does not support last_frame_image with 512P resolution. Please use 768P or 1080P resolution.")
        
        # Validate last_frame_image is only used with MiniMax-Hailuo-02
        if last_frame_image is not None and model not in hailuo_models:
            raise ValueError(f"last_frame_image is only supported by MiniMax-Hailuo-02 model, but current model is {model}.")
        
        # Validate duration for 01 series models
        if model not in hailuo_models and duration != "6":
            print(f"Warning: Duration parameter is not applicable to {model}. Using default 6s duration.")
            
        # Validate resolution for 01 series models
        if model not in hailuo_models and resolution != "768P":
            print(f"Warning: Resolution parameter is not applicable to {model}. 01 series models use fixed 720P resolution.")

        try:
            # Prepare API request
            headers = {
                'authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Build payload
            payload = {
                "model": model,
                "prompt": prompt,
                "prompt_optimizer": prompt_optimizer
            }
            
            # Add duration and resolution for MiniMax-Hailuo-02
            if model in hailuo_models:
                payload["duration"] = int(duration)
                payload["resolution"] = resolution
            
            # Helper function to convert ComfyUI image to base64
            def convert_image_to_base64(image_tensor, image_name):
                # Convert ComfyUI image tensor to PIL Image
                if len(image_tensor.shape) == 4:  # Batch dimension
                    # Take the first image from batch
                    tensor = image_tensor[0]
                else:
                    tensor = image_tensor
                
                # Convert from tensor format (H, W, C) with values 0-1 to PIL Image
                import torch
                import numpy as np
                
                # Convert tensor to numpy array and scale to 0-255
                if isinstance(tensor, torch.Tensor):
                    image_np = tensor.cpu().numpy()
                else:
                    image_np = tensor
                    
                # Ensure values are in range 0-1, then scale to 0-255
                image_np = np.clip(image_np, 0, 1)
                image_np = (image_np * 255).astype(np.uint8)
                
                # Convert to PIL Image
                pil_image = Image.fromarray(image_np)
                
                # Validate image dimensions
                width, height = pil_image.size
                aspect_ratio = width / height
                
                if aspect_ratio <= 2/5 or aspect_ratio >= 5/2:
                    raise ValueError(f"{image_name} aspect ratio ({aspect_ratio:.2f}) must be between 2:5 and 5:2")
                
                min_dimension = min(width, height)
                if min_dimension < 300:
                    raise ValueError(f"{image_name} short side ({min_dimension}px) must be at least 300px")
                
                # Convert PIL Image to base64
                import io
                buffer = io.BytesIO()
                
                # Save as JPEG for API compatibility
                if pil_image.mode in ('RGBA', 'LA', 'P'):
                    # Convert to RGB for JPEG
                    pil_image = pil_image.convert('RGB')
                
                pil_image.save(buffer, format='JPEG', quality=95)
                buffer.seek(0)
                
                # Check file size (should be < 20MB)
                file_size = buffer.getbuffer().nbytes
                if file_size > 20 * 1024 * 1024:  # 20MB
                    raise ValueError(f"{image_name} file size ({file_size/1024/1024:.1f}MB) exceeds 20MB limit")
                
                # Convert to base64
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                print(f"{image_name} converted to base64, size: {len(image_base64)} characters")
                print(f"{image_name} dimensions: {width}x{height}, aspect ratio: {aspect_ratio:.2f}")
                
                return f"data:image/jpeg;base64,{image_base64}"
            
            # Handle first frame image
            if first_frame_image is not None:
                payload["first_frame_image"] = convert_image_to_base64(first_frame_image, "First frame image")
            
            # Handle last frame image (only for MiniMax-Hailuo-02)
            if last_frame_image is not None:
                payload["last_frame_image"] = convert_image_to_base64(last_frame_image, "Last frame image")
            
            # Add optional callback URL if provided
            if callback_url.strip():
                payload["callback_url"] = callback_url.strip()
            
            print(f"Sending request to {self.api_url}")
            print(f"Model: {model}")
            print(f"Prompt: {prompt}")
            print(f"Prompt optimizer: {prompt_optimizer}")
            if model in hailuo_models:
                print(f"Duration: {duration}s")
                print(f"Resolution: {resolution}")
            if first_frame_image is not None:
                print(f"First frame image: provided")
            if last_frame_image is not None:
                print(f"Last frame image: provided")
            if callback_url:
                print(f"Callback URL: {callback_url}")
            
            # Make API request
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            print(f"Response status code: {response.status_code}")
            
            try:
                response_data = response.json()
                print(f"Response data: {json.dumps(response_data, indent=2)}")
            except json.JSONDecodeError:
                print(f"Raw response content: {response.content}")
                raise RuntimeError("Failed to decode JSON response")
            
            # Check for API errors
            base_resp = response_data.get("base_resp", {})
            status_code = base_resp.get("status_code")
            status_msg = base_resp.get("status_msg", "Unknown error")
            
            if status_code != 0:
                error_messages = {
                    1002: "Rate limit exceeded, please try again later",
                    1004: "Authentication failed, please check your API key",
                    1008: "Insufficient account balance",
                    1026: "Video description contains sensitive content, please adjust",
                    2013: "Invalid parameters, please check your input",
                    2049: "Invalid API key, please check your API key"
                }
                
                # Special handling for group_id access issues
                if status_code == 2013 and "group_id can not access video 02" in status_msg:
                    error_msg = "Your API key/account does not have access to MiniMax-Hailuo-02 model. Please check your account permissions or contact MiniMax support to enable access to the 02 series models."
                else:
                    error_msg = error_messages.get(status_code, f"API Error {status_code}: {status_msg}")
                
                raise RuntimeError(error_msg)
            
            # Extract task_id
            task_id = response_data.get("task_id")
            if not task_id:
                raise RuntimeError("No task_id returned from API")
            
            print(f"Video generation task created successfully, task_id: {task_id}")
            
            return (task_id,)

        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            raise RuntimeError(f"Failed to connect to MiniMax API: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise RuntimeError(f"Video generation failed: {str(e)}") 