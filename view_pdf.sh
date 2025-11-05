#!/bin/bash
# Quick PDF viewer script

if [ $# -eq 0 ]; then
    echo "Available PDF files:"
    echo "=================="
    ls -lh *.pdf 2>/dev/null | awk '{print "  " NR ". " $9 " (" $5 ")"}'
    echo ""
    echo "Usage: $0 <pdf_file>"
    echo "Example: $0 RepCRec_Project_Proposal.pdf"
    exit 0
fi

PDF_FILE="$1"

if [ ! -f "$PDF_FILE" ]; then
    echo "Error: File '$PDF_FILE' not found!"
    exit 1
fi

echo "Opening: $PDF_FILE"
echo "File size: $(ls -lh "$PDF_FILE" | awk '{print $5}')"
echo ""

# Try different PDF viewers
if command -v evince &> /dev/null; then
    evince "$PDF_FILE" &
elif command -v okular &> /dev/null; then
    okular "$PDF_FILE" &
elif command -v xdg-open &> /dev/null; then
    xdg-open "$PDF_FILE" &
elif command -v open &> /dev/null; then
    open "$PDF_FILE" &
else
    echo "No PDF viewer found. Please open manually:"
    echo "  File: $(realpath "$PDF_FILE")"
fi
