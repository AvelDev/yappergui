from flask import Flask, request, jsonify
from flask_cors import CORS
from transcription import TranscriptionManager
from audio_processor import AudioProcessor
from config import config
from logger import logger
import os

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize managers
transcription_manager = TranscriptionManager(config.models_dir, config.settings)
audio_processor = AudioProcessor(config.settings.get("ffmpeg_path"))

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        # Log incoming request
        logger.info(f"Received request: {request.data}")
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        logger.info(f"Processed request data: {data}")
        
        if not data or 'url' not in data:
            error_msg = "Missing 'url' parameter in request"
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400

        url = data['url']
        logger.info(f"Processing URL: {url}")

        # Download audio
        audio_file = audio_processor.download_audio(url)
        logger.info(f"Audio downloaded to: {audio_file}")
        
        # Set the audio file in transcription manager
        transcription_manager.temp_audio_file = audio_file
        
        # Perform transcription
        transcription, summary = transcription_manager.transcribe()
        
        response = {
            'status': 'success',
            'transcription': transcription,
            'summary': summary
        }
        
        logger.info("Transcription completed successfully")
        return jsonify(response)

    except Exception as e:
        error_msg = f"Error during transcription: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({'status': 'error', 'error': error_msg}), 500

    finally:
        if hasattr(transcription_manager, 'temp_audio_file') and transcription_manager.temp_audio_file:
            audio_processor.cleanup(transcription_manager.temp_audio_file)
            logger.info("Temporary files cleaned up")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

def start_api(host='0.0.0.0', port=5000):
    logger.info(f"Starting API server on {host}:{port}")
    app.run(host=host, port=port, debug=True) 