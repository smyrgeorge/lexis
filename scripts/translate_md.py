#!/usr/bin/env python3
"""
Markdown Translation Script

Translates markdown files using LLMs (Claude or ChatGPT).
"""

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv not found. Install it with: pip install python-dotenv")
    sys.exit(1)


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
    model: str = "claude-3-5-sonnet-20241022"
) -> str:
    """Translate text using Claude API."""
    try:
        import anthropic
    except ImportError:
        print("Error: anthropic package not found. Install it with: pip install anthropic")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    full_prompt = f"{prompt}\n{dictionary}\n## Text to Translate\n\n{text}"

    message = client.messages.create(
        model=model,
        max_tokens=8000,
        messages=[
            {"role": "user", "content": full_prompt}
        ]
    )

    return message.content[0].text


def translate_with_openai(
    text: str,
    prompt: str,
    dictionary: str,
    source_lang: str,
    target_lang: str,
    api_key: str,
    model: str = "gpt-4o"
) -> str:
    """Translate text using OpenAI API."""
    try:
        from openai import OpenAI
    except ImportError:
        print("Error: openai package not found. Install it with: pip install openai")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    full_prompt = f"{prompt}\n{dictionary}\n## Text to Translate\n\n{text}"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": full_prompt}
        ]
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
            content, prompt, dictionary, source_lang, target_lang, api_key,
            model if model else "claude-3-5-sonnet-20241022"
        )
    else:  # openai
        translated = translate_with_openai(
            content, prompt, dictionary, source_lang, target_lang, api_key,
            model if model else "gpt-4o"
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
        help="Path to input markdown file"
    )

    parser.add_argument(
        "-o", "--output-dir",
        default="./translations",
        help="Output directory for translated files"
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

    # Format prompt with languages
    formatted_prompt = args.prompt.format(
        source=args.source_lang,
        target=args.target_lang
    )

    try:
        translate_file(
            args.input_file,
            args.output_dir,
            args.provider,
            args.source_lang,
            args.target_lang,
            formatted_prompt,
            args.dictionary,
            args.model
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
