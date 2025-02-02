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
    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg_path = ffmpeg_path
        logger.info(f"AudioProcessor initialized with ffmpeg_path: {ffmpeg_path}")
        
    def download_audio(self, url: str, progress_hook: Optional[Callable] = None) -> str:
        """
        Download audio from URL and save to temporary file
        
        Args:
            url: URL to download from
            progress_hook: Optional callback function to report download progress
            
        Returns:
            str: Path to downloaded audio file
            
        Raises:
            AudioDownloadError: If download fails or receives empty response
        """
        temp_file = create_temp_audio_file()
        logger.info(f"Created temporary audio file: {temp_file}")
        logger.info(f"Starting audio download from URL: {url}")

        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }],
                'outtmpl': temp_file,
                'quiet': True,
                'no_warnings': True,
                'extract_audio': True,
                'socket_timeout': 30,
                'retries': 3,
            }

            if self.ffmpeg_path:
                ydl_opts['ffmpeg_location'] = self.ffmpeg_path
            
            if progress_hook:
                ydl_opts['progress_hooks'] = [progress_hook]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    error_code = ydl.download([url])
                    if error_code != 0:
                        raise AudioDownloadError(f"yt-dlp returned error code: {error_code}")
                except yt_dlp.utils.DownloadError as e:
                    if "Empty reply from server" in str(e):
                        raise AudioDownloadError("Otrzymano pustą odpowiedź z serwera. Spróbuj ponownie później.") from e
                    raise AudioDownloadError(f"Błąd podczas pobierania: {str(e)}") from e

            # Add .wav extension as yt-dlp automatically adds it
            final_path = f"{temp_file}.wav"
            logger.info(f"Audio downloaded successfully to: {final_path}")
            return final_path

        except Exception as e:
            error_msg = f"Error downloading audio: {str(e)}"
            logger.error(error_msg, exc_info=True)
            cleanup_temp_file(temp_file)
            raise AudioDownloadError(error_msg) from e
            
    def cleanup(self, file_path: str):
        """Clean up temporary files"""
        cleanup_temp_file(file_path)
