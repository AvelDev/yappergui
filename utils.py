"""
Utility Functions Module

This module provides utility functions used across the YapperGUI application.
It includes functions for file system operations, FFmpeg detection, and
temporary file management.

Functions:
    find_ffmpeg(): Locate FFmpeg executable in system PATH
    create_temp_audio_file(): Create temporary file for audio processing
    cleanup_temp_file(temp_file): Clean up temporary files and directories

Example:
    >>> from utils import find_ffmpeg, create_temp_audio_file
    >>> ffmpeg_path = find_ffmpeg()
    >>> if ffmpeg_path:
    ...     print(f"FFmpeg found at: {ffmpeg_path}")
    >>> temp_file = create_temp_audio_file()
    >>> print(f"Created temporary file: {temp_file}")
"""

import shutil
import os
import tempfile
from logger import logger

def find_ffmpeg() -> str:
    """
    Find ffmpeg executable in system PATH.
    
    Returns:
        str: Path to ffmpeg executable, or empty string if not found
    """
    logger.debug("Searching for FFmpeg in system PATH")
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        logger.info("FFmpeg found at: %s", ffmpeg_path)
    else:
        logger.warning("FFmpeg not found in system PATH")
    return ffmpeg_path or ""

def create_temp_audio_file() -> str:
    """
    Create a temporary directory and return path for audio file.
    
    Returns:
        str: Path to temporary file
    
    Note:
        The caller is responsible for cleaning up the temporary directory
        using cleanup_temp_file()
    """
    temp_dir = tempfile.mkdtemp()
    logger.debug("Created temporary directory: %s", temp_dir)
    return os.path.join(temp_dir, 'audio')

def cleanup_temp_file(temp_audio_file: str) -> None:
    """
    Clean up temporary file and its parent directory.
    
    Args:
        temp_audio_file: Path to temporary file to clean up
    """
    if temp_audio_file and os.path.exists(temp_audio_file):
        try:
            os.remove(temp_audio_file)
            os.rmdir(os.path.dirname(temp_audio_file))
            logger.debug("Cleaned up temporary file and directory: %s", temp_audio_file)
        except Exception as e:
            logger.error("Error cleaning up temporary files: %s", str(e), exc_info=True)
