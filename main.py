import sys
sys.path.append('src')
import tkinter as tk
from src.gui import URLProcessorApp
from src.api import start_api
import argparse

def main():
    parser = argparse.ArgumentParser(description='URL Processor Application')
    parser.add_argument('--api', action='store_true', help='Run in API mode')
    parser.add_argument('--port', type=int, default=5000, help='Port for API server')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host for API server')
    
    args = parser.parse_args()
    
    if args.api:
        print(f"Starting API server on {args.host}:{args.port}")
        start_api(host=args.host, port=args.port)
    else:
        root = tk.Tk()
        app = URLProcessorApp(root)
        root.mainloop()

if __name__ == "__main__":
    main()
