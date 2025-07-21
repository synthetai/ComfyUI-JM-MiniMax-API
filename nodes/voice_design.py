import os
import json
import time
import requests
import folder_paths

class VoiceDesign:
    """
    MiniMax Voice Design node for ComfyUI - Generate custom voices from text descriptions
    """
    def __init__(self):
        self.api_base = "https://api.minimax.io/v1/voice_design"
        
    def _detect_audio_format(self, audio_data):
        """
        检测音频数据的格式
        通过文件头部的魔术字节来识别音频格式
        """
        if not audio_data or len(audio_data) < 12:
            return "bin"  # 数据不足，使用通用二进制扩展名
        
        # 检查常见音频格式的文件头
        header = audio_data[:12]
        
        # WAV 格式: RIFF....WAVE
        if header.startswith(b'RIFF') and header[8:12] == b'WAVE':
            return "wav"
        
        # MP3 格式: ID3 标签或 MPEG 帧头
        if header.startswith(b'ID3') or header.startswith(b'\xff\xfb'):
            return "mp3"
        
        # FLAC 格式: fLaC
        if header.startswith(b'fLaC'):
            return "flac"
        
        # OGG 格式: OggS
        if header.startswith(b'OggS'):
            return "ogg"
        
        # AAC 格式: ADTS 头部
        if len(audio_data) >= 2 and (audio_data[0] == 0xff and (audio_data[1] & 0xf0) == 0xf0):
            return "aac"
        
        # M4A/MP4 格式: ftyp
        if b'ftyp' in header[:8]:
            return "m4a"
        
        # 默认返回wav（最常见的格式）
        print("⚠️ 无法识别音频格式，默认使用wav")
        return "wav"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"multiline": False}),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "讲述悬疑故事的播音员，声音低沉富有磁性，语速时快时慢，营造紧张神秘的氛围。",
                    "placeholder": "描述您想要的音色特征，如：性别、年龄、情感、语速、音调、使用场景等"
                }),
                "preview_text": ("STRING", {
                    "multiline": True,
                    "default": "夜深了，古屋里只有他一人。窗外传来若有若无的脚步声，他屏住呼吸，慢慢地，慢慢地，走向那扇吱呀作响的门……",
                    "placeholder": "用于试听的文本内容（可选，不超过200字）"
                }),
            },
            "optional": {
                "custom_voice_id": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "自定义音色ID（可选）。如果为空，将自动生成唯一ID"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("voice_id", "trial_audio")
    FUNCTION = "design_voice"
    CATEGORY = "JM-MiniMax-API/Speech"

    def design_voice(self, api_key, prompt, preview_text, custom_voice_id=""):
        if not api_key:
            raise ValueError("API Key must be provided")
        
        if not prompt.strip():
            raise ValueError("音色描述不能为空")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        # 生成或使用自定义voice_id
        if custom_voice_id and custom_voice_id.strip():
            voice_id = custom_voice_id.strip()
            print(f"🎯 使用自定义音色ID: {voice_id}")
        else:
            # 自动生成唯一的voice_id
            import uuid
            current_timestamp = int(time.time())
            unique_id = str(uuid.uuid4()).replace('-', '')[:8]
            voice_id = f"voice_{current_timestamp}_{unique_id}"
            print(f"🔄 自动生成音色ID: {voice_id}")

        # 构建请求数据
        payload = {
            "prompt": prompt.strip(),
            "voice_id": voice_id
        }
        
        # 如果提供了预览文本，则添加到请求中
        if preview_text and preview_text.strip():
            payload["preview_text"] = preview_text.strip()

        try:
            print(f"🎙️ Voice Design: 正在根据描述生成定制音色")
            print(f"📝 音色描述: {prompt}")
            if preview_text:
                print(f"🔊 预览文本: {preview_text}")
            
            response = requests.post(self.api_base, headers=headers, json=payload)
            print(f"📡 API响应状态: {response.status_code}")
            
            # 检查HTTP状态码
            response.raise_for_status()
            
            try:
                resp_data = response.json()
                print(f"📋 API响应: {json.dumps(resp_data, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError:
                print(f"❌ 无法解析JSON响应")
                print(f"原始响应: {response.content}")
                raise RuntimeError("无法解析API响应")
            
            # 检查API错误响应
            if "base_resp" in resp_data:
                base_resp = resp_data.get("base_resp", {})
                status_code = base_resp.get("status_code")
                status_msg = base_resp.get("status_msg", "未知错误")
                
                if status_code is not None and status_code != 0:
                    raise RuntimeError(f"API错误 {status_code}: {status_msg}")
            
            # 检查API返回的音色ID（应该与我们发送的一致）
            returned_voice_id = resp_data.get("voice_id")
            if returned_voice_id:
                print(f"✅ API确认音色ID: {returned_voice_id}")
                # 使用API返回的voice_id（可能与发送的稍有不同）
                final_voice_id = returned_voice_id
            else:
                # 如果API没有返回voice_id，使用我们发送的
                print(f"ℹ️ API未返回voice_id，使用发送的ID")
                final_voice_id = voice_id
            
            print(f"✅ 音色生成成功！最终音色ID: {final_voice_id}")
            
            # 处理试听音频（如果有）
            trial_audio_path = ""
            trial_audio = resp_data.get("trial_audio")
            if trial_audio:
                print(f"🎵 检测到试听音频")
                
                # 创建输出目录
                output_dir = folder_paths.get_output_directory()
                os.makedirs(output_dir, exist_ok=True)
                
                # 生成时间戳
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                
                try:
                    # 根据官方文档，trial_audio是hex编码的音频数据
                    if trial_audio.startswith("http"):
                        # 如果是URL，下载文件
                        print(f"📥 下载试听音频: {trial_audio}")
                        audio_response = requests.get(trial_audio)
                        audio_response.raise_for_status()
                        audio_data = audio_response.content
                    else:
                        # hex编码的音频数据，需要解码
                        print(f"🔓 解码hex编码的音频数据")
                        try:
                            audio_data = bytes.fromhex(trial_audio)
                        except ValueError as hex_error:
                            print(f"⚠️ hex解码失败，尝试base64解码: {hex_error}")
                            # 兼容性处理：如果hex解码失败，尝试base64
                            import base64
                            audio_data = base64.b64decode(trial_audio)
                    
                    # 检测音频格式
                    audio_format = self._detect_audio_format(audio_data)
                    print(f"🎼 检测到音频格式: {audio_format}")
                    
                    # 根据检测到的格式设置文件扩展名
                    trial_filename = f"voice_design_trial_{final_voice_id}_{timestamp}.{audio_format}"
                    trial_filepath = os.path.join(output_dir, trial_filename)
                    
                    # 保存音频文件
                    with open(trial_filepath, "wb") as f:
                        f.write(audio_data)
                    
                    trial_audio_path = os.path.abspath(trial_filepath)
                    print(f"💾 试听音频保存至: {trial_audio_path}")
                    
                except Exception as audio_error:
                    print(f"⚠️ 保存试听音频时出错: {str(audio_error)}")
                    # 不要因为试听音频保存失败而中断整个流程
            
            return (final_voice_id, trial_audio_path)

        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求错误: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"HTTP状态码: {e.response.status_code}")
                try:
                    error_data = e.response.json()
                    print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"错误响应内容: {e.response.content}")
            raise RuntimeError(f"调用MiniMax API失败: {str(e)}")
        except Exception as e:
            print(f"❌ 未预期的错误: {str(e)}")
            raise RuntimeError(f"音色设计失败: {str(e)}") 