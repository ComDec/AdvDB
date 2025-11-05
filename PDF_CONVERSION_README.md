# Markdown to PDF Conversion Tool

This directory contains tools to convert RepCRec project documentation from Markdown to professionally formatted PDF files.

## Quick Start

### Convert Single File

```bash
python3 md_to_pdf.py PROJECT_PROPOSAL.md RepCRec_Project_Proposal.pdf
```

### Convert All Documentation

```bash
./convert_all_docs.sh
```

## Generated Files

After conversion, you will have:

- `RepCRec_Project_Proposal.pdf` - Main project proposal (English, ~75 KB)
- `算法实现总结.pdf` - Algorithm implementation summary (Chinese, ~427 KB)
- `RepCRec_README.pdf` - Project README
- `RepCRec_Project_Summary.pdf` - Project summary

Additionally, HTML intermediate files are generated for debugging:
- `PROJECT_PROPOSAL.html`
- `算法实现总结.html`
- etc.

## Features

### Professional Styling
- ✓ Clean, academic-style formatting
- ✓ Professional typography with Georgia/Times New Roman fonts
- ✓ Syntax-highlighted code blocks
- ✓ Well-formatted tables
- ✓ Proper page headers and footers
- ✓ Page numbers
- ✓ A4 page size with proper margins

### Markdown Support
- ✓ Headers (H1-H4)
- ✓ Bold and italic text
- ✓ Code blocks (fenced and inline)
- ✓ Tables
- ✓ Lists (ordered and unordered)
- ✓ Blockquotes
- ✓ Horizontal rules

## Dependencies

The conversion tool requires:

- Python 3.7+
- `markdown` - Markdown parser
- `weasyprint` - HTML to PDF converter

### Installation

```bash
pip install markdown weasyprint
```

### System Dependencies (for WeasyPrint)

**Ubuntu/Debian:**
```bash
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0
```

**macOS:**
```bash
brew install pango
```

**Windows:**
Download and install GTK3 runtime from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer

## Usage

### Basic Usage

```bash
python3 md_to_pdf.py <input.md> [output.pdf]
```

If output filename is not specified, it will use the input filename with `.pdf` extension.

### Examples

```bash
# Convert with automatic output name
python3 md_to_pdf.py README.md

# Convert with custom output name
python3 md_to_pdf.py README.md MyProject_README.pdf

# Convert Chinese document
python3 md_to_pdf.py 算法实现总结.md
```

### Batch Conversion

Use the provided shell script to convert all documentation:

```bash
chmod +x convert_all_docs.sh
./convert_all_docs.sh
```

## Troubleshooting

### ImportError: No module named 'markdown'

Install the required packages:
```bash
pip install markdown weasyprint
```

### WeasyPrint warnings about fonts

This is normal. WeasyPrint will use fallback fonts if specific fonts are not available. The PDF will still be generated correctly.

### Chinese characters not displaying

Make sure your system has Chinese fonts installed:

**Ubuntu/Debian:**
```bash
sudo apt-get install fonts-noto-cjk
```

**macOS:**
Chinese fonts are pre-installed.

## Customization

To modify the PDF styling, edit the CSS in the `create_html_with_styling()` function in `md_to_pdf.py`.

Key style sections:
- `@page` - Page size, margins, headers/footers
- `body` - Font family, size, line height
- `h1, h2, h3, h4` - Header styles
- `code, pre` - Code block styling
- `table, th, td` - Table formatting

## Output Quality

The generated PDFs are:
- **Print-ready**: A4 size with appropriate margins
- **Professional**: Academic-style formatting
- **Readable**: Clear typography and proper spacing
- **Structured**: Proper hierarchy with styled headers
- **Compact**: Optimized file size

## File Sizes

Typical file sizes:
- Simple documentation (like README): 50-100 KB
- Comprehensive proposals: 75-150 KB
- Documents with many code blocks: 200-500 KB

## License

This conversion tool is provided as part of the RepCRec project under MIT License.

## Support

For issues or questions about the conversion tool, refer to the main RepCRec project documentation.

---

**Last Updated:** November 6, 2025
