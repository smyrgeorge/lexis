#!/usr/bin/env python3
"""
Chunk a markdown file into smaller pieces.

Supports chunking by:
- Heading level (default)
- Character count
- Token count (approximate)

# By heading (default - splits on # and ## headings)
python chunk_md.py out/estado-del-poder.md

# By heading level (e.g., split only on # headings)
python chunk_md.py out/estado-del-poder.md --heading-level 1

# By character count (5000 chars per chunk, 200 char overlap)
python chunk_md.py out/estado-del-poder.md --mode chars --max-chars 5000

# By token count (approximate, ~1000 tokens per chunk)
python chunk_md.py out/estado-del-poder.md --mode tokens --max-tokens 1000

# Custom output directory
python chunk_md.py out/estado-del-poder.md -o chunks/
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


def chunk_by_heading(content: str, max_level: int = 2) -> List[Tuple[str, str]]:
    """
    Split markdown by heading level.

    Args:
        content: Markdown content
        max_level: Maximum heading level to split on (1-6)

    Returns:
        List of (title, content) tuples
    """
    # Pattern to match headings up to max_level
    pattern = rf'^(#{{{1},{max_level}}})\s+(.+)$'

    chunks = []
    current_title = "Introduction"
    current_content = []

    lines = content.split('\n')

    for line in lines:
        match = re.match(pattern, line, re.MULTILINE)
        if match:
            # Save previous chunk
            if current_content:
                chunks.append((current_title, '\n'.join(current_content).strip()))

            # Start new chunk
            current_title = match.group(2).strip()
            current_content = [line]
        else:
            current_content.append(line)

    # Save last chunk
    if current_content:
        chunks.append((current_title, '\n'.join(current_content).strip()))

    return chunks


def chunk_by_size(content: str, max_chars: int = 5000, overlap: int = 200) -> List[str]:
    """
    Split markdown by character count with overlap.

    Args:
        content: Markdown content
        max_chars: Maximum characters per chunk
        overlap: Number of characters to overlap between chunks

    Returns:
        List of content chunks
    """
    chunks = []
    start = 0

    while start < len(content):
        end = start + max_chars

        # Try to break at a paragraph boundary
        if end < len(content):
            # Look for double newline (paragraph break) near the end
            search_start = max(start + max_chars - 200, start)
            para_break = content.rfind('\n\n', search_start, end)

            if para_break != -1:
                end = para_break + 2

        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position with overlap
        start = end - overlap if end < len(content) else end

    return chunks


def chunk_by_tokens(content: str, max_tokens: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split markdown by approximate token count.
    Approximation: 1 token ≈ 4 characters

    Args:
        content: Markdown content
        max_tokens: Maximum tokens per chunk
        overlap: Number of tokens to overlap

    Returns:
        List of content chunks
    """
    # Rough approximation: 1 token ≈ 4 characters
    max_chars = max_tokens * 4
    overlap_chars = overlap * 4

    return chunk_by_size(content, max_chars, overlap_chars)


def save_chunks(chunks: List[Tuple[str, str]] | List[str], output_dir: Path, base_name: str):
    """Save chunks to separate files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, chunk in enumerate(chunks, 1):
        if isinstance(chunk, tuple):
            title, content = chunk
            # Sanitize title for filename
            safe_title = re.sub(r'[^\w\s-]', '', title)
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            filename = f"{i:03d}-{safe_title[:50]}.md"

            # Add title as heading if not present
            if not content.startswith('#'):
                content = f"# {title}\n\n{content}"
        else:
            filename = f"{i:03d}-chunk.md"
            content = chunk

        output_file = output_dir / filename
        output_file.write_text(content, encoding='utf-8')
        print(f"Created: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Chunk markdown files into smaller pieces"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Input markdown file"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output directory (default: input_file_chunks/)"
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["heading", "chars", "tokens"],
        default="heading",
        help="Chunking mode (default: heading)"
    )
    parser.add_argument(
        "--heading-level",
        type=int,
        default=2,
        choices=range(1, 7),
        help="Maximum heading level for heading mode (default: 2)"
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=5000,
        help="Maximum characters per chunk for chars mode (default: 5000)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1000,
        help="Maximum tokens per chunk for tokens mode (default: 1000)"
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=200,
        help="Overlap size in chars/tokens for size-based chunking (default: 200)"
    )

    args = parser.parse_args()

    # Read input file
    if not args.input_file.exists():
        print(f"Error: File not found: {args.input_file}")
        return 1

    content = args.input_file.read_text(encoding='utf-8')

    # Determine output directory
    if args.output:
        output_dir = args.output
    else:
        output_dir = args.input_file.parent / f"{args.input_file.stem}_chunks"

    chunks = []

    # Chunk content
    if args.mode == "heading":
        chunks = chunk_by_heading(content, args.heading_level)
        print(f"Split into {len(chunks)} chunks by heading level {args.heading_level}")
    elif args.mode == "chars":
        chunks = chunk_by_size(content, args.max_chars, args.overlap)
        print(f"Split into {len(chunks)} chunks by character count (~{args.max_chars} chars each)")
    elif args.mode == "tokens":
        chunks = chunk_by_tokens(content, args.max_tokens, args.overlap)
        print(f"Split into {len(chunks)} chunks by token count (~{args.max_tokens} tokens each)")

    # Save chunks
    save_chunks(chunks, output_dir, args.input_file.stem)
    print(f"\nAll chunks saved to: {output_dir}")

    return 0


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Translation cancelled by user (Ctrl+C)")
        sys.exit(130)  # Standard exit code for SIGINT
