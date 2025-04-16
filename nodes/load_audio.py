import os
import folder_paths
import shutil

class JM_LoadAudio:
    """
    Load Audio node for ComfyUI
    Supports selecting audio files and provides upload capability
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        files = []
        input_dir = folder_paths.get_input_directory()
        
        if os.path.exists(input_dir):
            for f in os.listdir(input_dir):
                if os.path.isfile(os.path.join(input_dir, f)) and f.split('.')[-1].lower() in ["mp3", "wav", "m4a"]:
                    files.append(f)
        
        return {
            "required": {
                "audio_path": (files,),
            },
            "optional": {
                "upload": ("JMAUDIOUPLOAD",), # Special widget for audio upload
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("audio_file",)
    FUNCTION = "load_audio"
    CATEGORY = "JM-MiniMax-API/Speech"

    def load_audio(self, audio_path, upload=None):
        # Get the full path of the audio file
        audio_file_path = os.path.join(folder_paths.get_input_directory(), audio_path)
        
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        return (audio_file_path,)

    @classmethod
    def IS_CHANGED(cls, audio_path, upload=None):
        if not audio_path:
            return float("nan")
            
        filepath = folder_paths.get_annotated_filepath(audio_path)
        if not os.path.exists(filepath):
            return float("nan")
            
        return os.path.getmtime(filepath)

    @classmethod
    def VALIDATE_INPUTS(cls, audio_path, upload=None):
        if not audio_path:
            return "Please select an audio file"
        
        if not folder_paths.exists_annotated_filepath(audio_path):
            return f"Invalid audio file: {audio_path}"
        
        return True 