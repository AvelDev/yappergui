import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import messagebox
import yt_dlp
import os
import tempfile
from faster_whisper import WhisperModel
import threading
import json
import torch  # Do sprawdzania dostępności CUDA
import shutil  # Do sprawdzania ffmpeg w PATH

def find_ffmpeg():
    """Find ffmpeg executable in system PATH"""
    return shutil.which('ffmpeg')

class SettingsWindow:
    def __init__(self, parent, settings, on_settings_change):
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("400x500")  # Increased height for new option
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
            messagebox.showinfo("Success", f"FFmpeg found at: {ffmpeg_path}")
        else:
            messagebox.showerror("Error", "FFmpeg not found in system PATH")

    def save_settings(self):
        self.settings["model"] = self.model_var.get()
        self.settings["device"] = self.device_var.get()
        self.settings["ffmpeg_path"] = self.ffmpeg_path_var.get()
        self.settings["show_timestamps"] = self.show_timestamps_var.get()
        self.on_settings_change(self.settings)
        self.window.destroy()

class URLProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("URL Processor")
        self.root.geometry("600x400")
        self.temp_audio_file = None
        self.whisper_model = None
        self.lang_detect_model = None  # Model for quick language detection
        
        # Create models directory if it doesn't exist
        self.models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Load settings
        self.settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        self.settings = self.load_settings()

        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # URL Entry
        ttk.Label(main_frame, text="Enter URL:").grid(row=0, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(main_frame, width=50)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)

        # Process Button
        self.process_button = ttk.Button(main_frame, text="Process URL", command=self.process_url)
        self.process_button.grid(row=0, column=2, padx=5, pady=5)

        # Result Text Area
        ttk.Label(main_frame, text="Result:").grid(row=1, column=0, sticky=tk.W)
        self.result_text = tk.Text(main_frame, height=10, width=60)
        self.result_text.grid(row=2, column=0, columnspan=3, padx=5, pady=5)

        # Progress Frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Progress Label
        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack(side=tk.TOP, fill=tk.X)
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(side=tk.TOP, fill=tk.X, padx=5)

        # Save Button
        self.save_button = ttk.Button(main_frame, text="Save to File", command=self.save_to_file)
        self.save_button.grid(row=4, column=0, columnspan=3, pady=10)

        # Create menu
        self.create_menu()
        
        # Initialize whisper model
        self.load_model()

        # Check for FFmpeg at startup
        if not self.settings.get("ffmpeg_path"):
            ffmpeg_path = find_ffmpeg()
            if ffmpeg_path:
                self.settings["ffmpeg_path"] = ffmpeg_path
                self.save_settings()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Model Settings", command=self.open_settings)
        
    def open_settings(self):
        SettingsWindow(self.root, self.settings, self.change_settings)

    def load_settings(self):
        default_settings = {
            "model": "base",
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "ffmpeg_path": "",
            "show_timestamps": True  # Default value for timestamp display
        }
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    # Update with any missing default settings
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
                    return settings
            return default_settings
        except Exception as e:
            print(f"Error loading settings: {e}")
            return default_settings

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f)

    def change_settings(self, new_settings):
        self.settings.update(new_settings)
        self.save_settings()
        self.load_model()

    def load_model(self):
        try:
            self.update_progress("Loading models...", 0)
            
            # Load tiny model for language detection first
            if not self.lang_detect_model:
                self.update_progress("Loading language detection model...", 10)
                self.lang_detect_model = WhisperModel(
                    "tiny",
                    device=self.settings["device"],
                    compute_type="int8",  # Using int8 for faster language detection
                    download_root=self.models_dir
                )
            
            # Check if main model exists locally
            model_path = os.path.join(self.models_dir, self.settings['model'])
            if not os.path.exists(model_path):
                self.update_progress(f"Downloading {self.settings['model']} model... This might take a while.", 20)
            
            # Load main model for transcription
            if not self.whisper_model:
                self.whisper_model = WhisperModel(
                    self.settings["model"],
                    device=self.settings["device"],
                    compute_type="int8",  # Using int8 for better performance
                    download_root=self.models_dir
                )
            
            self.update_progress(
                f"Models loaded successfully (Device: {self.settings['device'].upper()})",
                100
            )
        except Exception as e:
            print(f"Error loading whisper model: {str(e)}")
            self.update_progress(f"Error loading model: {str(e)}", 0)

    def update_progress(self, message, progress=None):
        """Update progress bar and label"""
        self.progress_label.config(text=message)
        if progress is not None:
            self.progress_var.set(progress)
        self.root.update()

    def download_progress_hook(self, d):
        """Progress hook for yt-dlp"""
        if d['status'] == 'downloading':
            # Calculate download progress
            total_bytes = d.get('total_bytes')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes:
                progress = (downloaded_bytes / total_bytes) * 50  # Use first 50% for download
                self.update_progress(f"Downloading audio... {progress:.1f}%", progress)
        elif d['status'] == 'finished':
            self.update_progress("Download completed. Starting transcription...", 50)

    def process_url(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return

        # Check if FFmpeg is available
        ffmpeg_path = self.settings.get("ffmpeg_path")
        if not ffmpeg_path or not os.path.exists(ffmpeg_path):
            ffmpeg_path = find_ffmpeg()
            if not ffmpeg_path:
                messagebox.showerror("Error", "FFmpeg not found. Please set FFmpeg path in settings.")
                return
            self.settings["ffmpeg_path"] = ffmpeg_path
            self.save_settings()

        self.process_button.config(state='disabled')
        self.save_button.config(state='disabled')
        self.result_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        
        try:
            # Create a temporary directory for the audio file
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, 'audio')
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }],
                'progress_hooks': [self.download_progress_hook],
                'ffmpeg_location': ffmpeg_path,
                'outtmpl': temp_file
            }
            
            # Download audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Store the path to the temporary file (with wav extension)
            self.temp_audio_file = temp_file + '.wav'
            
            # Verify the file exists
            if not os.path.exists(self.temp_audio_file):
                raise FileNotFoundError(f"Downloaded audio file not found at {self.temp_audio_file}")
            
            # Start transcription in a separate thread
            threading.Thread(target=self.transcribe_audio, daemon=True).start()
            
        except Exception as e:
            self.show_transcription_error(str(e))
            self.cleanup_temp_file()
            self.process_button.config(state='normal')
            self.save_button.config(state='normal')

    def transcribe_audio(self):
        try:
            if not self.whisper_model or not self.lang_detect_model:
                self.load_model()
            
            self.update_progress("Detecting language... This will be quick...", 50)
            
            # First detect language using tiny model
            segments, info = self.lang_detect_model.transcribe(
                self.temp_audio_file,
                beam_size=1,
                language=None,
                condition_on_previous_text=False,
                vad_filter=True
            )
            
            detected_language = info.language
            self.update_progress(f"Detected language: {detected_language}. Starting transcription...", 60)
            
            # Now transcribe with the main model using the detected language
            segments, info = self.whisper_model.transcribe(
                self.temp_audio_file,
                beam_size=5,
                language=detected_language,
                condition_on_previous_text=True,
                vad_filter=True
            )
            
            # Process segments
            segments_list = list(segments)
            total_segments = len(segments_list)
            processed_text = []
            
            for i, segment in enumerate(segments_list):
                progress = 70 + (i / total_segments) * 20
                self.update_progress(f"Processing segment {i+1}/{total_segments}...", progress)
                
                # Format text based on settings
                if self.settings.get("show_timestamps", True):
                    processed_text.append(f"[{segment.start:.1f}s -> {segment.end:.1f}s] {segment.text}")
                else:
                    processed_text.append(segment.text)
            
            # Combine results
            self.update_progress("Finalizing transcription...", 90)
            text = "\n".join(processed_text) if self.settings.get("show_timestamps", True) else " ".join(processed_text)
            
            # Update GUI in the main thread
            self.root.after(0, self.update_transcription_result, text)
            
        except Exception as e:
            self.root.after(0, self.show_transcription_error, str(e))
        finally:
            self.root.after(0, self.cleanup_after_transcription)

    def update_transcription_result(self, text):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
        self.update_progress("Transcription completed!", 100)
        self.process_button.config(state='normal')
        self.save_button.config(state='normal')

    def show_transcription_error(self, error_message):
        messagebox.showerror("Transcription Error", f"Failed to transcribe audio: {error_message}")
        self.update_progress("", 0)
        self.process_button.config(state='normal')
        self.save_button.config(state='normal')

    def cleanup_after_transcription(self):
        self.process_button.config(state='normal')
        self.save_button.config(state='normal')

    def save_to_file(self):
        result = self.result_text.get(1.0, tk.END).strip()
        if result:
            try:
                # Ask user where to save the file
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
                )
                
                if save_path:
                    with open(save_path, 'w', encoding='utf-8') as file:
                        file.write(result)
                    messagebox.showinfo("Success", "Transcription saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
            finally:
                self.cleanup_temp_file()
        else:
            messagebox.showwarning("Warning", "No transcription to save")

    def cleanup_temp_file(self):
        # Clean up temporary file and directory
        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            try:
                os.remove(self.temp_audio_file)
                os.rmdir(os.path.dirname(self.temp_audio_file))
                self.temp_audio_file = None
            except Exception as e:
                print(f"Error cleaning up temporary files: {str(e)}")

    def __del__(self):
        # Ensure cleanup when the application closes
        self.cleanup_temp_file()

def main():
    root = tk.Tk()
    app = URLProcessorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()