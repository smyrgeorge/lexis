#!/usr/bin/env python3
"""
Markdown Translation Script

Translates markdown files using LLMs (Claude or ChatGPT).
Translated files are placed in the same directory as the source file by default.
Supports both single files and batch processing of directories.

Usage:
# Translate a single file with Claude
python scripts/translate_md.py input.md -s Spanish -t English
# Translate all .md files in a directory
python scripts/translate_md.py ./markdown-dir -s Spanish -t English
# With OpenAI
python scripts/translate_md.py input.md -p openai -s Spanish -t English
# With dictionary
python scripts/translate_md.py input.md -s Spanish -t English -d dictionary.csv
# With custom output directory
python scripts/translate_md.py input.md -s Spanish -t English -o ./translations
"""

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

default_openai_model = "gpt-4o"
default_claude_model = "claude-sonnet-4-5-20250929"


def load_csv_dictionary(csv_path: str) -> str:
    """
    Load a CSV dictionary file and format it as a string.
    Expected CSV format: source_term,target_term

    Args:
        csv_path: Path to the CSV dictionary file

    Returns:
        Formatted string with the dictionary entries
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dictionary file not found: {csv_path}")

    dictionary_entries = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        # Skip header if present
        header = next(reader, None)
        if header and header[0].lower() in ['source', 'term', 'original']:
            pass  # Header detected, already skipped
        else:
            # No header, process first row
            if header:
                dictionary_entries.append(f"{header[0]} -> {header[1]}")

        for row in reader:
            if len(row) >= 2:
                dictionary_entries.append(f"{row[0]} -> {row[1]}")

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
        source_lang: str,
        target_lang: str,
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

    return message.content[0].text


def translate_with_openai(
        text: str,
        prompt: str,
        dictionary: str,
        source_lang: str,
        target_lang: str,
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

    return response.choices[0].message.content


def translate_file(
        input_file: str,
        output_dir: str,
        provider: str,
        source_lang: str,
        target_lang: str,
        prompt: str,
        dictionary_path: Optional[str],
        model: Optional[str]
) -> None:
    """
    Translate a markdown file.

    Args:
        input_file: Path to input markdown file
        output_dir: Directory for output file
        provider: LLM provider ('claude' or 'openai')
        source_lang: Source language
        target_lang: Target language
        prompt: Translation prompt
        dictionary_path: Optional path to CSV dictionary
        model: Optional model override
    """
    # Read input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Load dictionary if provided
    dictionary = ""
    if dictionary_path:
        dictionary = load_csv_dictionary(dictionary_path)

    # Get API key
    api_key_env = "ANTHROPIC_API_KEY" if provider == "claude" else "OPENAI_API_KEY"
    api_key = os.getenv(api_key_env)

    if not api_key:
        raise ValueError(f"{api_key_env} not found in environment variables")

    # Translate
    print(f"Translating with {provider}...")
    if provider == "claude":
        translated = translate_with_claude(
            content,
            prompt,
            dictionary,
            source_lang,
            target_lang,
            api_key,
            model if model else default_claude_model
        )
    else:  # openai
        translated = translate_with_openai(
            content,
            prompt,
            dictionary,
            source_lang,
            target_lang,
            api_key,
            model if model else default_openai_model
        )

    # Generate output filename
    input_path = Path(input_file)
    output_filename = f"{input_path.stem}_{target_lang}.md"
    output_path = Path(output_dir) / output_filename

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(translated)

    print(f"✓ Translation saved to: {output_path}")


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
        default="Translate the following markdown text from {source} to {target}. Preserve all markdown formatting, structure, and syntax. Only translate the text content, not the markdown syntax itself.",
        help="Translation prompt (use {source} and {target} as placeholders)"
    )

    parser.add_argument(
        "-d", "--dictionary",
        help="Path to CSV dictionary file (format: source_term,target_term)"
    )

    parser.add_argument(
        "-m", "--model",
        help="Model to use (overrides default)"
    )

    args = parser.parse_args()

    input_path = Path(args.input_file)

    # Check if input exists
    if not input_path.exists():
        print(f"Error: {args.input_file} does not exist")
        sys.exit(1)

    # Determine if input is a file or directory
    if input_path.is_file():
        # Single file mode
        files_to_process = [input_path]
    elif input_path.is_dir():
        # Directory mode - find all .md files
        all_md_files = sorted(input_path.glob("*.md"))
        if not all_md_files:
            print(f"Error: No .md files found in directory {args.input_file}")
            sys.exit(1)

        # Filter out already translated files (those ending with _{target_lang}.md)
        files_to_process = []
        skipped = 0
        for f in all_md_files:
            # Check if file ends with _{target_lang}.md
            if f.stem.endswith(f"_{args.target_lang}"):
                skipped += 1
                continue
            # Also skip if the translated version already exists
            translated_file = f.parent / f"{f.stem}_{args.target_lang}.md"
            if translated_file.exists():
                print(f"⊘ Skipping {f.name} (translation already exists)")
                skipped += 1
                continue
            files_to_process.append(f)

        if not files_to_process:
            print(f"No files to translate. All files are already translated or skipped.")
            sys.exit(0)

        print(f"Found {len(all_md_files)} markdown files ({skipped} already translated, {len(files_to_process)} to process)")
    else:
        print(f"Error: {args.input_file} is not a file or directory")
        sys.exit(1)

    # Format prompt with languages
    formatted_prompt = args.prompt.format(
        source=args.source_lang,
        target=args.target_lang
    )

    # Process files
    processed = 0
    failed = 0

    for file_path in files_to_process:
        # If no output directory specified, use the same directory as the input file
        output_dir = args.output_dir
        if output_dir is None:
            output_dir = str(file_path.parent)

        print(f"\n{'='*80}")
        print(f"Processing: {file_path.name}")
        print(f"{'='*80}")

        try:
            translate_file(
                str(file_path),
                output_dir,
                args.provider,
                args.source_lang,
                args.target_lang,
                formatted_prompt,
                args.dictionary,
                args.model
            )
            processed += 1
        except Exception as e:
            print(f"✗ Error processing {file_path.name}: {e}")
            failed += 1

    # Summary
    if len(files_to_process) > 1:
        print(f"\n{'='*80}")
        print(f"Summary:")
        print(f"  Total files: {len(files_to_process)}")
        print(f"  Successfully translated: {processed}")
        print(f"  Failed: {failed}")
        print(f"{'='*80}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
