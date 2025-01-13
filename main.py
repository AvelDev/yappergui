import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import messagebox

class URLProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("URL Processor")
        self.root.geometry("600x400")

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

        # Save Button
        self.save_button = ttk.Button(main_frame, text="Save to File", command=self.save_to_file)
        self.save_button.grid(row=3, column=0, columnspan=3, pady=10)

    def process_url(self):
        url = self.url_entry.get()
        if url:
            # For now, just return the URL as the result
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, url)
        else:
            messagebox.showwarning("Warning", "Please enter a URL")

    def save_to_file(self):
        result = self.result_text.get(1.0, tk.END).strip()
        if result:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path:
                try:
                    with open(file_path, 'w') as file:
                        file.write(result)
                    messagebox.showinfo("Success", "Result saved successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file: {str(e)}")
        else:
            messagebox.showwarning("Warning", "No result to save")

def main():
    root = tk.Tk()
    app = URLProcessorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()