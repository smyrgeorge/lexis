"""
Text processing utilities.
"""

import re
import textwrap

_LIST_ITEM_RE = re.compile(r'^(\s*)([-*+]|\d+\.)\s')


def _is_special_line(line: str) -> bool:
    stripped = line.strip()
    return (
        not stripped or
        stripped.startswith('#') or
        stripped.startswith('```') or
        stripped.startswith('|') or
        bool(_LIST_ITEM_RE.match(line))
    )


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
        stripped = line.strip()

        # Empty lines
        if not stripped:
            wrapped_lines.append(line)
            i += 1
            continue

        # Headers, code blocks, tables — keep as-is
        if (stripped.startswith('#') or
                stripped.startswith('```') or
                stripped.startswith('|')):
            wrapped_lines.append(line)
            i += 1
            continue

        # Blockquotes — collect consecutive lines with the same prefix and re-wrap
        if stripped.startswith('>'):
            prefix_match = re.match(r'^(>\s*)', line)
            prefix = prefix_match.group(1) if prefix_match else '> '
            content_part = line[len(prefix):]

            # Keep directives (e.g. [!NOTE]) as-is
            if content_part.strip().startswith('[!'):
                wrapped_lines.append(line)
                i += 1
                continue

            # Collect consecutive blockquote lines with the same prefix
            block_parts = [content_part]
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                if not next_line.strip().startswith('>'):
                    break
                next_prefix_match = re.match(r'^(>\s*)', next_line)
                next_prefix = next_prefix_match.group(1) if next_prefix_match else '> '
                if next_prefix != prefix:
                    break
                next_content = next_line[len(next_prefix):]
                if next_content.strip().startswith('[!'):
                    break
                block_parts.append(next_content)
                j += 1

            joined = ' '.join(part.strip() for part in block_parts if part.strip())
            wrapped = textwrap.fill(
                joined,
                width=width - len(prefix),
                break_long_words=False,
                break_on_hyphens=False
            )
            for wline in wrapped.split('\n'):
                wrapped_lines.append(prefix + wline)
            i = j
            continue

        # List items — collect item line + indented continuation lines, then re-wrap
        m = _LIST_ITEM_RE.match(line)
        if m:
            leading = m.group(1)
            marker = m.group(2)
            subsequent_indent = ' ' * (len(leading) + len(marker) + 1)

            # Collect indented continuation lines that belong to this item
            full_text = line.rstrip()
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                if not next_line.strip():
                    break
                if _LIST_ITEM_RE.match(next_line):
                    break
                if next_line.strip().startswith('>'):
                    break
                if next_line.startswith(' ') or next_line.startswith('\t'):
                    full_text += ' ' + next_line.strip()
                    j += 1
                else:
                    break

            wrapped = textwrap.fill(
                full_text,
                width=width,
                subsequent_indent=subsequent_indent,
                break_long_words=False,
                break_on_hyphens=False
            )
            wrapped_lines.append(wrapped)
            i = j
            continue

        # Regular prose — collect consecutive non-special lines and re-wrap
        paragraph_lines = [line]
        j = i + 1
        while j < len(lines):
            next_line = lines[j]
            if _is_special_line(next_line) or next_line.strip().startswith('>'):
                break
            paragraph_lines.append(next_line)
            j += 1

        paragraph_text = ' '.join(l.strip() for l in paragraph_lines)
        wrapped = textwrap.fill(
            paragraph_text,
            width=width,
            break_long_words=False,
            break_on_hyphens=False
        )
        wrapped_lines.append(wrapped)
        i = j

    return '\n'.join(wrapped_lines)
