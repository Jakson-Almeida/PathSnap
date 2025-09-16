import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import os
import queue
import threading
from typing import Optional, List, Tuple
from pathlib import Path

class DirectoryTreeApp:
    """
    A GUI application for exploring directory structures with tree visualization.
    
    Features:
    - Browse and select directories
    - Configurable search depth
    - Filter by folders, files, or both
    - Proper tree structure formatting
    - Progress indication
    - Error handling
    - Copy results to clipboard
    """
    
    def __init__(self, root: tk.Tk) -> None:
        """Initialize the application."""
        self.root = root
        self.root.title("PathSnap - Directory Tree Explorer")
        self.root.geometry("900x700")
        self.root.minsize(600, 400)
        
        # Threading control
        self.stop_event = threading.Event()
        self.search_thread: Optional[threading.Thread] = None
        self.queue = queue.Queue()
        self.items_processed = 0
        
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Set up the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Directory selection frame
        dir_frame = ttk.LabelFrame(main_frame, text="Directory Selection", padding=5)
        dir_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(dir_frame, text="Directory:").pack(side=tk.LEFT)
        self.dir_entry = ttk.Entry(dir_frame, width=50)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.dir_entry.insert(0, os.path.expanduser("~"))
        
        browse_btn = ttk.Button(dir_frame, text="Browse", command=self.browse_directory)
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        # Options frame
        opt_frame = ttk.LabelFrame(main_frame, text="Options", padding=5)
        opt_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Depth control
        depth_frame = ttk.Frame(opt_frame)
        depth_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(depth_frame, text="Max Depth:").pack(side=tk.LEFT)
        self.depth_entry = ttk.Entry(depth_frame, width=8)
        self.depth_entry.pack(side=tk.LEFT, padx=5)
        self.depth_entry.insert(0, "-1")
        
        # Show options
        show_frame = ttk.Frame(opt_frame)
        show_frame.pack(side=tk.LEFT, padx=(20, 0))
        
        ttk.Label(show_frame, text="Show:").pack(side=tk.LEFT)
        self.show_option = tk.StringVar(value="both")
        ttk.Radiobutton(show_frame, text="Both", variable=self.show_option, value="both").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(show_frame, text="Folders", variable=self.show_option, value="folders").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(show_frame, text="Files", variable=self.show_option, value="files").pack(side=tk.LEFT, padx=2)
        
        # Control buttons
        btn_frame = ttk.Frame(opt_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        self.search_btn = ttk.Button(btn_frame, text="Generate Tree", command=self.toggle_search)
        self.search_btn.pack(side=tk.LEFT, padx=2)
        
        clear_btn = ttk.Button(btn_frame, text="Clear", command=self.clear_results)
        clear_btn.pack(side=tk.LEFT, padx=2)
        
        # Progress frame
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = ttk.Label(self.progress_frame, textvariable=self.progress_var)
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Results text area
        text_frame = ttk.LabelFrame(main_frame, text="Directory Tree", padding=5)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.text_area = scrolledtext.ScrolledText(
            text_frame, 
            wrap=tk.NONE,
            font=("Consolas", 9),
            bg="#f8f8f8",
            fg="#333333"
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # Horizontal scrollbar
        x_scroll = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.text_area.xview)
        x_scroll.pack(fill=tk.X)
        self.text_area.config(xscrollcommand=x_scroll.set)
        
        # Bottom frame with copy button and stats
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)
        
        self.stats_var = tk.StringVar(value="")
        self.stats_label = ttk.Label(bottom_frame, textvariable=self.stats_var)
        self.stats_label.pack(side=tk.LEFT)
        
        copy_btn = ttk.Button(bottom_frame, text="Copy Results", command=self.copy_results)
        copy_btn.pack(side=tk.RIGHT)
    
    def browse_directory(self) -> None:
        """Open directory browser dialog."""
        directory = filedialog.askdirectory(initialdir=self.dir_entry.get())
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
    
    def clear_results(self) -> None:
        """Clear the results text area."""
        self.text_area.delete(1.0, tk.END)
        self.stats_var.set("")
        self.progress_var.set("Ready")
    
    def toggle_search(self) -> None:
        """Toggle search operation (start/stop)."""
        if self.search_thread and self.search_thread.is_alive():
            self.stop_event.set()
            self.search_btn.config(text="Generate Tree")
            self.progress_bar.stop()
            self.progress_var.set("Stopping...")
        else:
            self.start_search()
    
    def start_search(self) -> None:
        """Start the directory search operation."""
        # Validate directory
        start_dir = self.dir_entry.get().strip()
        if not start_dir:
            messagebox.showerror("Error", "Please select a directory.")
            return
            
        if not os.path.isdir(start_dir):
            messagebox.showerror("Error", f"Directory not found: {start_dir}")
            return
        
        # Clear previous results
        self.text_area.delete(1.0, tk.END)
        self.stop_event.clear()
        self.items_processed = 0
        
        # Get parameters
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
        self.progress_bar.start()
        self.progress_var.set("Scanning directory...")
        self.monitor_search()
    
    def search_directory(self, start_dir: str, max_depth: int, show_option: str) -> None:
        """Search directory and build tree structure."""
        try:
            if not os.path.isdir(start_dir):
                self.queue.put(f"Error: Directory not found - {start_dir}")
                return
            
            # Get all directory paths first to build proper tree structure
            all_paths = []
            for root, dirs, files in os.walk(start_dir):
                if self.stop_event.is_set():
                    break
                
                rel_path = os.path.relpath(root, start_dir)
                depth = 0 if rel_path == "." else len(rel_path.split(os.sep))
                
                if max_depth >= 0 and depth > max_depth:
                    continue
                
                all_paths.append((root, depth, sorted(dirs), sorted(files)))
            
            # Build tree structure
            self.queue.put(f"{os.path.basename(start_dir)}/")
            
            for root, depth, dirs, files in all_paths:
                if self.stop_event.is_set():
                    break
                
                if depth == 0:
                    continue  # Skip root directory (already added)
                
                # Build path components for proper tree formatting
                path_parts = os.path.relpath(root, start_dir).split(os.sep)
                prefix_parts = []
                
                # Build prefix for each level
                for i in range(depth):
                    if i == depth - 1:
                        # Last level - check if it's the last item
                        is_last = True
                        if i < len(path_parts) - 1:
                            # Check if this is the last directory at this level
                            parent_path = os.sep.join(path_parts[:i+1])
                            parent_full_path = os.path.join(start_dir, parent_path)
                            try:
                                parent_contents = os.listdir(parent_full_path)
                                dirs_in_parent = [d for d in parent_contents if os.path.isdir(os.path.join(parent_full_path, d))]
                                if path_parts[i] in dirs_in_parent:
                                    is_last = path_parts[i] == sorted(dirs_in_parent)[-1]
                            except (OSError, PermissionError):
                                is_last = True
                        
                        prefix_parts.append("└── " if is_last else "├── ")
                    else:
                        # Intermediate levels
                        prefix_parts.append("│   ")
                
                prefix = "".join(prefix_parts)
                dir_name = os.path.basename(root)
                self.queue.put(f"{prefix}{dir_name}/")
                
                # Process files in this directory
                if show_option in ["both", "files"]:
                    for i, file_name in enumerate(files):
                        if self.stop_event.is_set():
                            break
                        
                        is_last_file = (i == len(files) - 1) and show_option != "both"
                        file_prefix = "└── " if is_last_file else "├── "
                        self.queue.put(f"{prefix}{file_prefix}{file_name}")
                        self.items_processed += 1
            
            self.queue.put(None)  # Search complete signal
            
        except Exception as e:
            self.queue.put(f"Error: {str(e)}")
    
    def monitor_search(self) -> None:
        """Monitor search progress and update UI."""
        try:
            while True:
                # Process all available items in queue
                try:
                    item = self.queue.get_nowait()
                    if item is None:  # Search complete
                        self.search_btn.config(text="Generate Tree")
                        self.progress_bar.stop()
                        self.progress_var.set(f"Complete - {self.items_processed} items processed")
                        self.stats_var.set(f"Items: {self.items_processed}")
                        break
                    self.text_area.insert(tk.END, item + "\n")
                    self.text_area.see(tk.END)
                except queue.Empty:
                    break
            
            # Check if thread is still running
            if self.search_thread and self.search_thread.is_alive():
                self.root.after(100, self.monitor_search)
            else:
                self.search_btn.config(text="Generate Tree")
                self.progress_bar.stop()
        except RuntimeError:
            pass  # Handle possible Tkinter shutdown
    
    def copy_results(self) -> None:
        """Copy results to clipboard."""
        content = self.text_area.get(1.0, tk.END)
        if content.strip():
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.progress_var.set("Results copied to clipboard!")
            self.root.after(2000, lambda: self.progress_var.set("Ready"))
        else:
            messagebox.showwarning("Warning", "No results to copy.")

def main() -> None:
    """Main entry point."""
    root = tk.Tk()
    app = DirectoryTreeApp(root)
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
