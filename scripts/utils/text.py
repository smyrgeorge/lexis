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

    for line in lines:
        # Don't wrap empty lines, headers, code blocks, or lines that are already short
        if (not line.strip() or
                line.strip().startswith('#') or
                line.strip().startswith('```') or
                line.strip().startswith('|') or  # Tables
                len(line) <= width):
            wrapped_lines.append(line)
        else:
            # Wrap long lines
            wrapped = textwrap.fill(
                line,
                width=width,
                break_long_words=False,
                break_on_hyphens=False
            )
            wrapped_lines.append(wrapped)

    return '\n'.join(wrapped_lines)
