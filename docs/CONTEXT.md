Collection of helper functions for:

- FFmpeg detection and path management
- Temporary file creation and cleanup
- System path operations

## Data Flow

1. User Input:

   - GUI: User enters YouTube URL and clicks "Process"
   - API: Client sends POST request to /transcribe endpoint

2. Audio Processing:

   - URL validation
   - Audio download using yt-dlp
   - Conversion to WAV format using FFmpeg

3. Transcription:

   - Language detection using tiny Whisper model
   - Full transcription using selected Whisper model
   - Progress tracking and updates

4. Summarization:

   - Send transcription to Ollama
   - Generate structured summary
   - Format results

5. Output:
   - GUI: Display in text areas and save to file option
   - API: Return JSON response

## Error Handling

The application implements comprehensive error handling:

- Custom exceptions for each component
- User-friendly error messages in GUI
- Proper HTTP error responses in API
- Detailed logging for debugging
- Cleanup of temporary files in error cases

## Configuration

Settings are managed through:

- GUI settings window
- JSON configuration file
- Command-line arguments for API mode
- Environment variable fallbacks

## Dependencies

Key external dependencies:

- faster-whisper: For transcription
- yt-dlp: For YouTube video download
- FFmpeg: For audio processing
- Ollama: For summarization
- Flask: For API server
- tkinter: For GUI interface
