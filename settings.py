import tkinter as tk
from tkinter import ttk, filedialog
import torch
from utils import find_ffmpeg
from config import config

class SettingsWindow:
    def __init__(self, parent, settings, on_settings_change):
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("400x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.models = ["tiny", "base", "small", "medium", "large", "large-v2"]
        self.settings = settings.copy()
        self.on_settings_change = on_settings_change
        
        # Create main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        current_row = 0
        
        # Model selection
        ttk.Label(main_frame, text="Select Whisper Model:").grid(row=current_row, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value=settings["model"])
        model_combo = ttk.Combobox(main_frame, textvariable=self.model_var, values=self.models, state="readonly")
        model_combo.grid(row=current_row, column=1, sticky=(tk.W, tk.E), pady=5)
        current_row += 1

        # FFmpeg path
        ttk.Label(main_frame, text="FFmpeg Path:").grid(row=current_row, column=0, sticky=tk.W, pady=5)
        self.ffmpeg_path_var = tk.StringVar(value=settings.get("ffmpeg_path", ""))
        ffmpeg_entry = ttk.Entry(main_frame, textvariable=self.ffmpeg_path_var, width=30)
        ffmpeg_entry.grid(row=current_row, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Browse button for FFmpeg
        browse_btn = ttk.Button(main_frame, text="Browse", command=self.browse_ffmpeg)
        browse_btn.grid(row=current_row, column=2, padx=5, pady=5)
        current_row += 1
        
        # Auto-detect button for FFmpeg
        detect_btn = ttk.Button(main_frame, text="Auto-detect", command=self.detect_ffmpeg)
        detect_btn.grid(row=current_row, column=1, pady=5)
        current_row += 1

        # Device selection
        ttk.Label(main_frame, text="Select Device:").grid(row=current_row, column=0, sticky=tk.W, pady=5)
        self.device_var = tk.StringVar(value=settings["device"])
        devices = ["cpu"]
        if torch.cuda.is_available():
            devices.append("cuda")
        device_combo = ttk.Combobox(main_frame, textvariable=self.device_var, values=devices, state="readonly")
        device_combo.grid(row=current_row, column=1, sticky=(tk.W, tk.E), pady=5)
        current_row += 1

        # Timestamp option
        ttk.Label(main_frame, text="Show Timestamps:").grid(row=current_row, column=0, sticky=tk.W, pady=5)
        self.show_timestamps_var = tk.BooleanVar(value=settings.get("show_timestamps", True))
        timestamp_check = ttk.Checkbutton(main_frame, variable=self.show_timestamps_var)
        timestamp_check.grid(row=current_row, column=1, sticky=tk.W, pady=5)
        current_row += 1

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=current_row, column=0, columnspan=3, pady=20)

        # Save and Cancel buttons
        save_button = ttk.Button(button_frame, text="Save", command=self.save_settings)
        save_button.pack(side=tk.LEFT, padx=5)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.window.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

    def browse_ffmpeg(self):
        filename = filedialog.askopenfilename(
            title="Select FFmpeg executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if filename:
            self.ffmpeg_path_var.set(filename)

    def detect_ffmpeg(self):
        ffmpeg_path = find_ffmpeg()
        if ffmpeg_path:
            self.ffmpeg_path_var.set(ffmpeg_path)
            tk.messagebox.showinfo("Success", f"FFmpeg found at: {ffmpeg_path}")
        else:
            tk.messagebox.showerror("Error", "FFmpeg not found in system PATH")

    def save_settings(self):
        self.settings["model"] = self.model_var.get()
        self.settings["device"] = self.device_var.get()
        self.settings["ffmpeg_path"] = self.ffmpeg_path_var.get()
        self.settings["show_timestamps"] = self.show_timestamps_var.get()
        self.on_settings_change(self.settings)
