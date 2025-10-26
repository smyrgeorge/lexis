#!/usr/bin/env bash

# Usage:
#
# # Basic usage (markdown files will be placed in the same directory as the PDFs)
# ./scripts/batch_convert_pdf_to_md.sh ./pdfs
#
# # Override docling options
# DOCLING_OPTIONS_OVERRIDE='--to md --image-export-mode base64' ./scripts/batch_convert_pdf_to_md.sh ./pdfs
#
# Default docling command:
# The script runs: docling <file.pdf> --to md --no-tables --image-export-mode placeholder --output <pdf_directory>
# Script to process all PDFs in a directory with docling
# Markdown files are placed in the same directory as the source PDFs
# Usage: ./batch_convert_pdf_to_md.sh <directory_path>

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default docling options - modify these as needed
DOCLING_OPTIONS=(--to md --no-tables --image-export-mode placeholder)

# Function to display usage
usage() {
    echo "Usage: $0 <directory_path>"
    echo ""
    echo "Arguments:"
    echo "  directory_path    : Directory containing PDF files to process"
    echo ""
    echo "Note:"
    echo "  Markdown files will be placed in the same directory as the source PDFs"
    echo ""
    echo "Environment variables:"
    echo "  DOCLING_OPTIONS_OVERRIDE : Override default docling options"
    echo "                             (default: --to md --no-tables --image-export-mode placeholder)"
    echo ""
    echo "Example:"
    echo "  $0 ./pdfs"
    echo "  DOCLING_OPTIONS_OVERRIDE='--to md --image-export-mode base64' $0 ./pdfs"
    exit 1
}

# Check if directory argument is provided
if [ $# -lt 1 ]; then
    echo -e "${RED}Error: Directory path is required${NC}"
    usage
fi

INPUT_DIR="$1"

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo -e "${RED}Error: Directory '$INPUT_DIR' does not exist${NC}"
    exit 1
fi

# Check if docling is installed
if ! command -v docling &> /dev/null; then
    echo -e "${RED}Error: docling is not installed${NC}"
    echo "Install it with: pip install docling"
    exit 1
fi

# Allow override of docling options via environment variable
if [ -n "$DOCLING_OPTIONS_OVERRIDE" ]; then
    read -ra DOCLING_OPTIONS <<< "$DOCLING_OPTIONS_OVERRIDE"
fi

echo -e "${GREEN}Processing PDFs in: $INPUT_DIR${NC}"
echo -e "${GREEN}Output: Markdown files will be placed in the same directory as the PDFs${NC}"
echo -e "${GREEN}Docling options: ${DOCLING_OPTIONS[*]}${NC}"
echo ""

# Counter for processed files
processed=0
failed=0

# Find and process all PDF files (sorted)
while IFS= read -r -d '' pdf_file; do
    filename=$(basename "$pdf_file")
    pdf_dir=$(dirname "$pdf_file")
    echo -e "${YELLOW}Processing: $filename${NC}"

    # Run docling command - output to the same directory as the PDF
    if docling "$pdf_file" "${DOCLING_OPTIONS[@]}" --output "$pdf_dir"; then
        echo -e "${GREEN}✓ Successfully processed: $filename${NC}"
        ((processed++))
    else
        echo -e "${RED}✗ Failed to process: $filename${NC}"
        ((failed++))
    fi
    echo ""
done < <(find "$INPUT_DIR" -maxdepth 1 -type f -name "*.pdf" -print0 | sort -z)

# Summary
echo "========================================"
echo -e "${GREEN}Total processed: $processed${NC}"
if [ $failed -gt 0 ]; then
    echo -e "${RED}Total failed: $failed${NC}"
fi
echo "========================================"

exit 0
