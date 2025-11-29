#!/usr/bin/env python3
"""
Markdown Translation Script

Translates markdown files using LLMs (Claude or ChatGPT).
Translated files are placed in the same directory as the source file by default.
Supports both single files and batch processing of directories.

Features:
- Automatically includes context from previous/next chunks to improve translation quality
- Skips already translated files when processing directories
- Supports custom dictionaries for specialized terminology

Usage:
# Translate a single file with Claude
python scripts/translate_md.py input.md -s Spanish -t English
# Translate all .md files in a directory (with context from adjacent chunks)
python scripts/translate_md.py ./markdown-dir -s Spanish -t English
# Disable context from adjacent chunks
python scripts/translate_md.py ./markdown-dir -s Spanish -t English -c 0
# Custom context lines (default is 5)
python scripts/translate_md.py ./markdown-dir -s Spanish -t English -c 10
# With OpenAI
python scripts/translate_md.py input.md -p openai -s Spanish -t English
# With dictionary
python scripts/translate_md.py input.md -s Spanish -t English -d dictionary.txt
# With custom output directory
python scripts/translate_md.py input.md -s Spanish -t English -o ./translations
"""

import argparse
import os
import re
import sys
import time
import warnings
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from utils.term import Colors, Icons
from utils.text import wrap_markdown_lines

# Suppress Pydantic V1 compatibility warning with Python 3.14+
warnings.filterwarnings("ignore", message="Core Pydantic V1 functionality.*", category=UserWarning)

default_openai_model = "gpt-4o"
default_claude_model = "claude-sonnet-4-5-20250929"
default_prompt = """
Translate the following markdown text from {source} to {target}.
Rules:
- Preserve all markdown formatting, structure, and syntax.
- Only translate the text content, not the markdown syntax itself.
- Only output the translated text, no additional text headings (e.g., "Translation:").
"""


def load_txt_dictionary(txt_path: str) -> str:
    """
    Load a TXT dictionary file and format it as a string.
    Expected TXT format: term: translation 1, translation 2

    Args:
        txt_path: Path to the TXT dictionary file

    Returns:
        Formatted string with the dictionary entries
    """
    if not os.path.exists(txt_path):
        raise FileNotFoundError(f"Dictionary file not found: {txt_path}")

    dictionary_entries = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Validate format: term: translation 1, translation 2
            if ':' not in line:
                raise ValueError(
                    f"Invalid format in dictionary file at line {line_num}: '{line}'\n"
                    f"Expected format: 'term: translation 1, translation 2'"
                )

            term, translations = line.split(':', 1)
            term = term.strip()
            translations = translations.strip()

            if not term or not translations:
                raise ValueError(
                    f"Invalid format in dictionary file at line {line_num}: '{line}'\n"
                    f"Both term and translations must be non-empty"
                )

            dictionary_entries.append(f"{term} -> {translations}")

    if not dictionary_entries:
        return ""

    return "\n".join([
        "\n## Translation Dictionary",
        "Use the following term translations:",
        "```",
        *dictionary_entries,
        "```\n"
    ])


def translate_with_claude(
        text: str,
        prompt: str,
        dictionary: str,
        api_key: str,
        model: str = default_claude_model
) -> str:
    """Translate text using Claude API."""
    import anthropic
    from anthropic.types import MessageParam

    client = anthropic.Anthropic(api_key=api_key)
    full_prompt = f"{prompt}\n{dictionary}\n## Text to Translate:\n\n{text}"

    messages: list[MessageParam] = [
        {"role": "user", "content": full_prompt}
    ]

    message = client.messages.create(
        model=model,
        max_tokens=8000,
        messages=messages
    )

    text = message.content[0].text
    if not text or not text.strip():
        raise ValueError("API returned empty translation")
    return text


def translate_with_openai(
        text: str,
        prompt: str,
        dictionary: str,
        api_key: str,
        model: str = default_openai_model
) -> str:
    """Translate text using OpenAI API."""
    from openai import OpenAI
    from openai.types.chat import ChatCompletionUserMessageParam

    client = OpenAI(api_key=api_key)
    full_prompt = f"{prompt}\n{dictionary}\n## Text to Translate:\n\n{text}"

    messages: list[ChatCompletionUserMessageParam] = [
        {"role": "user", "content": full_prompt}
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    content = response.choices[0].message.content
    if not content or not content.strip():
        raise ValueError("API returned empty translation")
    return content


def natural_sort_key(path: Path) -> list:
    """
    Generate a sort key for natural sorting of file names.
    This ensures that file10.md comes after file2.md, not before.

    Args:
        path: Path object to generate a sort key for

    Returns:
        List of strings and integers for natural sorting
    """
    return [int(c) if c.isdigit() else c.lower()
            for c in re.split(r'(\d+)', str(path.name))]


def get_file_lines(file_path: str, num_lines: int, from_end: bool = False) -> list[str]:
    """
    Get the first or last N lines from a file.

    Args:
        file_path: Path to the file
        num_lines: Number of lines to get
        from_end: If True, get last N lines; if False, get first N lines

    Returns:
        List of lines
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if from_end:
                return lines[-num_lines:] if len(lines) >= num_lines else lines
            else:
                return lines[:num_lines] if len(lines) >= num_lines else lines
    except Exception as e:
        print(f"Warning: Could not read context from {file_path}: {e}")
        return []


# noinspection PyUnusedLocal
def translate_file(
        input_file: str,
        output_dir: str,
        provider: str,
        source_lang: str,
        target_lang: str,
        prompt: str,
        dictionary_path: Optional[str],
        model: Optional[str],
        prev_file: Optional[str] = None,
        next_file: Optional[str] = None,
        context_lines: int = 5,
        line_width: Optional[int] = 120,
        wrap_lines: bool = True
) -> None:
    """
    Translate a Markdown file.

    Args:
        input_file: Path to input markdown file
        output_dir: Directory for output file
        provider: LLM provider ('claude' or 'openai')
        source_lang: Source language
        target_lang: Target language
        prompt: Translation prompt
        dictionary_path: Optional path to TXT dictionary
        model: Optional model override
        prev_file: Optional path to previous chunk file
        next_file: Optional path to next chunk file
        context_lines: Number of lines to include from prev/next chunks for context
        line_width: Maximum line width for wrapping (default: 120)
        wrap_lines: Whether to wrap lines (default: True)
    """
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Build context from previous and next chunks
    context_prefix = ""
    context_suffix = ""

    if prev_file and context_lines > 0:
        prev_lines = get_file_lines(prev_file, context_lines, from_end=True)
        if prev_lines:
            context_prefix = (
                "---\n"
                "## CONTEXT FROM PREVIOUS CHUNK (FOR REFERENCE ONLY - DO NOT TRANSLATE THIS SECTION)\n"
                "The following lines are from the previous chunk to provide context.\n"
                "DO NOT translate this section, only use it for context.\n"
                "---\n\n"
                + "".join(prev_lines) +
                "\n---\n"
                "## END OF PREVIOUS CHUNK CONTEXT\n"
                "---\n\n"
            )

    if next_file and context_lines > 0:
        next_lines = get_file_lines(next_file, context_lines, from_end=False)
        if next_lines:
            context_suffix = (
                "\n---\n"
                "## CONTEXT FROM NEXT CHUNK (FOR REFERENCE ONLY - DO NOT TRANSLATE THIS SECTION)\n"
                "The following lines are from the next chunk to provide context.\n"
                "DO NOT translate this section, only use it for context.\n"
                "---\n\n"
                + "".join(next_lines) +
                "\n---\n"
                "## END OF NEXT CHUNK CONTEXT\n"
                "---\n"
            )

    # Add the main content marker if we have any context
    if context_prefix or context_suffix:
        content_with_context = (
            context_prefix +
            "---\n## MAIN CONTENT TO TRANSLATE\n"
            "Translate ONLY this section below:\n---\n\n" +
            content +
            "\n---\n## END OF MAIN CONTENT\n---\n" +
            context_suffix
        )
    else:
        content_with_context = content

    # Load dictionary if provided
    dictionary = ""
    if dictionary_path:
        dictionary = load_txt_dictionary(dictionary_path)

    # Get API key
    api_key_env = "ANTHROPIC_API_KEY" if provider == "claude" else "OPENAI_API_KEY"
    api_key = os.getenv(api_key_env)

    if not api_key:
        raise ValueError(f"{api_key_env} not found in environment variables")

    # Translate
    if context_prefix or context_suffix:
        print(f"  {Colors.CYAN}{Icons.GLOBE} Translating with {Colors.MAGENTA}{provider}{Colors.RESET} {Colors.GRAY}(with context from adjacent chunks){Colors.RESET}...")
    else:
        print(f"  {Colors.CYAN}{Icons.GLOBE} Translating with {Colors.MAGENTA}{provider}{Colors.RESET}...")
    start_time = time.time()

    if provider == "claude":
        translated = translate_with_claude(
            content_with_context,
            prompt,
            dictionary,
            api_key,
            model if model else default_claude_model
        )
    else:  # openai
        translated = translate_with_openai(
            content_with_context,
            prompt,
            dictionary,
            api_key,
            model if model else default_openai_model
        )

    elapsed_time = time.time() - start_time

    # Wrap lines if enabled
    if wrap_lines and line_width:
        translated = wrap_markdown_lines(translated, line_width)

    # Generate output filename
    input_path = Path(input_file)
    output_filename = f"{input_path.stem}_{target_lang}.md"
    output_path = Path(output_dir) / output_filename

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(translated)

    print(f"  {Colors.GREEN}{Icons.SUCCESS} Translation saved to:{Colors.RESET} {Colors.CYAN}{output_path}{Colors.RESET} {Colors.GRAY}({Icons.CLOCK} {elapsed_time:.2f}s){Colors.RESET}")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Translate markdown files using LLMs",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "input_file",
        help="Path to input markdown file or directory containing markdown files"
    )

    parser.add_argument(
        "-o", "--output-dir",
        default=None,
        help="Output directory for translated files (default: same directory as input file)"
    )

    parser.add_argument(
        "-p", "--provider",
        choices=["claude", "openai"],
        default="claude",
        help="LLM provider to use"
    )

    parser.add_argument(
        "-s", "--source-lang",
        required=True,
        help="Source language (e.g., 'Spanish', 'es')"
    )

    parser.add_argument(
        "-t", "--target-lang",
        required=True,
        help="Target language (e.g., 'English', 'en')"
    )

    parser.add_argument(
        "--prompt",
        default=default_prompt,
        help="Translation prompt (use {source} and {target} as placeholders)"
    )

    parser.add_argument(
        "--style",
        default=None,
        help="Style remarks for the translation (e.g., 'Use formal tone', 'Keep it concise')"
    )

    parser.add_argument(
        "-d", "--dictionary",
        help="Path to TXT dictionary file (format: term: translation 1, translation 2)"
    )

    parser.add_argument(
        "-m", "--model",
        help="Model to use (overrides default)"
    )

    parser.add_argument(
        "-c", "--context-lines",
        type=int,
        default=5,
        help="Number of lines from previous/next chunks to include as context (default: 5, set to 0 to disable)"
    )

    parser.add_argument(
        "--line-width",
        type=int,
        default=120,
        help="Maximum line width for wrapping (default: 120)"
    )

    parser.add_argument(
        "--no-wrap",
        action="store_true",
        help="Disable line wrapping"
    )

    args = parser.parse_args()

    input_path = Path(args.input_file)

    # Check if input exists
    if not input_path.exists():
        print(f"{Colors.RED}{Icons.ERROR} Error:{Colors.RESET} {args.input_file} does not exist")
        sys.exit(1)

    # Determine if the input is a file or directory
    if input_path.is_file():
        # Single file mode
        files_to_process = [input_path]
    elif input_path.is_dir():
        # Directory mode - find all .md files
        all_md_files = sorted(input_path.glob("*.md"), key=natural_sort_key)
        if not all_md_files:
            print(f"{Colors.RED}{Icons.ERROR} Error:{Colors.RESET} No .md files found in directory {args.input_file}")
            sys.exit(1)

        # Filter out already translated files (those ending with _{target_lang}.md)
        files_to_process = []
        skipped = 0
        for f in all_md_files:
            # Check if the file ends with _{target_lang}.md
            if f.stem.endswith(f"_{args.target_lang}"):
                skipped += 1
                continue
            # Also skip if the translated version already exists
            translated_file = f.parent / f"{f.stem}_{args.target_lang}.md"
            if translated_file.exists():
                print(f"{Colors.YELLOW}{Icons.SKIP} Skipping:{Colors.RESET} {Colors.DIM}{f.name}{Colors.RESET} {Colors.GRAY}(translation already exists){Colors.RESET}")
                skipped += 1
                continue
            files_to_process.append(f)

        if not files_to_process:
            print(f"{Colors.YELLOW}{Icons.INFO} Info:{Colors.RESET} No files to translate. All files are already translated or skipped.")
            sys.exit(0)

        print(
            f"{Colors.CYAN}{Icons.INFO} Found:{Colors.RESET} {Colors.BOLD}{len(all_md_files)}{Colors.RESET} markdown files "
            f"({Colors.GRAY}{skipped} already translated{Colors.RESET}, {Colors.GREEN}{len(files_to_process)} to process{Colors.RESET})")
    else:
        print(f"{Colors.RED}{Icons.ERROR} Error:{Colors.RESET} {args.input_file} is not a file or directory")
        sys.exit(1)

    # Format prompt with languages
    formatted_prompt = args.prompt.format(
        source=args.source_lang,
        target=args.target_lang
    )

    # Append style remarks if provided
    if args.style:
        formatted_prompt += f"\nStyle Guidelines:\n{args.style}"

    # Print the prompt for user preview
    print(f"\n{Colors.CYAN}{'─' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Icons.SPARKLES} Translation Prompt Preview{Colors.RESET}")
    print(f"{Colors.CYAN}{'─' * 80}{Colors.RESET}")
    print(f"{Colors.WHITE}{formatted_prompt}{Colors.RESET}")
    print(f"{Colors.CYAN}{'─' * 80}{Colors.RESET}\n")

    # Show cost estimation for batch processing
    if len(files_to_process) > 1:
        total_chars = 0
        for file_path in files_to_process:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    total_chars += len(f.read())
            except Exception:
                pass  # Skip files that can't be read

        est_tokens = total_chars // 4  # Estimate: 1 token ≈ 4 characters

        print(f"\n{Colors.BLUE}{'─' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Icons.CHART} Batch Translation Estimate{Colors.RESET}")
        print(f"{Colors.BLUE}{'─' * 80}{Colors.RESET}")
        print(f"   {Colors.CYAN}Files to process:{Colors.RESET} {Colors.BOLD}{len(files_to_process)}{Colors.RESET}")
        print(f"   {Colors.CYAN}Total characters:{Colors.RESET} {Colors.BOLD}{total_chars:,}{Colors.RESET}")
        print(f"   {Colors.CYAN}Estimated input tokens:{Colors.RESET} {Colors.BOLD}~{est_tokens:,}{Colors.RESET}")
        print(f"   {Colors.CYAN}Provider:{Colors.RESET} {Colors.MAGENTA}{args.provider}{Colors.RESET}")
        print(f"   {Colors.CYAN}Model:{Colors.RESET} {Colors.MAGENTA}{args.model if args.model else (default_claude_model if args.provider == 'claude' else default_openai_model)}{Colors.RESET}")
        print(f"\n   {Colors.GRAY}{Icons.INFO} Note: Actual costs depend on output length and provider pricing.{Colors.RESET}")
        print(f"   {Colors.GRAY}{Icons.INFO} Context from adjacent chunks will add additional tokens.{Colors.RESET}")
        print(f"{Colors.BLUE}{'─' * 80}{Colors.RESET}")

    # Process files
    processed = 0
    failed = 0

    for idx, file_path in enumerate(files_to_process):
        # If no output directory specified, use the same directory as the input file
        output_dir = args.output_dir
        if output_dir is None:
            output_dir = str(file_path.parent)

        # Read the current file for stats
        with open(file_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
            current_lines = current_content.split('\n')
            # Get first 5 lines for preview
            current_first_lines = current_lines[:5] if len(current_lines) >= 5 else current_lines
            current_char_count = len(current_content)

        # Determine previous and next files for context
        # Look at ALL files in the directory, not just files_to_process
        prev_file = None
        next_file = None
        prev_last_lines = []
        next_first_lines = []

        if args.context_lines > 0 and input_path.is_dir():
            # Get all .md files (including already translated ones) sorted
            all_source_files = sorted([
                f for f in input_path.glob("*.md")
                if not f.stem.endswith(f"_{args.target_lang}")
            ], key=natural_sort_key)

            # Find the current file's position in the complete list
            try:
                current_idx = all_source_files.index(file_path)

                # Previous file (if not first)
                if current_idx > 0:
                    prev_file = str(all_source_files[current_idx - 1])
                    try:
                        with open(prev_file, 'r', encoding='utf-8') as f:
                            # Get the LAST 5 non-empty lines from the previous chunk
                            all_lines = [line.strip() for line in f.readlines() if line.strip()]
                            prev_last_lines = all_lines[-5:] if len(all_lines) >= 5 else all_lines
                    except Exception:
                        pass

                # Next file (if not last)
                if current_idx < len(all_source_files) - 1:
                    next_file = str(all_source_files[current_idx + 1])
                    try:
                        with open(next_file, 'r', encoding='utf-8') as f:
                            # Get the FIRST 5 lines from the next chunk
                            all_lines = f.readlines()
                            next_first_lines = [line.strip() for line in all_lines[:5]]
                    except Exception:
                        pass
            except ValueError:
                # File wasn't found in the list, skip context
                pass

        print(f"\n{Colors.GREEN}{'─' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Icons.FILE} [{idx + 1}/{len(files_to_process)}] Processing:{Colors.RESET} {Colors.CYAN}{file_path.name}{Colors.RESET}")
        print(f"{Colors.GREEN}{'─' * 80}{Colors.RESET}")
        print(f"  {Colors.DIM}Characters:{Colors.RESET} {Colors.BOLD}{current_char_count:,}{Colors.RESET}")
        print(f"  {Colors.DIM}First lines:{Colors.RESET}")
        for i, line in enumerate(current_first_lines, 1):
            truncated_line = line[:75] + '...' if len(line) > 75 else line
            print(f"    {Colors.GRAY}{i}.{Colors.RESET} {truncated_line}")
        if prev_file and args.context_lines > 0:
            print(f"\n  {Colors.BLUE}{Icons.FILE} Previous chunk:{Colors.RESET} {Colors.DIM}{Path(prev_file).name}{Colors.RESET}")
            if prev_last_lines:
                print(f"     {Colors.DIM}Last lines:{Colors.RESET}")
                for i, line in enumerate(prev_last_lines, 1):
                    truncated_line = line[:75] + '...' if len(line) > 75 else line
                    print(f"       {Colors.GRAY}{i}.{Colors.RESET} {Colors.DIM}{truncated_line}{Colors.RESET}")
        if next_file and args.context_lines > 0:
            print(f"\n  {Colors.BLUE}{Icons.FILE} Next chunk:{Colors.RESET} {Colors.DIM}{Path(next_file).name}{Colors.RESET}")
            if next_first_lines:
                print(f"     {Colors.DIM}First lines:{Colors.RESET}")
                for i, line in enumerate(next_first_lines, 1):
                    truncated_line = line[:75] + '...' if len(line) > 75 else line
                    print(f"       {Colors.GRAY}{i}.{Colors.RESET} {Colors.DIM}{truncated_line}{Colors.RESET}")
        print(f"{Colors.GREEN}{'─' * 80}{Colors.RESET}")

        try:
            translate_file(
                str(file_path),
                output_dir,
                args.provider,
                args.source_lang,
                args.target_lang,
                formatted_prompt,
                args.dictionary,
                args.model,
                prev_file,
                next_file,
                args.context_lines,
                args.line_width,
                not args.no_wrap
            )
            processed += 1
        except Exception as e:
            print(f"  {Colors.RED}{Icons.ERROR} Error processing {Colors.CYAN}{file_path.name}{Colors.RESET}: {Colors.RED}{e}{Colors.RESET}")
            failed += 1

    # Summary
    if len(files_to_process) > 1:
        print(f"\n{Colors.MAGENTA}{'═' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Icons.CHART} Summary{Colors.RESET}")
        print(f"{Colors.MAGENTA}{'═' * 80}{Colors.RESET}")
        print(f"  {Colors.CYAN}Total files:{Colors.RESET} {Colors.BOLD}{len(files_to_process)}{Colors.RESET}")
        print(f"  {Colors.GREEN}{Icons.SUCCESS} Successfully translated:{Colors.RESET} {Colors.BOLD}{Colors.GREEN}{processed}{Colors.RESET}")
        if failed > 0:
            print(f"  {Colors.RED}{Icons.ERROR} Failed:{Colors.RESET} {Colors.BOLD}{Colors.RED}{failed}{Colors.RESET}")
        print(f"{Colors.MAGENTA}{'═' * 80}{Colors.RESET}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Translation cancelled by user (Ctrl+C)")
        sys.exit(130)  # Standard exit code for SIGINT
