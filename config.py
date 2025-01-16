"""
Configuration Management Module

This module provides centralized configuration management for the YapperGUI application.
It handles loading, saving, and updating application settings, providing a single source
of truth for all configuration-related operations.

The Config class is implemented as a singleton to ensure consistent settings across
the application. It manages settings such as:
- Whisper model selection
- Processing device (CPU/CUDA)
- FFmpeg path
- Timestamp display preferences

Example:
    >>> from config import config
    >>> print(config.settings)
    {'model': 'base', 'device': 'cuda', 'ffmpeg_path': '/usr/local/bin/ffmpeg'}
    >>> config.update_settings({'model': 'large'})
    >>> config.save_settings()
"""

import os
import json
import torch

class Config:
    DEFAULT_SETTINGS = {
        "model": "base",
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "ffmpeg_path": "",
        "show_timestamps": True
    }

    def __init__(self):
        """Initialize Config with default settings and paths."""
        self.settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        self.models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
        self.settings = self.load_settings()

    def load_settings(self):
        """
        Load settings from the JSON file, falling back to defaults if necessary.
        
        Returns:
            dict: The loaded settings, with any missing values filled in from defaults
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    # Update with any missing default settings
                    return {**self.DEFAULT_SETTINGS, **settings}
            return self.DEFAULT_SETTINGS.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.DEFAULT_SETTINGS.copy()

    def save_settings(self, settings):
        """
        Save settings to the JSON file.
        
        Args:
            settings (dict): The settings to save
        """
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f)

    def update_settings(self, new_settings):
        """
        Update current settings with new values and save to file.
        
        Args:
            new_settings (dict): New settings to update
        """
        self.settings.update(new_settings)
        self.save_settings(self.settings)

config = Config()
