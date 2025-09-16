import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import os
import queue
import threading
from typing import Optional, List, Tuple
from pathlib import Path

# Configure ttk styles
def configure_styles():
    """Configure modern ttk styles for a beautiful UI."""
    style = ttk.Style()
    
    # Set theme
    style.theme_use('clam')
    
    # Configure main window colors
    style.configure('Title.TLabel', 
                   font=('TkDefaultFont', 12, 'bold'))
    
    # Configure section headers
    style.configure('Section.TLabel', 
                   font=('TkDefaultFont', 10, 'bold'))
    
    # Configure buttons
    style.configure('Primary.TButton',
                   font=('TkDefaultFont', 9, 'bold'),
                   padding=(12, 8))
    
    style.configure('Secondary.TButton',
                   font=('TkDefaultFont', 9),
                   padding=(8, 6))
    
    style.configure('Danger.TButton',
                   font=('TkDefaultFont', 9),
                   padding=(8, 6))
    
    # Configure entry fields
    style.configure('Modern.TEntry',
                   font=('TkDefaultFont', 9),
                   padding=(8, 6))
    
    # Configure progress bar
    style.configure('Modern.Horizontal.TProgressbar',
                   background='#3498db',
                   troughcolor='#ecf0f1')
    
    # Configure label frames
    style.configure('Card.TLabelframe',
                   relief='solid',
                   borderwidth=1)
    
    style.configure('Card.TLabelframe.Label',
                   font=('TkDefaultFont', 10, 'bold'))

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
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Configure modern styling
        configure_styles()
        
        # Threading control
        self.stop_event = threading.Event()
        self.search_thread: Optional[threading.Thread] = None
        self.queue = queue.Queue()
        self.items_processed = 0
        
        # Folder ignore functionality
        self.ignored_folders = set()
        self.load_default_ignore_patterns()
        
        # UI state
        self.options_expanded = False
        
        self.setup_ui()
    
    def load_default_ignore_patterns(self) -> None:
        """Load common ignore patterns."""
        common_patterns = [
            '__pycache__',
            '.git',
            '.svn',
            'node_modules',
            '.vscode',
            '.idea',
            'venv',
            'env',
            '.env',
            'build',
            'dist',
            'target',
            '.DS_Store',
            'Thumbs.db'
        ]
        self.ignored_folders.update(common_patterns)
        
        # Update UI if it exists
        if hasattr(self, 'ignore_listbox'):
            self.ignore_listbox.delete(0, tk.END)
            for pattern in sorted(self.ignored_folders):
                self.ignore_listbox.insert(tk.END, pattern)
            self.progress_var.set("Loaded default ignore patterns")
            self.root.after(2000, lambda: self.progress_var.set("Ready"))
        
    def setup_ui(self) -> None:
        """Set up the user interface."""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Compact header section
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title and main controls in one row
        title_controls_frame = ttk.Frame(header_frame)
        title_controls_frame.pack(fill=tk.X)
        
        # Title
        title_label = ttk.Label(title_controls_frame, text="PathSnap", style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # Directory selection (compact)
        dir_frame = ttk.Frame(title_controls_frame)
        dir_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 0))
        
        ttk.Label(dir_frame, text="Directory:", style='Section.TLabel').pack(side=tk.LEFT)
        self.dir_entry = ttk.Entry(dir_frame, style='Modern.TEntry', width=40)
        self.dir_entry.pack(side=tk.LEFT, padx=(5, 5))
        self.dir_entry.insert(0, os.path.expanduser("~"))
        
        browse_btn = ttk.Button(dir_frame, text="Browse", 
                               command=self.browse_directory, style='Secondary.TButton')
        browse_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Main action buttons
        action_frame = ttk.Frame(title_controls_frame)
        action_frame.pack(side=tk.RIGHT)
        
        self.search_btn = ttk.Button(action_frame, text="Generate Tree", 
                                    command=self.toggle_search, style='Primary.TButton')
        self.search_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_btn = ttk.Button(action_frame, text="Clear", 
                              command=self.clear_results, style='Secondary.TButton')
        clear_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Options toggle button
        self.options_btn = ttk.Button(action_frame, text="Options", 
                                     command=self.toggle_options, style='Secondary.TButton')
        self.options_btn.pack(side=tk.LEFT)
        
        # Collapsible options panel
        self.options_frame = ttk.Frame(header_frame)
        self.options_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Options content (initially hidden)
        options_content = ttk.LabelFrame(self.options_frame, text="Options", 
                                        style='Card.TLabelframe', padding=10)
        options_content.pack(fill=tk.X)
        
        # Options in a single row
        options_row = ttk.Frame(options_content)
        options_row.pack(fill=tk.X)
        
        # Depth control
        depth_frame = ttk.Frame(options_row)
        depth_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(depth_frame, text="Max Depth:", style='Section.TLabel').pack(side=tk.LEFT)
        self.depth_entry = ttk.Entry(depth_frame, style='Modern.TEntry', width=8)
        self.depth_entry.pack(side=tk.LEFT, padx=(5, 0))
        self.depth_entry.insert(0, "-1")
        
        # Display options
        show_frame = ttk.Frame(options_row)
        show_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(show_frame, text="Display:", style='Section.TLabel').pack(side=tk.LEFT)
        self.show_option = tk.StringVar(value="both")
        
        radio_frame = ttk.Frame(show_frame)
        radio_frame.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Radiobutton(radio_frame, text="Both", variable=self.show_option, value="both").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Radiobutton(radio_frame, text="Folders", variable=self.show_option, value="folders").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Radiobutton(radio_frame, text="Files", variable=self.show_option, value="files").pack(side=tk.LEFT)
        
        # Ignore folders (compact)
        ignore_frame = ttk.Frame(options_row)
        ignore_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(ignore_frame, text="Ignore:", style='Section.TLabel').pack(side=tk.LEFT)
        self.ignore_entry = ttk.Entry(ignore_frame, style='Modern.TEntry', width=15)
        self.ignore_entry.pack(side=tk.LEFT, padx=(5, 5))
        self.ignore_entry.bind('<Return>', lambda e: self.add_ignore_folder())
        
        add_ignore_btn = ttk.Button(ignore_frame, text="Add", 
                                   command=self.add_ignore_folder, style='Secondary.TButton')
        add_ignore_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Ignore list (compact dropdown style)
        self.ignore_listbox = tk.Listbox(ignore_frame, height=1, selectmode=tk.SINGLE,
                                        bg='#ffffff', fg='#2c3e50',
                                        selectbackground='#3498db', selectforeground='white',
                                        relief='solid', borderwidth=1)
        self.ignore_listbox.pack(side=tk.LEFT, padx=(0, 5))
        
        # Ignore management buttons
        ignore_btn_frame = ttk.Frame(ignore_frame)
        ignore_btn_frame.pack(side=tk.LEFT)
        
        remove_ignore_btn = ttk.Button(ignore_btn_frame, text="Remove", 
                                      command=self.remove_ignore_folder, style='Secondary.TButton')
        remove_ignore_btn.pack(side=tk.LEFT, padx=(0, 3))
        
        clear_ignore_btn = ttk.Button(ignore_btn_frame, text="Clear", 
                                     command=self.clear_ignore_folders, style='Danger.TButton')
        clear_ignore_btn.pack(side=tk.LEFT, padx=(0, 3))
        
        load_defaults_btn = ttk.Button(ignore_btn_frame, text="Defaults", 
                                      command=self.load_default_ignore_patterns, style='Secondary.TButton')
        load_defaults_btn.pack(side=tk.LEFT)
        
        # Load default ignore patterns into listbox
        for pattern in sorted(self.ignored_folders):
            self.ignore_listbox.insert(tk.END, pattern)
        
        # Initially hide options
        self.options_frame.pack_forget()
        
        # Progress bar (compact)
        progress_frame = ttk.Frame(main_container)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var, 
                                       style='Section.TLabel')
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate', 
                                           style='Modern.Horizontal.TProgressbar')
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Main results area (takes most space)
        results_frame = ttk.LabelFrame(main_container, text="Directory Tree", 
                                      style='Card.TLabelframe', padding=5)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Text area with custom styling
        self.text_area = scrolledtext.ScrolledText(
            results_frame, 
            wrap=tk.NONE,
            font=("Courier", 9),
            bg="#ffffff",
            fg="#2c3e50",
            relief="solid",
            borderwidth=1,
            selectbackground="#3498db",
            selectforeground="white",
            insertbackground="#2c3e50"
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # Bottom status bar
        status_frame = ttk.Frame(main_container)
        status_frame.pack(fill=tk.X)
        
        self.stats_var = tk.StringVar(value="")
        self.stats_label = ttk.Label(status_frame, textvariable=self.stats_var, 
                                    font=('TkDefaultFont', 9), foreground='#7f8c8d')
        self.stats_label.pack(side=tk.LEFT)
        
        copy_btn = ttk.Button(status_frame, text="Copy Results", 
                             command=self.copy_results, style='Primary.TButton')
        copy_btn.pack(side=tk.RIGHT)
    
    def toggle_options(self) -> None:
        """Toggle the options panel visibility."""
        if self.options_expanded:
            self.options_frame.pack_forget()
            self.options_btn.config(text="Options")
            self.options_expanded = False
        else:
            self.options_frame.pack(fill=tk.X, pady=(10, 0))
            self.options_btn.config(text="Hide Options")
            self.options_expanded = True
    
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
    
    def add_ignore_folder(self) -> None:
        """Add a folder to the ignore list."""
        folder_name = self.ignore_entry.get().strip()
        if folder_name:
            if folder_name not in self.ignored_folders:
                self.ignored_folders.add(folder_name)
                self.ignore_listbox.insert(tk.END, folder_name)
                self.ignore_entry.delete(0, tk.END)
                self.progress_var.set(f"Added '{folder_name}' to ignore list")
                self.root.after(2000, lambda: self.progress_var.set("Ready"))
            else:
                self.progress_var.set(f"'{folder_name}' is already in ignore list")
                self.root.after(2000, lambda: self.progress_var.set("Ready"))
    
    def remove_ignore_folder(self) -> None:
        """Remove selected folder from ignore list."""
        selection = self.ignore_listbox.curselection()
        if selection:
            index = selection[0]
            folder_name = self.ignore_listbox.get(index)
            self.ignored_folders.discard(folder_name)
            self.ignore_listbox.delete(index)
            self.progress_var.set(f"Removed '{folder_name}' from ignore list")
            self.root.after(2000, lambda: self.progress_var.set("Ready"))
    
    def clear_ignore_folders(self) -> None:
        """Clear all ignored folders."""
        self.ignored_folders.clear()
        self.ignore_listbox.delete(0, tk.END)
        self.progress_var.set("Cleared all ignored folders")
        self.root.after(2000, lambda: self.progress_var.set("Ready"))
    
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
            args=(start_dir, max_depth, show_option, self.ignored_folders),
            daemon=True
        )
        self.search_thread.start()
        self.search_btn.config(text="Stop")
        self.progress_bar.start()
        self.progress_var.set("Scanning directory...")
        self.monitor_search()
    
    def search_directory(self, start_dir: str, max_depth: int, show_option: str, ignored_folders: set) -> None:
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
                
                # Filter out ignored folders
                filtered_dirs = []
                dirs_to_remove = []
                for dir_name in dirs:
                    if dir_name not in ignored_folders:
                        filtered_dirs.append(dir_name)
                    else:
                        # Mark for removal from os.walk traversal
                        dirs_to_remove.append(dir_name)
                
                # Remove ignored directories from os.walk traversal
                for dir_name in dirs_to_remove:
                    dirs.remove(dir_name)
                
                all_paths.append((root, depth, sorted(filtered_dirs), sorted(files)))
            
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
