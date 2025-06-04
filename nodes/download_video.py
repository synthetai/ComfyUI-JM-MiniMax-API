import os
import requests
import time
import folder_paths
from urllib.parse import urlparse

class DownloadVideo:
    """
    Download Video from URL node for ComfyUI
    """
    def __init__(self):
        pass
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_url": ("STRING", {"multiline": False, "placeholder": "Video URL from status check"}),
                "filename_prefix": ("STRING", {"default": "minimax_video", "multiline": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "download_video"
    CATEGORY = "JM-MiniMax-API/Video"

    def download_video(self, video_url, filename_prefix):
        if not video_url or not video_url.strip():
            raise ValueError("Video URL must be provided")
        
        video_url = video_url.strip()
        
        try:
            # Validate URL
            parsed_url = urlparse(video_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid video URL provided")
            
            print(f"Downloading video from: {video_url}")
            
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
            with requests.get(video_url, stream=True, timeout=60) as response:
                response.raise_for_status()
                
                # Get content length for progress tracking
                content_length = response.headers.get('content-length')
                if content_length:
                    total_size = int(content_length)
                    print(f"Video file size: {total_size / (1024*1024):.1f} MB")
                else:
                    total_size = None
                    print("Video file size: Unknown")
                
                downloaded_size = 0
                with open(video_filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # Print progress every 1MB
                            if total_size and downloaded_size % (1024*1024) == 0:
                                progress = (downloaded_size / total_size) * 100
                                print(f"Download progress: {progress:.1f}%")
            
            print(f"Video downloaded successfully to: {video_filepath}")
            print(f"Final file size: {os.path.getsize(video_filepath) / (1024*1024):.1f} MB")
            
            return (os.path.abspath(video_filepath),)

        except requests.exceptions.RequestException as e:
            print(f"Download error: {str(e)}")
            raise RuntimeError(f"Failed to download video: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise RuntimeError(f"Video download failed: {str(e)}") 