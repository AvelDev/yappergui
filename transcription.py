import yt_dlp
import os
import requests
import json
from faster_whisper import WhisperModel
from utils import create_temp_audio_file, cleanup_temp_file

class TranscriptionManager:
    def __init__(self, models_dir, settings):
        self.models_dir = models_dir
        self.settings = settings
        self.whisper_model = None
        self.lang_detect_model = None
        self.temp_audio_file = None
        
    def load_models(self, progress_callback=None):
        try:
            if progress_callback:
                progress_callback("Loading models...", 0)
            
            # Load tiny model for language detection first
            if not self.lang_detect_model:
                if progress_callback:
                    progress_callback("Loading language detection model...", 10)
                self.lang_detect_model = WhisperModel(
                    "tiny",
                    device=self.settings["device"],
                    compute_type="int8",
                    download_root=self.models_dir
                )
            
            # Check if main model exists locally
            model_path = os.path.join(self.models_dir, self.settings['model'])
            if not os.path.exists(model_path) and progress_callback:
                progress_callback(f"Downloading {self.settings['model']} model... This might take a while.", 20)
            
            # Load main model for transcription
            if not self.whisper_model:
                self.whisper_model = WhisperModel(
                    self.settings["model"],
                    device=self.settings["device"],
                    compute_type="int8",
                    download_root=self.models_dir
                )
            
            if progress_callback:
                progress_callback(
                    f"Models loaded successfully (Device: {self.settings['device'].upper()})",
                    100
                )
                
        except Exception as e:
            print(f"Error loading whisper model: {str(e)}")
            if progress_callback:
                progress_callback(f"Error loading model: {str(e)}", 0)
            raise

    def download_audio(self, url, ffmpeg_path, progress_callback=None):
        temp_file = create_temp_audio_file()
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'progress_hooks': [progress_callback] if progress_callback else None,
            'ffmpeg_location': ffmpeg_path,
            'outtmpl': temp_file
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        self.temp_audio_file = temp_file + '.wav'
        
        if not os.path.exists(self.temp_audio_file):
            raise FileNotFoundError(f"Downloaded audio file not found at {self.temp_audio_file}")
            
        return self.temp_audio_file

    def send_to_ollama(self, text):
        prompt = f"""
                    Your output should use the following template:
                    ### Summary
                    ### Analogy
                    ### Notes
                    - [Emoji] Bulletpoint
                    ### Keywords
                    - Explanation
                    You have been tasked with creating a concise summary of a YouTube video using its transcription.
                    Make a summary of the transcript.
                    Additionally make a short complex analogy to give context and/or analogy from day-to-day life from the transcript.
                    Create 10 bullet points (each with an appropriate emoji) that summarize the key points or important moments from the video's transcription.
                    In addition to the bullet points, extract the most important keywords and any complex words not known to the average reader as
                    well as any acronyms mentioned. For each keyword and complex word, provide an explanation and definition based on its occurrence in the transcription.
                    Please ensure that the summary, bullet points, and explanations fit within the 330-word limit, while still offering a comprehensive and clear understanding of the video's content.
                    Use the text above: {text}.
                    """
                    
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "mistral:latest",
                    "prompt": prompt,
                    # "prompt": f"Stresć mi ten tekst: {text}"
                },
                stream=True
            )
            
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        json_response = json.loads(line)
                        if 'response' in json_response:
                            full_response += json_response['response']
                return full_response
            return None
        except Exception as e:
            print(f"Error sending to Ollama: {str(e)}")
            return None

    def transcribe(self, progress_callback=None):
        try:
            if not self.whisper_model or not self.lang_detect_model:
                self.load_models(progress_callback)
            
            if progress_callback:
                progress_callback("Detecting language... This will be quick...", 50)
            
            # First detect language using tiny model
            segments, info = self.lang_detect_model.transcribe(
                self.temp_audio_file,
                beam_size=1,
                language=None,
                condition_on_previous_text=False,
                vad_filter=True
            )
            
            detected_language = info.language
            if progress_callback:
                progress_callback(f"Detected language: {detected_language}. Starting transcription...", 60)
            
            # Now transcribe with the main model using the detected language
            segments, info = self.whisper_model.transcribe(
                self.temp_audio_file,
                beam_size=5,
                language=detected_language,
                condition_on_previous_text=True,
                vad_filter=True
            )
            
            # Process segments
            segments_list = list(segments)
            total_segments = len(segments_list)
            processed_text = []
            
            for i, segment in enumerate(segments_list):
                if progress_callback:
                    progress = 70 + (i / total_segments) * 20
                    progress_callback(f"Processing segment {i+1}/{total_segments}...", progress)
                
                # Format text based on settings
                if self.settings.get("show_timestamps", True):
                    processed_text.append(f"[{segment.start:.1f}s -> {segment.end:.1f}s] {segment.text}")
                else:
                    processed_text.append(segment.text)
            
            # Combine results
            if progress_callback:
                progress_callback("Finalizing transcription...", 90)
            
            final_text = "\n".join(processed_text) if self.settings.get("show_timestamps", True) else " ".join(processed_text)
            
            # Send to Ollama for summarization
            if progress_callback:
                progress_callback("Sending to Ollama for summarization...", 95)
            summary = self.send_to_ollama(final_text)
            
            return final_text, summary
            
        finally:
            cleanup_temp_file(self.temp_audio_file)
            self.temp_audio_file = None
