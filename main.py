import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import messagebox
import yt_dlp
import os
import tempfile
from faster_whisper import WhisperModel
import threading

class URLProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("URL Processor")
        self.root.geometry("600x400")
        self.temp_audio_file = None
        self.whisper_model = None
        
        # Initialize whisper model
        try:
            self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
            print("Whisper model loaded successfully")
        except Exception as e:
            print(f"Error loading whisper model: {str(e)}")

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

        # Progress Label
        self.progress_label = ttk.Label(main_frame, text="")
        self.progress_label.grid(row=3, column=0, columnspan=3)

        # Save Button
        self.save_button = ttk.Button(main_frame, text="Save to File", command=self.save_to_file)
        self.save_button.grid(row=4, column=0, columnspan=3, pady=10)

    def process_url(self):
        url = self.url_entry.get()
        if url:
            if url.startswith("https://www.youtube.com/watch?v="):
                try:
                    self.progress_label.config(text="Downloading audio...")
                    self.process_button.config(state='disabled')
                    
                    # Create a temporary directory for the audio file
                    temp_dir = tempfile.mkdtemp()
                    temp_file = os.path.join(temp_dir, 'audio')
                    
                    # Configure yt-dlp options
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': temp_file,
                        'ffmpeg_location': '/opt/homebrew/bin/ffmpeg',  # Path to ffmpeg
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
                    self.progress_label.config(text="")
            else:
                messagebox.showwarning("Warning", "Please enter a valid YouTube URL")
        else:
            messagebox.showwarning("Warning", "Please enter a URL")

    def transcribe_audio(self):
        try:
            if not self.whisper_model:
                self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
            
            self.progress_label.config(text="Transcribing audio... This might take a while...")
            
            # Perform transcription
            segments, _ = self.whisper_model.transcribe(self.temp_audio_file, beam_size=5)
            
            # Combine all segments
            text = " ".join([segment.text for segment in segments])
            
            # Update GUI in the main thread
            self.root.after(0, self.update_transcription_result, text)
            
        except Exception as e:
            self.root.after(0, self.show_transcription_error, str(e))
        finally:
            self.root.after(0, self.cleanup_after_transcription)

    def update_transcription_result(self, text):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
        self.progress_label.config(text="Transcription completed!")
        self.process_button.config(state='normal')

    def show_transcription_error(self, error_message):
        messagebox.showerror("Transcription Error", f"Failed to transcribe audio: {error_message}")
        self.progress_label.config(text="")
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