import os
import requests
import time
import json
import folder_paths
from urllib.parse import urlparse

class DownloadVideo:
    """
    Download Video using file_id from MiniMax API
    """
    def __init__(self):
        self.retrieve_api = "https://api.minimaxi.chat/v1/files/retrieve"
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"multiline": False}),
                "file_id": ("STRING", {"multiline": False, "placeholder": "File ID from video status check"}),
                "filename_prefix": ("STRING", {"default": "minimax_video", "multiline": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "download_video"
    CATEGORY = "JM-MiniMax-API/Video"

    def download_video(self, api_key, file_id, filename_prefix):
        if not api_key or not file_id:
            raise ValueError("API Key and File ID must be provided")
        
        file_id = file_id.strip()
        
        try:
            print(f"Step 1: Retrieving download URL for file_id: {file_id}")
            
            # Step 1: Get download URL using file_id
            retrieve_url = f"{self.retrieve_api}?file_id={file_id}"
            headers = {
                'authorization': f'Bearer {api_key}',
            }
            
            print(f"Retrieve URL: {retrieve_url}")
            
            response = requests.get(retrieve_url, headers=headers, timeout=30)
            
            print(f"Retrieve response status code: {response.status_code}")
            
            if response.status_code != 200:
                raise RuntimeError(f"Failed to retrieve file info. Status code: {response.status_code}")
            
            try:
                retrieve_data = response.json()
                print(f"Retrieve response data: {json.dumps(retrieve_data, indent=2)}")
            except json.JSONDecodeError:
                print(f"Raw retrieve response content: {response.content}")
                raise RuntimeError("Failed to decode JSON response from file retrieve API")
            
            # Check for API errors
            base_resp = retrieve_data.get("base_resp", {})
            status_code = base_resp.get("status_code")
            status_msg = base_resp.get("status_msg", "Unknown error")
            
            if status_code is not None and status_code != 0:
                error_messages = {
                    1002: "Rate limit exceeded, please try again later",
                    1004: "Authentication failed, please check your API key",
                    1008: "Insufficient account balance",
                    2013: "Invalid parameters, please check your file_id",
                    2049: "Invalid API key, please check your API key"
                }
                error_msg = error_messages.get(status_code, f"API Error {status_code}: {status_msg}")
                raise RuntimeError(error_msg)
            
            # Extract download URL
            file_info = retrieve_data.get("file", {})
            download_url = file_info.get("download_url", "")
            
            if not download_url:
                raise RuntimeError("No download URL found in API response")
            
            print(f"Download URL retrieved: {download_url}")
            
            # Step 2: Download the video file
            print(f"Step 2: Downloading video from URL")
            
            # Validate download URL
            parsed_url = urlparse(download_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid download URL received from API")
            
            # Create output directory
            output_dir = folder_paths.get_output_directory()
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate timestamp for filename
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            
            # Clean filename prefix (remove any invalid characters)
            clean_prefix = "".join(c for c in filename_prefix if c.isalnum() or c in ('-', '_'))
            if not clean_prefix:
                clean_prefix = "minimax_video"
            
            # Try to get file extension from URL or default to mp4
            url_path = parsed_url.path
            if url_path and '.' in url_path:
                file_extension = url_path.split('.')[-1].lower()
                # Validate extension
                if file_extension not in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
                    file_extension = 'mp4'
            else:
                file_extension = 'mp4'
            
            # Generate filename
            video_filename = f"{clean_prefix}_{timestamp}.{file_extension}"
            video_filepath = os.path.join(output_dir, video_filename)
            
            # Download video with progress tracking
            print(f"Downloading to: {video_filepath}")
            
            with requests.get(download_url, stream=True, timeout=120) as download_response:
                download_response.raise_for_status()
                
                # Get content length for progress tracking
                content_length = download_response.headers.get('content-length')
                if content_length:
                    total_size = int(content_length)
                    print(f"Video file size: {total_size / (1024*1024):.1f} MB")
                else:
                    total_size = None
                    print("Video file size: Unknown")
                
                downloaded_size = 0
                with open(video_filepath, 'wb') as f:
                    for chunk in download_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # Print progress every 1MB
                            if total_size and downloaded_size % (1024*1024) == 0:
                                progress = (downloaded_size / total_size) * 100
                                print(f"Download progress: {progress:.1f}%")
            
            final_size = os.path.getsize(video_filepath)
            print(f"Video downloaded successfully!")
            print(f"File path: {video_filepath}")
            print(f"Final file size: {final_size / (1024*1024):.1f} MB")
            
            return (os.path.abspath(video_filepath),)

        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            raise RuntimeError(f"Failed to download video: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise RuntimeError(f"Video download failed: {str(e)}") 