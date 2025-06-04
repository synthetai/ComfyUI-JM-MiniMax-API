import os
import json
import time
import requests
import folder_paths

class CheckVideoStatus:
    """
    MiniMax Check Video Generation Status node for ComfyUI
    """
    def __init__(self):
        self.api_base = "https://api.minimaxi.chat/v1/query/video_generation"
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"multiline": False}),
                "task_id": ("STRING", {"multiline": False, "placeholder": "Task ID from video generation"}),
                "check_interval": ("INT", {"default": 30, "min": 10, "max": 300, "step": 5, "tooltip": "Check interval in seconds"}),
                "max_wait_time": ("INT", {"default": 1800, "min": 300, "max": 7200, "step": 300, "tooltip": "Maximum wait time in seconds (default: 30 minutes)"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("status", "file_id", "video_url", "cover_image_url")
    FUNCTION = "check_status"
    CATEGORY = "JM-MiniMax-API/Video"

    def check_status(self, api_key, task_id, check_interval=30, max_wait_time=1800):
        if not api_key or not task_id:
            raise ValueError("API Key and Task ID must be provided")

        try:
            # Build URL with task_id as query parameter (as per official API)
            url = f"{self.api_base}?task_id={task_id}"
            
            # Prepare API request headers
            headers = {
                'authorization': f'Bearer {api_key}',
                'content-type': 'application/json',
            }
            
            print(f"Starting status check for task_id: {task_id}")
            print(f"Check interval: {check_interval} seconds")
            print(f"Maximum wait time: {max_wait_time} seconds ({max_wait_time//60} minutes)")
            print(f"Request URL: {url}")
            
            start_time = time.time()
            attempt = 0
            
            while True:
                attempt += 1
                elapsed_time = time.time() - start_time
                
                print(f"\n--- Attempt {attempt} (Elapsed: {elapsed_time:.0f}s) ---")
                
                # Check if we've exceeded the maximum wait time
                if elapsed_time > max_wait_time:
                    raise RuntimeError(f"Maximum wait time ({max_wait_time} seconds) exceeded. Video generation may still be in progress.")
                
                # Make API request using GET method (as per official API)
                response = requests.get(url, headers=headers, timeout=30)
                
                print(f"Response status code: {response.status_code}")
                
                if response.status_code == 404:
                    raise RuntimeError("Video generation task not found. Please check your task_id.")
                
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
                
                if status_code is not None and status_code != 0:
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
                    video_width = response_data['video_width']
                    video_height = response_data['video_height']
                    if video_width > 0 and video_height > 0:
                        print(f"Video dimensions: {video_width}x{video_height}")
                
                if "video_length" in response_data and response_data['video_length']:
                    print(f"Video length: {response_data['video_length']}s")
                
                print(f"Status: {status}")
                if file_id:
                    print(f"File ID: {file_id}")
                if video_url:
                    print(f"Video URL: {video_url}")
                if cover_image_url:
                    print(f"Cover Image URL: {cover_image_url}")
                
                # Check if the task is completed
                if status.lower() == "success":
                    print(f"\n🎉 Video generation completed successfully!")
                    print(f"Total time: {elapsed_time:.0f} seconds ({elapsed_time/60:.1f} minutes)")
                    return (status, file_id, video_url, cover_image_url)
                elif status.lower() == "failed":
                    print(f"\n❌ Video generation failed!")
                    raise RuntimeError(f"Video generation failed with status: {status}")
                else:
                    # Status is still processing/preparing, wait and try again
                    print(f"Status: {status} - Waiting {check_interval} seconds before next check...")
                    
                    # Show progress
                    remaining_time = max(0, max_wait_time - elapsed_time)
                    print(f"Remaining wait time: {remaining_time:.0f} seconds ({remaining_time/60:.1f} minutes)")
                    
                    time.sleep(check_interval)

        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            raise RuntimeError(f"Failed to connect to MiniMax API: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise RuntimeError(f"Status check failed: {str(e)}") 