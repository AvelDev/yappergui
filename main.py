import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import messagebox
import yt_dlp
import os
import tempfile
from faster_whisper import WhisperModel
import threading
import json

class SettingsWindow:
    def __init__(self, parent, current_model, on_model_change):
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("400x300")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.models = ["tiny", "base", "small", "medium", "large", "large-v2"]
        self.current_model = current_model
        self.on_model_change = on_model_change
        
        # Create main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Model selection
        ttk.Label(main_frame, text="Select Whisper Model:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value=current_model)
        model_combo = ttk.Combobox(main_frame, textvariable=self.model_var, values=self.models, state="readonly")
        model_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # Model info
        self.info_text = tk.Text(main_frame, height=8, width=40, wrap=tk.WORD)
        self.info_text.grid(row=1, column=0, columnspan=2, pady=10)
        self.update_model_info(self.current_model)
        
        # Bind model change
        model_combo.bind('<<ComboboxSelected>>', lambda e: self.update_model_info(self.model_var.get()))
        
        # Save button
        ttk.Button(main_frame, text="Save", command=self.save_settings).grid(row=2, column=0, columnspan=2, pady=10)

    def update_model_info(self, model):
        model_info = {
            "tiny": "Smallest model, fastest but least accurate\nSize: ~75MB",
            "base": "Good balance for simple transcription\nSize: ~150MB",
            "small": "Better accuracy than base\nSize: ~500MB",
            "medium": "Good accuracy for most cases\nSize: ~1.5GB",
            "large": "High accuracy\nSize: ~3GB",
            "large-v2": "Best accuracy, newest version\nSize: ~3GB"
        }
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, model_info.get(model, ""))

    def save_settings(self):
        new_model = self.model_var.get()
        if new_model != self.current_model:
            self.on_model_change(new_model)
        self.window.destroy()

class URLProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("URL Processor")
        self.root.geometry("600x400")
        self.temp_audio_file = None
        self.whisper_model = None
        
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

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Model Settings", command=self.open_settings)
        
    def open_settings(self):
        SettingsWindow(self.root, self.settings["model"], self.change_model)

    def load_settings(self):
        default_settings = {"model": "base"}
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except:
                return default_settings
        return default_settings

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f)

    def change_model(self, new_model):
        self.settings["model"] = new_model
        self.save_settings()
        self.load_model()

    def load_model(self):
        try:
            self.update_progress("Loading model...", 0)
            
            # Check if model exists locally
            model_path = os.path.join(self.models_dir, self.settings['model'])
            if not os.path.exists(model_path):
                self.update_progress(f"Downloading {self.settings['model']} model... This might take a while.", 10)
            
            self.whisper_model = WhisperModel(
                self.settings["model"],
                device="cpu",
                compute_type="int8",
                download_root=self.models_dir
            )
            self.update_progress(f"Model {self.settings['model']} loaded successfully", 100)
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
        url = self.url_entry.get()
        if url:
            if url.startswith("https://www.youtube.com/watch?v="):
                try:
                    self.update_progress("Preparing to download audio...", 0)
                    self.process_button.config(state='disabled')
                    
                    # Create a temporary directory for the audio file
                    temp_dir = tempfile.mkdtemp()
                    temp_file = os.path.join(temp_dir, 'audio')
                    
                    # Configure yt-dlp options
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': temp_file,
                        'ffmpeg_location': '/opt/homebrew/bin/ffmpeg',
                        'progress_hooks': [self.download_progress_hook],
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                    }

                    # Download audio
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    
                    # Store the path to the temporary file (with mp3 extension)
                    self.temp_audio_file = temp_file + '.mp3'
                    
                    # Start transcription in a separate thread
                    threading.Thread(target=self.transcribe_audio, daemon=True).start()
                
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to download audio: {str(e)}")
                    self.cleanup_temp_file()
                    self.process_button.config(state='normal')
                    self.update_progress("", 0)
            else:
                messagebox.showwarning("Warning", "Please enter a valid YouTube URL")
        else:
            messagebox.showwarning("Warning", "Please enter a URL")

    def transcribe_audio(self):
        try:
            if not self.whisper_model:
                self.load_model()
            
            self.update_progress("Transcribing audio... This might take a while...", 50)
            
            # Perform transcription in steps to show progress
            # 1. Detect language (60%)
            self.update_progress("Detecting language...", 60)
            segments, info = self.whisper_model.transcribe(
                self.temp_audio_file,
                beam_size=5
            )
            
            # 2. Process segments (60-90%)
            segments_list = list(segments)  # Convert generator to list
            total_segments = len(segments_list)
            processed_text = []
            
            for i, segment in enumerate(segments_list):
                progress = 60 + (i / total_segments) * 30
                self.update_progress(f"Processing segment {i+1}/{total_segments}...", progress)
                processed_text.append(segment.text)
            
            # 3. Combine results (90-100%)
            self.update_progress("Finalizing transcription...", 90)
            text = " ".join(processed_text)
            
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

    def show_transcription_error(self, error_message):
        messagebox.showerror("Transcription Error", f"Failed to transcribe audio: {error_message}")
        self.update_progress("", 0)
        self.process_button.config(state='normal')

    def cleanup_after_transcription(self):
        self.process_button.config(state='normal')

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