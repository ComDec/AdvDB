#!/bin/bash
# Convert all markdown documentation to PDF

echo "=================================================="
echo "Converting RepCRec Documentation to PDF"
echo "=================================================="
echo ""

# Main project proposal (English)
echo "1. Converting PROJECT_PROPOSAL.md..."
python3 md_to_pdf.py PROJECT_PROPOSAL.md RepCRec_Project_Proposal.pdf
echo ""

# Algorithm implementation summary (Chinese)
echo "2. Converting 算法实现总结.md..."
python3 md_to_pdf.py 算法实现总结.md 算法实现总结.pdf
echo ""

# Main README
echo "3. Converting README.md..."
python3 md_to_pdf.py README.md RepCRec_README.pdf
echo ""

# Project summary
echo "4. Converting PROJECT_SUMMARY.md..."
python3 md_to_pdf.py PROJECT_SUMMARY.md RepCRec_Project_Summary.pdf
echo ""

echo "=================================================="
echo "Conversion Complete!"
echo "=================================================="
echo ""
echo "Generated PDF files:"
ls -lh *.pdf 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'
echo ""
echo "Generated HTML files (intermediate):"
ls -lh *.html 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'
