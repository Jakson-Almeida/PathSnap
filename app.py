import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import os
import queue
import threading

class DirectoryTreeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Directory Tree Explorer")
        self.root.geometry("800x600")
        self.setup_ui()
        
        # Threading control
        self.stop_event = threading.Event()
        self.search_thread = None
        self.queue = queue.Queue()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Directory selection
        dir_frame = ttk.Frame(main_frame)
        dir_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(dir_frame, text="Directory:").pack(side=tk.LEFT)
        self.dir_entry = ttk.Entry(dir_frame, width=50)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.dir_entry.insert(0, os.path.expanduser("~"))
        
        browse_btn = ttk.Button(dir_frame, text="Browse", command=self.browse_directory)
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        # Options frame
        opt_frame = ttk.Frame(main_frame)
        opt_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(opt_frame, text="Depth:").pack(side=tk.LEFT)
        self.depth_entry = ttk.Entry(opt_frame, width=8)
        self.depth_entry.pack(side=tk.LEFT, padx=5)
        self.depth_entry.insert(0, "-1")
        
        ttk.Label(opt_frame, text="Show:").pack(side=tk.LEFT, padx=(10, 5))
        self.show_option = tk.StringVar(value="both")
        ttk.Radiobutton(opt_frame, text="Both", variable=self.show_option, value="both").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(opt_frame, text="Folders", variable=self.show_option, value="folders").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(opt_frame, text="Files", variable=self.show_option, value="files").pack(side=tk.LEFT, padx=2)
        
        self.search_btn = ttk.Button(opt_frame, text="Search", command=self.toggle_search)
        self.search_btn.pack(side=tk.RIGHT)
        
        # Results text area
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.text_area = scrolledtext.ScrolledText(
            text_frame, 
            wrap=tk.NONE,
            font=("Consolas", 10))
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # Horizontal scrollbar
        x_scroll = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.text_area.xview)
        x_scroll.pack(fill=tk.X)
        self.text_area.config(xscrollcommand=x_scroll.set)
        
        # Copy button
        copy_frame = ttk.Frame(main_frame)
        copy_frame.pack(fill=tk.X, pady=5)
        
        copy_btn = ttk.Button(copy_frame, text="Copy Results", command=self.copy_results)
        copy_btn.pack(side=tk.RIGHT)
    
    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.dir_entry.get())
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
    
    def toggle_search(self):
        if self.search_thread and self.search_thread.is_alive():
            self.stop_event.set()
            self.search_btn.config(text="Search")
        else:
            self.start_search()
    
    def start_search(self):
        # Clear previous results
        self.text_area.delete(1.0, tk.END)
        self.stop_event.clear()
        
        # Get parameters
        start_dir = self.dir_entry.get()
        try:
            max_depth = int(self.depth_entry.get())
        except ValueError:
            max_depth = -1
        show_option = self.show_option.get()
        
        # Start search thread
        self.search_thread = threading.Thread(
            target=self.search_directory,
            args=(start_dir, max_depth, show_option),
            daemon=True
        )
        self.search_thread.start()
        self.search_btn.config(text="Stop")
        self.monitor_search()
    
    def search_directory(self, start_dir, max_depth, show_option):
        try:
            if not os.path.isdir(start_dir):
                self.queue.put(f"Error: Directory not found - {start_dir}")
                return
            
            # Walk through directory tree
            for root, dirs, files in os.walk(start_dir):
                if self.stop_event.is_set():
                    break
                
                # Calculate current depth
                rel_path = os.path.relpath(root, start_dir)
                depth = 0 if rel_path == "." else len(rel_path.split(os.sep))
                
                # Skip if beyond max depth
                if max_depth >= 0 and depth > max_depth:
                    continue
                
                # Format prefix based on depth
                prefix = "  " * depth
                
                # Handle root directory
                if depth == 0:
                    self.queue.put(start_dir)
                
                # Process directories
                if show_option in ["both", "folders"]:
                    for d in sorted(dirs):
                        self.queue.put(f"{prefix}├── {d}/")
                
                # Process files
                if show_option in ["both", "files"]:
                    for f in sorted(files):
                        self.queue.put(f"{prefix}├── {f}")
            
            self.queue.put(None)  # Search complete signal
            
        except Exception as e:
            self.queue.put(f"Error: {str(e)}")
    
    def monitor_search(self):
        try:
            while True:
                # Process all available items in queue
                try:
                    item = self.queue.get_nowait()
                    if item is None:  # Search complete
                        self.search_btn.config(text="Search")
                        break
                    self.text_area.insert(tk.END, item + "\n")
                    self.text_area.see(tk.END)
                except queue.Empty:
                    break
            
            # Check if thread is still running
            if self.search_thread.is_alive():
                self.root.after(100, self.monitor_search)
            else:
                self.search_btn.config(text="Search")
        except RuntimeError:
            pass  # Handle possible Tkinter shutdown
    
    def copy_results(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.text_area.get(1.0, tk.END))

if __name__ == "__main__":
    root = tk.Tk()
    app = DirectoryTreeApp(root)
    root.mainloop()
