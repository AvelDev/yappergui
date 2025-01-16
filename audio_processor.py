import yt_dlp
from utils import create_temp_audio_file, cleanup_temp_file
from logger import logger
from typing import Optional, Callable

class AudioProcessingError(Exception):
    """Base exception for audio processing errors"""
    pass

class AudioDownloadError(AudioProcessingError):
    """Exception raised when audio download fails"""
    pass

class AudioProcessor:
    def __init__(self, ffmpeg_path: str):
        self.ffmpeg_path = ffmpeg_path
        logger.info("AudioProcessor initialized with ffmpeg_path: %s", ffmpeg_path)
        
    def download_audio(self, url: str, progress_hook: Optional[Callable] = None) -> str:
        """Download audio from URL using yt-dlp
        
        Args:
            url: YouTube URL to download from
            progress_hook: Optional callback for download progress
            
        Returns:
            str: Path to downloaded audio file
            
        Raises:
            AudioDownloadError: If download fails
        """
        temp_audio_file = create_temp_audio_file()
        logger.info("Created temporary audio file: %s", temp_audio_file)
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'ffmpeg_location': self.ffmpeg_path,
            'outtmpl': temp_audio_file,
            'progress_hooks': [progress_hook] if progress_hook else None,
        }
        
        try:
            logger.info("Starting audio download from URL: %s", url)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            output_file = f"{temp_audio_file}.wav"
            logger.info("Audio download completed: %s", output_file)
            return output_file
            
        except Exception as e:
            error_msg = f"Error downloading audio: {str(e)}"
            logger.error(error_msg, exc_info=True)
            cleanup_temp_file(temp_audio_file)
            raise AudioDownloadError(error_msg) from e
            
    def cleanup(self, audio_file: str) -> None:
        """Clean up downloaded audio file
        
        Args:
            audio_file: Path to audio file to clean up
        """
        logger.info("Cleaning up audio file: %s", audio_file)
        cleanup_temp_file(audio_file)
