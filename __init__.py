from .nodes.text_to_speech import TextToSpeech
from .nodes.voice_cloning import VoiceCloning
from .nodes.voice_design import VoiceDesign
from .nodes.load_audio import JM_LoadAudio
from .nodes.video_generation import MiniMaxVideoGeneration
from .nodes.check_video_status import CheckVideoStatus
from .nodes.download_video import DownloadVideo
from .nodes.music_generation import MusicGeneration

NODE_CLASS_MAPPINGS = {
    "JM-MiniMax-API/text-to-speech": TextToSpeech,
    "JM-MiniMax-API/voice-cloning": VoiceCloning,
    "JM-MiniMax-API/voice-design": VoiceDesign,
    "JM-MiniMax-API/load-audio": JM_LoadAudio,
    "JM-MiniMax-API/video-generation": MiniMaxVideoGeneration,
    "JM-MiniMax-API/check-video-status": CheckVideoStatus,
    "JM-MiniMax-API/download-video": DownloadVideo,
    "JM-MiniMax-API/music-generation": MusicGeneration
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "JM-MiniMax-API/text-to-speech": "MiniMax Text to Speech",
    "JM-MiniMax-API/voice-cloning": "MiniMax Voice Cloning",
    "JM-MiniMax-API/voice-design": "MiniMax Voice Design",
    "JM-MiniMax-API/load-audio": "Load Audio",
    "JM-MiniMax-API/video-generation": "MiniMax Video Generation",
    "JM-MiniMax-API/check-video-status": "Check Video Status",
    "JM-MiniMax-API/download-video": "Download Video",
    "JM-MiniMax-API/music-generation": "MiniMax Music Generation"
}

# Tell ComfyUI where to find web extensions
WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"] 