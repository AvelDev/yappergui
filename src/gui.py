import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import threading
import time
from settings import SettingsWindow
from utils import find_ffmpeg
from transcription import TranscriptionManager
from audio_processor import AudioProcessor
from config import config

class URLProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("URL Processor")
        self.root.geometry("700x600")
        
        # Initialize variables
        self.transcription_start_time = None
        self.timer_id = None
        
        # Create models directory if it doesn't exist
        os.makedirs(config.models_dir, exist_ok=True)
        
        # Initialize managers
        self.transcription_manager = TranscriptionManager(config.models_dir, config.settings)
        self.audio_processor = AudioProcessor(config.settings.get("ffmpeg_path"))

        self.setup_gui()
        self.check_ffmpeg()
        self.load_model()

    def setup_gui(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # URL Entry
        ttk.Label(main_frame, text="Youtube URL:").grid(row=0, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(main_frame, width=50)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)

        # Process Button
        self.process_button = ttk.Button(main_frame, text="Podsumuj", command=self.process_url)
        self.process_button.grid(row=0, column=2, padx=5, pady=5)

        # Transcription Text Area
        ttk.Label(main_frame, text="Transkrypcja:").grid(row=1, column=0, sticky=tk.W)
        self.transcription_text = tk.Text(main_frame, height=10, width=60)
        self.transcription_text.grid(row=2, column=0, columnspan=3, padx=5, pady=5)

        # Summary Text Area
        ttk.Label(main_frame, text="Podsumowanie:").grid(row=3, column=0, sticky=tk.W)
        self.summary_text = tk.Text(main_frame, height=10, width=60)
        self.summary_text.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

        # Progress Frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Timer Label
        self.timer_label = ttk.Label(progress_frame, text="")
        self.timer_label.pack(side=tk.TOP, fill=tk.X)
        
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
        self.save_button = ttk.Button(main_frame, text="Zapisz do pliku", command=self.save_to_file)
        self.save_button.grid(row=6, column=0, columnspan=3, pady=10)

        # Create menu
        self.create_menu()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Model Settings", command=self.open_settings)

    def check_ffmpeg(self):
        if not config.settings.get("ffmpeg_path"):
            ffmpeg_path = find_ffmpeg()
            if ffmpeg_path:
                config.settings["ffmpeg_path"] = ffmpeg_path
                config.save_settings(config.settings)
                self.audio_processor = AudioProcessor(ffmpeg_path)

    def load_model(self):
        try:
            self.transcription_manager.load_models(self.update_progress)
        except Exception as e:
            print(f"Error loading whisper model: {str(e)}")
            self.update_progress(f"Error loading model: {str(e)}", 0)

    def open_settings(self):
        SettingsWindow(self.root, config.settings, self.change_settings)

    def change_settings(self, new_settings):
        config.update_settings(new_settings)
        self.transcription_manager.settings = config.settings
        self.audio_processor = AudioProcessor(config.settings.get("ffmpeg_path"))
        self.load_model()

    def update_timer(self):
        """Update the timer display"""
        if self.transcription_start_time:
            elapsed = time.time() - self.transcription_start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.timer_label.config(text=f"Czas transkrypcji: {minutes:02d}:{seconds:02d}")
            self.timer_id = self.root.after(1000, self.update_timer)

    def start_timer(self):
        """Start the transcription timer"""
        self.transcription_start_time = time.time()
        self.update_timer()

    def stop_timer(self):
        """Stop the transcription timer"""
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def update_progress(self, message, progress=None):
        """Update progress bar and label"""
        self.progress_label.config(text=message)
        if progress is not None:
            self.progress_var.set(progress)
        self.root.update()

    def process_url(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return

        # Check if FFmpeg is available
        if not config.settings.get("ffmpeg_path"):
            ffmpeg_path = find_ffmpeg()
            if not ffmpeg_path:
                messagebox.showerror("Error", "FFmpeg not found. Please set FFmpeg path in settings.")
                return
            config.settings["ffmpeg_path"] = ffmpeg_path
            config.save_settings(config.settings)
            self.audio_processor = AudioProcessor(ffmpeg_path)

        self.process_button.config(state='disabled')
        self.save_button.config(state='disabled')
        self.transcription_text.delete(1.0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        
        try:
            # Download audio in a separate thread
            threading.Thread(
                target=self.process_url_thread,
                args=(url,),
                daemon=True
            ).start()
            
        except Exception as e:
            self.show_transcription_error(str(e))
            self.process_button.config(state='normal')
            self.save_button.config(state='normal')

    def process_url_thread(self, url):
        try:
            # Download audio
            self.update_progress("Downloading audio...", 10)
            audio_file = self.audio_processor.download_audio(url, self.download_progress_hook)
            
            # Set the audio file in transcription manager
            self.transcription_manager.temp_audio_file = audio_file
            
            # Start transcription
            self.start_timer()
            transcription, summary = self.transcription_manager.transcribe(self.update_progress)
            
            # Update UI with results
            self.root.after(0, self.update_results, transcription, summary)
            
        except Exception as e:
            self.root.after(0, self.show_transcription_error, str(e))
        finally:
            self.root.after(0, self.cleanup)
            if hasattr(self, 'audio_file') and self.audio_file:
                self.audio_processor.cleanup(self.audio_file)

    def download_progress_hook(self, d):
        """Progress hook for yt-dlp"""
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes:
                progress = (downloaded_bytes / total_bytes) * 50  # Use first 50% for download
                self.update_progress(f"Downloading audio... {progress:.1f}%", progress)
        elif d['status'] == 'finished':
            self.update_progress("Download completed. Starting transcription...", 50)

    def update_results(self, transcription, summary):
        """Update UI with transcription and summary results"""
        self.transcription_text.delete(1.0, tk.END)
        self.transcription_text.insert(tk.END, transcription)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary)
        self.cleanup()

    def show_transcription_error(self, error_message):
        """Show error message in UI"""
        messagebox.showerror("Error", error_message)
        self.cleanup()

    def cleanup(self):
        """Reset UI state after processing"""
        self.process_button.config(state='normal')
        self.save_button.config(state='normal')
        self.stop_timer()
        self.progress_var.set(0)
        self.progress_label.config(text="")

    def save_to_file(self):
        """Save transcription and summary to a file"""
        if not self.transcription_text.get(1.0, tk.END).strip() and not self.summary_text.get(1.0, tk.END).strip():
            messagebox.showerror("Error", "No text to save")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.transcription_text.get(1.0, tk.END))
                    file.write("\n\n")
                    file.write(self.summary_text.get(1.0, tk.END))
                messagebox.showinfo("Success", "File saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving file: {str(e)}")
