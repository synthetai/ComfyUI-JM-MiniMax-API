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
                "model": (["T2V-01-Director", "T2V-01", "I2V-01-Director", "I2V-01", "I2V-01-live", "S2V-01"], {
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
                "image": ("IMAGE", {
                    "tooltip": "Required for I2V models (I2V-01-Director, I2V-01, I2V-01-live). Optional for other models."
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

    def generate_video(self, api_key, model, prompt, prompt_optimizer, image=None, callback_url=""):
        if not api_key:
            raise ValueError("API Key must be provided")

        # Check model requirements
        i2v_models = ["I2V-01-Director", "I2V-01", "I2V-01-live"]
        t2v_models = ["T2V-01-Director", "T2V-01"]
        s2v_models = ["S2V-01"]
        
        if model in i2v_models and image is None:
            raise ValueError(f"Model {model} requires an image input. Please connect an image to the 'image' input.")
        
        if model in t2v_models and not prompt.strip():
            raise ValueError(f"Model {model} requires a text prompt. Please provide a description in the 'prompt' field.")

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
            
            # Handle image input for I2V models
            if model in i2v_models and image is not None:
                # Convert ComfyUI image tensor to PIL Image
                if len(image.shape) == 4:  # Batch dimension
                    # Take the first image from batch
                    image_tensor = image[0]
                else:
                    image_tensor = image
                
                # Convert from tensor format (H, W, C) with values 0-1 to PIL Image
                import torch
                import numpy as np
                
                # Convert tensor to numpy array and scale to 0-255
                if isinstance(image_tensor, torch.Tensor):
                    image_np = image_tensor.cpu().numpy()
                else:
                    image_np = image_tensor
                    
                # Ensure values are in range 0-1, then scale to 0-255
                image_np = np.clip(image_np, 0, 1)
                image_np = (image_np * 255).astype(np.uint8)
                
                # Convert to PIL Image
                pil_image = Image.fromarray(image_np)
                
                # Validate image dimensions
                width, height = pil_image.size
                aspect_ratio = width / height
                
                if aspect_ratio <= 2/5 or aspect_ratio >= 5/2:
                    raise ValueError(f"Image aspect ratio ({aspect_ratio:.2f}) must be between 2:5 and 5:2")
                
                min_dimension = min(width, height)
                if min_dimension < 300:
                    raise ValueError(f"Image short side ({min_dimension}px) must be at least 300px")
                
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
                    raise ValueError(f"Image file size ({file_size/1024/1024:.1f}MB) exceeds 20MB limit")
                
                # Convert to base64
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # Add image to payload
                payload["first_frame_image"] = f"data:image/jpeg;base64,{image_base64}"
                
                print(f"Image converted to base64, size: {len(image_base64)} characters")
                print(f"Image dimensions: {width}x{height}, aspect ratio: {aspect_ratio:.2f}")
            
            # Add optional callback URL if provided
            if callback_url.strip():
                payload["callback_url"] = callback_url.strip()
            
            print(f"Sending request to {self.api_url}")
            print(f"Model: {model}")
            print(f"Prompt: {prompt}")
            print(f"Prompt optimizer: {prompt_optimizer}")
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