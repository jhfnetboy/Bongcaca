# VoiceTyper Deployment Guide

## Environment Setup

### Prerequisites
- macOS with Homebrew installed
- Miniconda/Anaconda

### Initialize Environment

1. **Install Conda (if not already installed)**
```bash
brew install --cask miniconda
conda init zsh
source ~/.zshrc
```

2. **Create Virtual Environment**
```bash
conda create -n voice_typer python=3.11 -y
```

3. **Activate Environment**
```bash
conda activate voice_typer
```

4. **Install Dependencies**
```bash
pip install -r requirements.txt
```

## Running the Application

### Quick Start
```bash
# Activate environment and run
conda activate voice_typer && python main.py
```

### Using Environment Script
```bash
# Make script executable (one time only)
chmod +x python-env.sh

# Run application
./python-env.sh && python main.py
```

## Build and Test

### Dependencies
All dependencies are listed in `requirements.txt`:
- faster-whisper==1.1.1 (core transcription engine)
- PySide6==6.6.1 (GUI framework)
- pyaudio==0.2.14 (audio recording)
- torch==2.2.1, torchaudio==2.2.1 (ML framework)
- numpy==1.26.4 (numerical computing)
- pyautogui==0.9.54 (GUI automation)
- Additional utility packages

### Verification
Run the following to verify installation:
```bash
conda activate voice_typer
python -c "import faster_whisper; print('Dependencies OK')"
python main.py  # Should start the application GUI
```

## Troubleshooting

### Common Issues

1. **Environment not found**
   - Run: `conda info --envs` to list environments
   - Recreate if missing: `conda create -n voice_typer python=3.11 -y`

2. **Missing dependencies**
   - Reinstall: `pip install -r requirements.txt`

3. **Audio device issues**
   - Check audio settings in macOS System Preferences
   - Ensure microphone permissions are granted 