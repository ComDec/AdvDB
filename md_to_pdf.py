#!/usr/bin/env python3
"""
Markdown to PDF Converter with Beautiful Rendering
Converts PROJECT_PROPOSAL.md to a professionally formatted PDF
"""

import sys
from pathlib import Path

import markdown


def create_html_with_styling(md_content, title="RepCRec Project Proposal"):
    """Convert markdown to HTML with professional styling"""

    # Convert markdown to HTML
    md = markdown.Markdown(
        extensions=[
            "extra",  # Tables, code blocks, etc.
            "codehilite",  # Syntax highlighting
            "toc",  # Table of contents
            "fenced_code",  # Fenced code blocks
            "tables",  # Table support
        ]
    )

    html_content = md.convert(md_content)

    # Professional CSS styling
    css = """
    <style>
        @page {
            size: A4;
            margin: 2.5cm 2cm 2cm 2cm;
            @top-right {
                content: "RepCRec Project";
                font-size: 10pt;
                color: #666;
            }
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10pt;
                color: #666;
            }
        }

        body {
            font-family: 'Georgia', 'Times New Roman', serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
            margin: 0 auto;
        }

        h1 {
            color: #1a1a1a;
            font-size: 28pt;
            font-weight: bold;
            margin-top: 0;
            margin-bottom: 0.5em;
            padding-bottom: 0.3em;
            border-bottom: 3px solid #2c5aa0;
            page-break-after: avoid;
        }

        h2 {
            color: #2c5aa0;
            font-size: 20pt;
            font-weight: bold;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            page-break-after: avoid;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 0.2em;
        }

        h3 {
            color: #34495e;
            font-size: 16pt;
            font-weight: bold;
            margin-top: 1.2em;
            margin-bottom: 0.5em;
            page-break-after: avoid;
        }

        h4 {
            color: #555;
            font-size: 13pt;
            font-weight: bold;
            margin-top: 1em;
            margin-bottom: 0.5em;
            page-break-after: avoid;
        }

        p {
            margin-bottom: 0.8em;
            text-align: justify;
        }

        strong {
            color: #1a1a1a;
            font-weight: bold;
        }

        em {
            font-style: italic;
        }

        code {
            background-color: #f5f5f5;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 2px 5px;
            font-family: 'Courier New', monospace;
            font-size: 9pt;
            color: #c7254e;
        }

        pre {
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-left: 4px solid #2c5aa0;
            border-radius: 4px;
            padding: 12px;
            margin: 1em 0;
            overflow-x: auto;
            page-break-inside: avoid;
        }

        pre code {
            background-color: transparent;
            border: none;
            padding: 0;
            color: #333;
            font-size: 9pt;
            line-height: 1.4;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
            page-break-inside: avoid;
        }

        th {
            background-color: #2c5aa0;
            color: white;
            font-weight: bold;
            padding: 10px;
            text-align: left;
            border: 1px solid #ddd;
        }

        td {
            padding: 8px;
            border: 1px solid #ddd;
        }

        tr:nth-child(even) {
            background-color: #f9f9f9;
        }

        tr:hover {
            background-color: #f5f5f5;
        }

        ul, ol {
            margin: 0.5em 0 1em 1.5em;
            padding-left: 0;
        }

        li {
            margin-bottom: 0.3em;
        }

        blockquote {
            border-left: 4px solid #2c5aa0;
            padding-left: 15px;
            margin-left: 0;
            color: #666;
            font-style: italic;
        }

        hr {
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 2em 0;
        }

        .title-page {
            text-align: center;
            padding-top: 30%;
            page-break-after: always;
        }

        .title-page h1 {
            font-size: 32pt;
            border-bottom: none;
            margin-bottom: 0.3em;
        }

        .subtitle {
            font-size: 16pt;
            color: #666;
            margin-bottom: 2em;
        }

        .metadata {
            font-size: 12pt;
            color: #888;
            margin-top: 3em;
        }

        /* Checkmarks for lists */
        li::marker {
            color: #2c5aa0;
            font-weight: bold;
        }

        /* Page breaks */
        .page-break {
            page-break-after: always;
        }

        /* Print-specific adjustments */
        @media print {
            body {
                font-size: 10pt;
            }

            h1 {
                font-size: 24pt;
            }

            h2 {
                font-size: 18pt;
            }

            h3 {
                font-size: 14pt;
            }
        }
    </style>
    """

    # Create complete HTML document
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {css}
</head>
<body>
    {html_content}
</body>
</html>
"""

    return html_template


def convert_md_to_pdf(md_file, output_pdf=None):
    """Convert markdown file to PDF"""

    md_path = Path(md_file)

    if not md_path.exists():
        print(f"Error: File '{md_file}' not found!")
        return False

    if output_pdf is None:
        output_pdf = md_path.with_suffix(".pdf")

    print(f"Reading Markdown file: {md_file}")
    md_content = md_path.read_text(encoding="utf-8")

    print("Converting Markdown to HTML...")
    html_content = create_html_with_styling(md_content)

    # Save HTML for debugging (optional)
    html_file = md_path.with_suffix(".html")
    html_file.write_text(html_content, encoding="utf-8")
    print(f"HTML file saved: {html_file}")

    print("Generating PDF...")
    try:
        from weasyprint import CSS, HTML

        # Convert HTML to PDF
        HTML(string=html_content).write_pdf(
            output_pdf,
            stylesheets=[
                CSS(
                    string="""
                @page {
                    size: A4;
                    margin: 2.5cm 2cm 2cm 2cm;
                }
            """
                )
            ],
        )

        print(f"✓ PDF created successfully: {output_pdf}")
        output_pdf_path = Path(output_pdf)
        print(f"  File size: {output_pdf_path.stat().st_size / 1024:.1f} KB")
        return True

    except ImportError:
        print("\n" + "=" * 60)
        print("ERROR: WeasyPrint is not installed!")
        print("=" * 60)
        print("\nPlease install required packages:")
        print("  pip install weasyprint markdown")
        print("\nNote: WeasyPrint requires additional system dependencies:")
        print("  - On Ubuntu/Debian: sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0")
        print("  - On macOS: brew install pango")
        print("  - On Windows: Download GTK3 runtime")
        print("\nHTML file has been generated instead: {html_file}")
        return False


def main():
    if len(sys.argv) > 1:
        md_file = sys.argv[1]
        output_pdf = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # Default to PROJECT_PROPOSAL.md
        md_file = "PROJECT_PROPOSAL.md"
        output_pdf = "RepCRec_Project_Proposal.pdf"

    print("=" * 60)
    print("Markdown to PDF Converter")
    print("=" * 60)
    print()

    success = convert_md_to_pdf(md_file, output_pdf)

    if success:
        print("\n✓ Conversion completed successfully!")
    else:
        print("\n✗ Conversion failed. Check error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
