import tkinter as tk
from gui import URLProcessorApp

def main():
    root = tk.Tk()
    app = URLProcessorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
