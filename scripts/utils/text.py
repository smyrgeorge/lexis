"""
Text processing utilities.
"""

import textwrap


def wrap_markdown_lines(content: str, width: int = 120) -> str:
    """
    Wrap markdown lines to a specified width while preserving the structure.

    Args:
        content: The Markdown content
        width: Maximum line width (default: 120)

    Returns:
        Wrapped markdown content
    """
    lines = content.split('\n')
    wrapped_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Don't wrap empty lines, headers, code blocks, or tables
        if (not line.strip() or
                line.strip().startswith('#') or
                line.strip().startswith('```') or
                line.strip().startswith('|')):
            wrapped_lines.append(line)
            i += 1
            continue

        # For regular text, collect consecutive non-empty lines into a paragraph
        paragraph_lines = [line]
        j = i + 1

        # Collect lines until we hit an empty line or special formatting
        while j < len(lines):
            next_line = lines[j]
            # Stop if we hit an empty line, header, code block, or table
            if (not next_line.strip() or
                    next_line.strip().startswith('#') or
                    next_line.strip().startswith('```') or
                    next_line.strip().startswith('|')):
                break
            paragraph_lines.append(next_line)
            j += 1

        # Join the paragraph lines and wrap them together
        paragraph_text = ' '.join(line.strip() for line in paragraph_lines)
        wrapped = textwrap.fill(
            paragraph_text,
            width=width,
            break_long_words=False,
            break_on_hyphens=False
        )
        wrapped_lines.append(wrapped)

        # Move to the next unprocessed line
        i = j

    return '\n'.join(wrapped_lines)
