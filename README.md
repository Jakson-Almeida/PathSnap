# PathSnap - Directory Tree Explorer

A modern, feature-rich GUI application for exploring directory structures with beautiful tree visualization.

## Features

- **Intuitive GUI**: Clean, modern interface built with tkinter
- **Flexible Directory Selection**: Browse or manually enter directory paths
- **Configurable Depth**: Set maximum search depth (unlimited by default)
- **Smart Filtering**: Show folders only, files only, or both
- **Proper Tree Structure**: Correctly formatted tree with proper symbols (├──, └──, │)
- **Real-time Progress**: Visual progress indication during scanning
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Copy to Clipboard**: Easy copying of results
- **Statistics**: Display item counts and processing status
- **Responsive Design**: Resizable window with proper scrolling

## Requirements

- Python 3.6+
- tkinter (usually included with Python)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/PathSnap.git
cd PathSnap
```

2. Run the application:
```bash
python app.py
```

## Usage

1. **Select Directory**: Use the "Browse" button or manually enter a directory path
2. **Configure Options**:
   - Set maximum depth (-1 for unlimited)
   - Choose what to display (Both, Folders, or Files)
3. **Generate Tree**: Click "Generate Tree" to start scanning
4. **View Results**: The tree structure will appear in the text area
5. **Copy Results**: Use "Copy Results" to copy the tree to clipboard

## Features in Detail

### Tree Structure Formatting
The application generates properly formatted tree structures:
```
project/
├── src/
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_main.py
└── README.md
```

### Error Handling
- Validates directory existence before scanning
- Handles permission errors gracefully
- Provides clear error messages to users

### Performance
- Multi-threaded scanning to keep UI responsive
- Progress indication for large directories
- Ability to stop long-running scans

## Screenshots

The application features a clean, modern interface with:
- Directory selection panel
- Configuration options
- Progress indication
- Scrollable results area
- Copy functionality

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### Version 2.0
- Fixed tree structure formatting
- Added proper error handling
- Improved UI with progress indication
- Added statistics display
- Enhanced code quality with type hints
- Added comprehensive documentation
