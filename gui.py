import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import time
from settings import SettingsWindow, load_settings, save_settings_to_file
from utils import find_ffmpeg
from transcription import TranscriptionManager

class URLProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("URL Processor")
        self.root.geometry("600x400")
        
        # Initialize variables
        self.transcription_start_time = None
        self.timer_id = None
        
        # Create models directory if it doesn't exist
        self.models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Load settings
        self.settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        self.settings = load_settings(self.settings_file)
        
        # Initialize transcription manager
        self.transcription_manager = TranscriptionManager(self.models_dir, self.settings)

        self.setup_gui()
        self.check_ffmpeg()
        self.load_model()

    def setup_gui(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
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
        self.save_button = ttk.Button(main_frame, text="Save to File", command=self.save_to_file)
        self.save_button.grid(row=4, column=0, columnspan=3, pady=10)

        # Create menu
        self.create_menu()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Model Settings", command=self.open_settings)

    def check_ffmpeg(self):
        if not self.settings.get("ffmpeg_path"):
            ffmpeg_path = find_ffmpeg()
            if ffmpeg_path:
                self.settings["ffmpeg_path"] = ffmpeg_path
                save_settings_to_file(self.settings_file, self.settings)

    def load_model(self):
        try:
            self.transcription_manager.load_models(self.update_progress)
        except Exception as e:
            print(f"Error loading whisper model: {str(e)}")
            self.update_progress(f"Error loading model: {str(e)}", 0)

    def open_settings(self):
        SettingsWindow(self.root, self.settings, self.change_settings)

    def change_settings(self, new_settings):
        self.settings.update(new_settings)
        save_settings_to_file(self.settings_file, self.settings)
        self.transcription_manager.settings = self.settings
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
            save_settings_to_file(self.settings_file, self.settings)

        self.process_button.config(state='disabled')
        self.save_button.config(state='disabled')
        self.result_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        
        try:
            # Download audio in a separate thread
            threading.Thread(
                target=self.process_url_thread,
                args=(url, ffmpeg_path),
                daemon=True
            ).start()
            
        except Exception as e:
            self.show_transcription_error(str(e))
            self.process_button.config(state='normal')
            self.save_button.config(state='normal')

    def process_url_thread(self, url, ffmpeg_path):
        try:
            # Download audio
            self.transcription_manager.download_audio(url, ffmpeg_path, self.download_progress_hook)
            
            # Start transcription
            self.start_timer()
            transcription, summary = self.transcription_manager.transcribe(self.update_progress)
            
            # Update GUI in the main thread
            self.root.after(0, self.update_transcription_result, transcription, summary)
            
        except Exception as e:
            self.root.after(0, self.show_transcription_error, str(e))
        finally:
            self.root.after(0, self.cleanup_after_transcription)

    def update_transcription_result(self, transcription, summary):
        """Update the result text area with transcription and summary"""
        self.result_text.delete(1.0, tk.END)
        
        # Add summary section
        self.result_text.insert(tk.END, "=== PODSUMOWANIE ===\n\n")
        if summary:
            self.result_text.insert(tk.END, f"{summary}\n\n")
        else:
            self.result_text.insert(tk.END, "Nie udało się wygenerować podsumowania.\n\n")
        
        # Add transcription section
        self.result_text.insert(tk.END, "=== PEŁNA TRANSKRYPCJA ===\n\n")
        self.result_text.insert(tk.END, transcription)
        
        # Enable buttons
        self.process_button.config(state='normal')
        self.save_button.config(state='normal')
        
        # Stop the timer
        self.stop_timer()
        
        # Update progress
        self.update_progress("Transcription completed!", 100)

    def show_transcription_error(self, error_message):
        messagebox.showerror("Transcription Error", f"Failed to transcribe audio: {error_message}")
        self.update_progress("", 0)
        self.process_button.config(state='normal')
        self.save_button.config(state='normal')

    def cleanup_after_transcription(self):
        self.stop_timer()
        self.process_button.config(state=tk.NORMAL)
        self.update_progress("", 0)

    def save_to_file(self):
        """Save transcription and summary to a file"""
        if not self.result_text.get(1.0, tk.END).strip():
            messagebox.showerror("Error", "No text to save")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.result_text.get(1.0, tk.END))
                messagebox.showinfo("Success", "File saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving file: {str(e)}")
