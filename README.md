# SCRIBD_to_PDF

A Python tool for downloading Scribd documents as PDF files for educational purposes.

## Features

- 🔍 Extract document pages from Scribd URLs
- ⚡ Multithreaded downloading for faster processing
- 📄 Automatic PDF generation from images
- 🔧 Customizable image quality and sizing
 ```bash
(Note : The tool doesn't yet support pages with text only pages which are pictures)
  ```
## 🛠️ Requirements

- Python 3.7+
- Required packages:

  ```bash
  pip install requests Pillow img2pdf
  ```

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ILFforever/SCRIBD_to_PDF.git
   cd SCRIBD_to_PDF
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Usage

1. Run the script:
   ```bash
   python Scribd_to_PDF.py
   ```

2. Enter a Scribd document URL when prompted:
   ```
   https://www.scribd.com/document/123456/your-document
   ```

3. Configure settings:
   - **Max Width**: Maximum image width in pixels (default: 1200)
   - **Quality**: JPEG quality 1-100% (default: 85%)
   - **Filename**: Output PDF name (defaults to the file name on the page)

4. Wait for processing and find your PDF in the current directory!

## ⚖️ Legal Disclaimer

- **Educational use only** - This tool is intended for educational and research purposes
- **Respects robots.txt** - Only accesses publicly available document pages
- **Terms of Service** - Users must comply with Scribd's Terms of Service
- **User Responsibility** - Users are responsible for ensuring their use complies with local laws and regulations
- **No Commercial Use** - This tool should not be used for commercial purposes

## 🔧 Technical Details

### How It Works
1. Extracts page URLs from Scribd document metadata
2. Fetches JSONP content containing image URLs
3. Downloads images in parallel using multithreading
4. Processes images (resize, optimize) in memory
5. Combines images into a single PDF file

### Getting Help

If you encounter issues:
1. Check that your Scribd URL is in the correct format
2. Ensure all dependencies are installed correctly
3. Verify your internet connection is stable

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

💖 I can be contacted at hammymukura@gmail.com

**Note**: This tool is for educational purposes only. Please respect content creators' rights and Scribd's Terms of Service.
