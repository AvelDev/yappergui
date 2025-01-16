# YapperGUI API Documentation

This document describes the internal API of YapperGUI's main components.

## Modules Overview

### 1. Config Module (`config.py`)

The configuration management system.

```python
from config import config

# Get current settings
settings = config.settings

# Update settings
config.update_settings({
    "model": "large",
    "device": "cuda"
})
```

#### Key Classes
- `Config`: Singleton configuration manager

#### Key Methods
- `load_settings()`: Load settings from file
- `save_settings(settings)`: Save settings to file
- `update_settings(new_settings)`: Update and save settings

### 2. Audio Processor (`audio_processor.py`)

Handles YouTube video download and audio extraction.

```python
from audio_processor import AudioProcessor

processor = AudioProcessor(ffmpeg_path="/usr/local/bin/ffmpeg")
audio_file = processor.download_audio("https://youtube.com/watch?v=...")
```

#### Key Classes
- `AudioProcessor`: Main audio processing class
- `AudioProcessingError`: Base exception class
- `AudioDownloadError`: Download-specific exception

#### Key Methods
- `download_audio(url, progress_hook)`: Download and extract audio
- `cleanup(audio_file)`: Clean up temporary files

### 3. Transcription Manager (`transcription.py`)

Manages audio transcription and summarization.

```python
from transcription import TranscriptionManager

manager = TranscriptionManager(models_dir="./models", settings={...})
transcription, summary = manager.transcribe(progress_callback)
```

#### Key Classes
- `TranscriptionManager`: Main transcription class
- `TranscriptionError`: Base exception class
- `ModelLoadError`: Model loading exception

#### Key Methods
- `load_models(progress_callback)`: Load Whisper models
- `transcribe(progress_callback)`: Transcribe audio and generate summary
- `send_to_ollama(text)`: Send text to Ollama for summarization

### 4. Logger (`logger.py`)

Logging system for the application.

```python
from logger import logger

logger.info("Operation successful")
logger.error("An error occurred", exc_info=True)
```

#### Key Classes
- `Logger`: Singleton logger class

#### Methods
- `get_logger()`: Get logger instance
- Standard logging methods: debug, info, warning, error, critical

### 5. Utils (`utils.py`)

Utility functions used across the application.

```python
from utils import find_ffmpeg, create_temp_audio_file

ffmpeg_path = find_ffmpeg()
temp_file = create_temp_audio_file()
```

#### Key Functions
- `find_ffmpeg()`: Locate FFmpeg executable
- `create_temp_audio_file()`: Create temporary file
- `cleanup_temp_file(temp_file)`: Clean up temporary files

### 6. GUI (`gui.py`)

Main application GUI implementation.

```python
from gui import URLProcessorApp
import tkinter as tk

root = tk.Tk()
app = URLProcessorApp(root)
root.mainloop()
```

#### Key Classes
- `URLProcessorApp`: Main application window

#### Key Methods
- `process_url()`: Process YouTube URL
- `update_progress(message, progress)`: Update progress display
- `save_to_file()`: Save results to file

## Error Handling

All modules use custom exception classes:

```python
try:
    # Operation
except AudioProcessingError as e:
    logger.error("Audio processing failed", exc_info=True)
except TranscriptionError as e:
    logger.error("Transcription failed", exc_info=True)
```

## Threading Model

The application uses threading for long-running operations:

```python
threading.Thread(
    target=self.process_url_thread,
    args=(url,),
    daemon=True
).start()
```

## Progress Callbacks

Progress updates use callback functions:

```python
def update_progress(message: str, progress: Optional[float] = None):
    """Update progress display
    
    Args:
        message: Status message
        progress: Progress percentage (0-100)
    """
    pass
```

## Configuration Schema

```json
{
    "model": "base",
    "device": "cuda",
    "ffmpeg_path": "/usr/local/bin/ffmpeg",
    "show_timestamps": true
}
```
