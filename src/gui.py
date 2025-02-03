import customtkinter as ctk
from tkinter import messagebox, filedialog
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
        self.root.geometry("800x900")
        
        # Dodanie minimalnego rozmiaru okna
        self.root.minsize(400, 300)  # Minimalne wymiary okna
        
        # Konfiguracja customtkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Konfiguracja responsywności
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
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
        # Główny scrollowany kontener
        self.main_frame = ctk.CTkScrollableFrame(
            self.root,
            width=760,  # Szerokość nieco mniejsza niż okno by zmieścić scrollbar
            height=860  # Wysokość nieco mniejsza niż okno by zmieścić scrollbar
        )
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # URL Frame
        url_frame = ctk.CTkFrame(self.main_frame)
        url_frame.grid(row=0, column=0, padx=10, pady=(0, 20), sticky="ew")
        url_frame.grid_columnconfigure(0, weight=1)
        
        # URL Entry
        self.url_entry = ctk.CTkEntry(
            url_frame, 
            placeholder_text="Wprowadź URL z YouTube",
            height=40
        )
        self.url_entry.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        
        # Process Button
        self.process_button = ctk.CTkButton(
            url_frame,
            text="Podsumuj",
            command=self.process_url,
            height=40,
            width=120
        )
        self.process_button.grid(row=0, column=1, padx=(5, 10), pady=10)
        
        # Transcription Frame
        transcription_frame = ctk.CTkFrame(self.main_frame)
        transcription_frame.grid(row=1, column=0, padx=10, pady=(0, 20), sticky="nsew")
        transcription_frame.grid_columnconfigure(0, weight=1)
        transcription_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(transcription_frame, text="Transkrypcja:", anchor="w").grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w"
        )
        
        self.transcription_text = ctk.CTkTextbox(
            transcription_frame,
            height=200,
            wrap="word"
        )
        self.transcription_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # Summary Frame
        summary_frame = ctk.CTkFrame(self.main_frame)
        summary_frame.grid(row=2, column=0, padx=10, pady=(0, 20), sticky="nsew")
        summary_frame.grid_columnconfigure(0, weight=1)
        summary_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(summary_frame, text="Podsumowanie:", anchor="w").grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w"
        )
        
        self.summary_text = ctk.CTkTextbox(
            summary_frame,
            height=200,
            wrap="word"
        )
        self.summary_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # Status Frame
        status_frame = ctk.CTkFrame(self.main_frame)
        status_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)
        
        # Timer Label
        self.timer_label = ctk.CTkLabel(status_frame, text="")
        self.timer_label.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="w")
        
        # Progress Label
        self.progress_label = ctk.CTkLabel(status_frame, text="Status")
        self.progress_label.grid(row=1, column=0, padx=10, pady=(5, 0), sticky="w")
        
        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(status_frame)
        self.progress_bar.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")
        self.progress_bar.set(0)
        
        # Save Button
        self.save_button = ctk.CTkButton(
            self.main_frame,
            text="Zapisz do pliku",
            command=self.save_to_file,
            height=40
        )
        self.save_button.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Menu Button
        self.settings_button = ctk.CTkButton(
            self.main_frame,
            text="Ustawienia",
            command=self.open_settings,
            height=40
        )
        self.settings_button.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="ew")

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
            self.timer_label.configure(text=f"Czas transkrypcji: {minutes:02d}:{seconds:02d}")
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
        self.progress_label.configure(text=message)
        if progress is not None:
            self.progress_bar.set(progress / 100)
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

        self.process_button.configure(state='disabled')
        self.save_button.configure(state='disabled')
        self.transcription_text.delete(1.0, ctk.END)
        self.summary_text.delete(1.0, ctk.END)
        self.progress_bar.set(0)
        
        try:
            threading.Thread(
                target=self.process_url_thread,
                args=(url,),
                daemon=True
            ).start()
            
        except Exception as e:
            self.show_transcription_error(str(e))
            self.process_button.configure(state='normal')
            self.save_button.configure(state='normal')

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
        self.transcription_text.delete(1.0, ctk.END)
        self.transcription_text.insert(ctk.END, transcription)
        self.summary_text.delete(1.0, ctk.END)
        self.summary_text.insert(ctk.END, summary)
        self.cleanup()

    def show_transcription_error(self, error_message):
        """Show error message in UI"""
        messagebox.showerror("Error", error_message)
        self.cleanup()

    def cleanup(self):
        """Reset UI state after processing"""
        self.process_button.configure(state='normal')
        self.save_button.configure(state='normal')
        self.stop_timer()
        self.progress_bar.set(0)
        self.progress_label.configure(text="Status")

    def save_to_file(self):
        """Save transcription and summary to a file"""
        if not self.transcription_text.get(1.0, ctk.END).strip() and not self.summary_text.get(1.0, ctk.END).strip():
            messagebox.showerror("Error", "No text to save")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.transcription_text.get(1.0, ctk.END))
                    file.write("\n\n")
                    file.write(self.summary_text.get(1.0, ctk.END))
                messagebox.showinfo("Success", "File saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving file: {str(e)}")
