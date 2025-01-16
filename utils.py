import shutil
import os
import tempfile

def find_ffmpeg():
    """Find ffmpeg executable in system PATH"""
    return shutil.which('ffmpeg')

def create_temp_audio_file():
    """Create a temporary directory and return path for audio file"""
    temp_dir = tempfile.mkdtemp()
    return os.path.join(temp_dir, 'audio')

def cleanup_temp_file(temp_audio_file):
    """Clean up temporary file and directory"""
    if temp_audio_file and os.path.exists(temp_audio_file):
        try:
            os.remove(temp_audio_file)
            os.rmdir(os.path.dirname(temp_audio_file))
        except Exception as e:
            print(f"Error cleaning up temporary files: {str(e)}")
