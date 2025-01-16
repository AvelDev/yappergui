# YapperGUI Installation Guide

This guide provides detailed instructions for installing YapperGUI and its dependencies on different operating systems.

## Prerequisites

### System Requirements
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- GPU with CUDA support (optional, for faster processing)
- 2GB free disk space for models

### Required Software
- FFmpeg
- Python virtual environment (recommended)
- Git
- Ollama

## Installation Steps

### 1. Install FFmpeg

#### macOS
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Windows
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract to a directory
3. Add to system PATH

### 2. Install Ollama

#### macOS/Linux
```bash
curl https://ollama.ai/install.sh | sh
```

#### Windows
Download from https://ollama.ai/download

### 3. Install YapperGUI

1. Clone the repository:
```bash
git clone https://github.com/yourusername/yappergui.git
cd yappergui
```

2. Create and activate virtual environment:
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Pull required Ollama model:
```bash
ollama pull mistral
```

## Verify Installation

1. Run the application:
```bash
python main.py
```

2. Check settings:
- Open Settings menu
- Verify FFmpeg path
- Check GPU/CUDA availability

## Troubleshooting

### Common Issues

1. FFmpeg not found
- Verify FFmpeg installation
- Check system PATH
- Set path manually in settings

2. CUDA/GPU Issues
- Update GPU drivers
- Install CUDA toolkit
- Check torch GPU support

3. Ollama Connection Error
- Verify Ollama is running
- Check port 11434 is available
- Restart Ollama service

### Getting Help

- Check the logs in the `logs` directory
- Open an issue on GitHub
- Check existing issues for solutions

## Updating

1. Pull latest changes:
```bash
git pull origin main
```

2. Update dependencies:
```bash
pip install -r requirements.txt --upgrade
```

## Uninstallation

1. Remove virtual environment:
```bash
deactivate  # if active
rm -rf venv
```

2. Delete application directory:
```bash
cd ..
rm -rf yappergui
```

3. (Optional) Remove Ollama:
```bash
# macOS/Linux
sudo rm -rf /usr/local/bin/ollama
```
