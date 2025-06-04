import os
import json
import requests
import folder_paths

class CheckVideoStatus:
    """
    MiniMax Check Video Generation Status node for ComfyUI
    """
    def __init__(self):
        self.api_url = "https://api.minimax.chat/v1/query/video_generation"
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"multiline": False}),
                "task_id": ("STRING", {"multiline": False, "placeholder": "Task ID from video generation"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("status", "file_id", "video_url", "cover_image_url")
    FUNCTION = "check_status"
    CATEGORY = "JM-MiniMax-API/Video"

    def check_status(self, api_key, task_id):
        if not api_key or not task_id:
            raise ValueError("API Key and Task ID must be provided")

        try:
            # Prepare API request
            headers = {
                'authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "task_id": task_id
            }
            
            print(f"Checking status for task_id: {task_id}")
            
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
                    2013: "Invalid parameters, please check your input",
                    2049: "Invalid API key, please check your API key"
                }
                error_msg = error_messages.get(status_code, f"API Error {status_code}: {status_msg}")
                raise RuntimeError(error_msg)
            
            # Extract task information
            status = response_data.get("status", "unknown")
            file_id = response_data.get("file_id", "")
            video_url = response_data.get("video_url", "")
            cover_image_url = response_data.get("cover_image_url", "")
            
            # Additional information for logging
            if "video_width" in response_data and "video_height" in response_data:
                print(f"Video dimensions: {response_data['video_width']}x{response_data['video_height']}")
            
            if "video_length" in response_data:
                print(f"Video length: {response_data['video_length']}s")
            
            print(f"Status: {status}")
            if file_id:
                print(f"File ID: {file_id}")
            if video_url:
                print(f"Video URL: {video_url}")
            if cover_image_url:
                print(f"Cover Image URL: {cover_image_url}")
            
            return (status, file_id, video_url, cover_image_url)

        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            raise RuntimeError(f"Failed to connect to MiniMax API: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise RuntimeError(f"Status check failed: {str(e)}") 