#!/usr/bin/env python3
"""
Markdown to HTML Converter
Converts Markdown files to HTML with Mermaid diagram support
"""

import sys
import re
from pathlib import Path

import markdown


def process_mermaid_blocks(md_content):
    """Process Mermaid code blocks and convert them to HTML divs with mermaid.js"""
    # Find all mermaid code blocks (handles various formats)
    pattern = r'```mermaid\s*\n(.*?)\n```'
    
    def replace_mermaid(match):
        mermaid_code = match.group(1).strip()
        # Escape HTML special characters but preserve newlines
        mermaid_code = mermaid_code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # Create a unique ID for this mermaid diagram
        import hashlib
        diagram_id = f"mermaid-{hashlib.md5(mermaid_code.encode()).hexdigest()[:8]}"
        return f'<div class="mermaid" id="{diagram_id}">\n{mermaid_code}\n</div>'
    
    processed_content = re.sub(pattern, replace_mermaid, md_content, flags=re.DOTALL | re.MULTILINE)
    return processed_content


def create_html_with_styling(md_content, title="Document"):
    """Convert markdown to HTML with professional styling"""

    # Process Mermaid blocks first
    md_content = process_mermaid_blocks(md_content)

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
        }

        body {
            font-family: 'Georgia', 'Times New Roman', serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
            margin: 0 auto;
            padding: 20px;
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

        /* Mermaid diagram styling */
        .mermaid {
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            margin: 1em 0;
            text-align: center;
            page-break-inside: avoid;
            max-height: 500px;
            overflow: auto;
        }

        .mermaid svg {
            max-width: 100%;
            height: auto;
            max-height: 480px;
        }
        
        .mermaid .nodeLabel,
        .mermaid .edgeLabel {
            font-size: 11px !important;
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

            .mermaid {
                page-break-inside: avoid;
            }
        }
    </style>
    """

    # Create complete HTML document with Mermaid.js
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {css}
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default', 
            flowchart: {{ 
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis',
                nodeSpacing: 50,
                rankSpacing: 80,
                padding: 10
            }},
            state: {{
                nodeSpacing: 50,
                rankSpacing: 80,
                padding: 10
            }},
            themeVariables: {{
                primaryColor: '#2c5aa0',
                primaryTextColor: '#fff',
                primaryBorderColor: '#1a4480',
                lineColor: '#2c5aa0',
                secondaryColor: '#f0f0f0',
                tertiaryColor: '#ffffff',
                fontSize: '12px',
                fontFamily: 'Arial, sans-serif'
            }}
        }});
    </script>
</head>
<body>
    {html_content}
</body>
</html>
"""

    return html_template


def convert_md_to_html(md_file, output_html=None):
    """Convert markdown file to HTML"""

    md_path = Path(md_file)

    if not md_path.exists():
        print(f"Error: File '{md_file}' not found!")
        return False

    if output_html is None:
        output_html = md_path.with_suffix(".html")

    print(f"Reading Markdown file: {md_file}")
    md_content = md_path.read_text(encoding="utf-8")

    print("Converting Markdown to HTML...")
    html_content = create_html_with_styling(md_content, title=md_path.stem)

    print(f"Writing HTML file: {output_html}")
    output_path = Path(output_html)
    output_path.write_text(html_content, encoding="utf-8")

    print(f"✓ HTML file created successfully: {output_html}")
    print(f"  File size: {output_path.stat().st_size / 1024:.1f} KB")
    return True


def main():
    if len(sys.argv) > 1:
        md_file = sys.argv[1]
        output_html = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        print("Usage: python md_to_html.py <markdown_file> [output_html_file]")
        print("\nExample:")
        print("  python md_to_html.py PROJECT_PROPOSAL.md")
        print("  python md_to_html.py PROJECT_PROPOSAL.md output.html")
        sys.exit(1)

    print("=" * 60)
    print("Markdown to HTML Converter")
    print("=" * 60)
    print()

    success = convert_md_to_html(md_file, output_html)

    if success:
        print("\n✓ Conversion completed successfully!")
        print("\nNote: Open the HTML file in a browser to view rendered Mermaid diagrams.")
    else:
        print("\n✗ Conversion failed. Check error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

