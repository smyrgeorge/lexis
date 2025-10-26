# translate_md.py

Advanced markdown translation tool using LLMs (Claude or ChatGPT) with context-aware chunking support.

## Overview

This script translates markdown files using state-of-the-art language models. It includes intelligent features like
context preservation across chunks, automatic skipping of already-translated files, and custom terminology dictionaries.

## Key Features

### 🎯 Context-Aware Translation

- **Automatic Context Inclusion**: When translating chunks in a directory, automatically includes lines from adjacent
  chunks to improve translation quality across boundaries
- **Configurable Context Size**: Control how many lines of context to include (default: 5)
- **Clear LLM Instructions**: Explicitly marks context sections so the LLM knows what to translate and what's for
  reference only

### 🚀 Smart Processing

- **Batch Directory Processing**: Process all markdown files in a directory at once
- **Already-Translated Detection**: Automatically skips files that have already been translated
- **Progress Tracking**: Shows current file, character count, execution time, and context information

### 🔧 Customization

- **Custom Dictionaries**: CSV-based terminology dictionaries for consistent specialized translation
- **Custom Prompts**: Override the default translation prompt
- **Model Selection**: Choose specific models (e.g., `claude-sonnet-4-5-20250929`, `gpt-4o-mini`)
- **Provider Choice**: Use Claude (Anthropic) or ChatGPT (OpenAI)

### 🎨 Output Control

- **Same-Directory Output**: Translated files placed next to source files by default
- **Language Suffix**: Output files named as `<original>_<target-lang>.md`
- **Custom Output Directory**: Override default location if needed

## Usage

### Basic Translation

```bash
# Translate a single file with Claude (default)
python scripts/translate_md.py document.md -s Spanish -t English

# Translate using OpenAI
python scripts/translate_md.py document.md -s Spanish -t English -p openai
```

### Batch Translation with Context

```bash
# Translate all markdown files in a directory
# Automatically uses context from adjacent chunks
python scripts/translate_md.py ./chunks -s Spanish -t English

# Customize context lines (default is 5)
python scripts/translate_md.py ./chunks -s Spanish -t English -c 10

# Disable context (not recommended for chunked documents)
python scripts/translate_md.py ./chunks -s Spanish -t English -c 0
```

### With Custom Dictionary

```bash
# Use terminology dictionary for consistent translations
python scripts/translate_md.py document.md -s Spanish -t English -d ./dictionary.csv
```

Dictionary format (`dictionary.csv`):

```csv
source,target
poder,power
estado,state
democracia,democracy
```

### Advanced Options

```bash
# Custom model
python scripts/translate_md.py document.md -s Spanish -t English -m gpt-4o-mini

# Custom output directory
python scripts/translate_md.py document.md -s Spanish -t English -o ./translations

# Custom prompt
python scripts/translate_md.py document.md -s Spanish -t English --prompt "Translate from {source} to {target}. Be formal."
```

## Command-Line Options

| Option            | Short | Description                             | Default          |
|-------------------|-------|-----------------------------------------|------------------|
| `input_file`      | -     | Input markdown file or directory        | Required         |
| `--source-lang`   | `-s`  | Source language                         | Required         |
| `--target-lang`   | `-t`  | Target language                         | Required         |
| `--provider`      | `-p`  | LLM provider: `claude` or `openai`      | `claude`         |
| `--output-dir`    | `-o`  | Output directory                        | Same as input    |
| `--dictionary`    | `-d`  | Path to CSV dictionary file             | None             |
| `--model`         | `-m`  | Specific model to use                   | Provider default |
| `--prompt`        | -     | Custom translation prompt               | Default prompt   |
| `--context-lines` | `-c`  | Lines from prev/next chunks for context | 5                |

## Context-Aware Translation

When processing multiple chunks in a directory, the script automatically includes context from adjacent files to improve
translation quality at chunk boundaries.

### How It Works

For `chunk_002.md`:

```
┌─────────────────────────────────────┐
│ CONTEXT FROM PREVIOUS CHUNK         │
│ (Last 5 lines from chunk_001.md)   │
│ - FOR REFERENCE ONLY -              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ MAIN CONTENT TO TRANSLATE           │
│ (Full content of chunk_002.md)      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ CONTEXT FROM NEXT CHUNK             │
│ (First 5 lines from chunk_003.md)   │
│ - FOR REFERENCE ONLY -              │
└─────────────────────────────────────┘
```

The LLM receives clear instructions that context sections are **for reference only** and should **not be translated**.

### Benefits

1. **Better Continuity**: Sentences split across chunks are translated coherently
2. **Pronoun Resolution**: Context helps resolve pronouns and references
3. **Consistent Terminology**: See how terms were used in adjacent sections
4. **Natural Flow**: Maintains narrative flow across chunk boundaries

### Example

Without context:

```
[chunk_001.md ends]: "...el presidente del país."
[chunk_002.md starts]: "Él decidió cambiar la política."
Translation: "He decided to change the policy."  ❌ (Who is "he"?)
```

With context:

```
[chunk_001.md context]: "...el presidente del país."
[chunk_002.md]: "Él decidió cambiar la política."
Translation: "The president decided to change the policy."  ✅
```

## Progress Output

```
================================================================================
Processing: chunk_005.md
  Characters: 19,850
  First line: fueran actores del mercado que responden a incentivos...

  📄 Previous chunk: chunk_004.md
     Last line: ...las empresas tecnológicas afrontan diversos desafíos.

  📄 Next chunk: chunk_006.md
     First line: No obstante, en la actualidad, las grandes empresas...
================================================================================
Translating with claude (with context from adjacent chunks)...
✓ Translation saved to: chunk_005_English.md (took 4.23s)
```

## Skipping Already-Translated Files

When processing a directory, the script automatically skips:

1. Files ending with `_{target_lang}.md` (e.g., `document_English.md`)
2. Files where a translation already exists (e.g., skip `doc.md` if `doc_English.md` exists)

```
⊘ Skipping document_001.md (translation already exists)
⊘ Skipping document_002.md (translation already exists)
Found 30 markdown files (8 already translated, 22 to process)
```

## Environment Setup

### API Keys

Create a `.env` file in the project root:

```bash
# For Claude (Anthropic)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# For ChatGPT (OpenAI)
OPENAI_API_KEY=your_openai_api_key_here
```

### Models

**Claude (Default)**:

- Default model: `claude-sonnet-4-5-20250929`
- Best for: High-quality literary and technical translation
- Context window: Large (200K tokens)

**OpenAI**:

- Default model: `gpt-4o`
- Alternative: `gpt-4o-mini` (faster, cheaper)
- Best for: Fast translation, cost optimization

## Complete Translation Pipeline

### Step 1: Prepare PDF

```bash
# Split large PDF into manageable chunks
python scripts/chunk_pdf.py large-book.pdf -p 10 -o ./pdf-chunks
```

### Step 2: Convert to Markdown

```bash
# Batch convert all PDF chunks to markdown
python scripts/pdf_to_md.py ./pdf-chunks
```

### Step 3: Translate with Context

```bash
# Translate all markdown chunks with automatic context
python scripts/translate_md.py ./pdf-chunks -s Spanish -t English -d ./dictionary.csv
```

Result: Each chunk translated with awareness of surrounding context!

## Custom Prompts

Override the default prompt using `{source}` and `{target}` placeholders:

```bash
python scripts/translate_md.py doc.md \
  -s Spanish -t English \
  --prompt "Translate the following {source} text to {target}. Use formal academic language. Preserve all markdown formatting."
```

## Dictionary Format

Create a CSV file with source and target terms:

```csv
source,target
inteligencia artificial,artificial intelligence
aprendizaje automático,machine learning
red neuronal,neural network
```

The dictionary is prepended to the translation prompt, helping the LLM use consistent terminology.

## Error Handling

- **Missing API Key**: Clear error message with setup instructions
- **File Not Found**: Validates input files/directories exist
- **Translation Failures**: Reports errors but continues processing remaining files
- **Keyboard Interrupt**: Graceful exit with `Ctrl+C`
- **Network Issues**: API errors are caught and reported

## Performance Tips

1. **Batch Processing**: Process directories instead of individual files (one API call per file, not per directory)
2. **Context Size**: More context = better quality but higher cost (5 lines is a good balance)
3. **Model Selection**: Use `gpt-4o-mini` for drafts, `claude-sonnet` for final translations
4. **Dictionary**: Pre-define technical terms to ensure consistency and reduce iterations

## Requirements

- Python 3.9+
- anthropic (`pip install anthropic`) - for Claude
- openai (`pip install openai`) - for ChatGPT
- python-dotenv (`pip install python-dotenv`)

## Example Output (Full Session)

```
Found 27 markdown files (4 already translated, 23 to process)

================================================================================
Processing: estado-del-poder_chunk_005_pages_41-50.md
  Characters: 19,850
  First line: fueran actores del mercado que responden a incentivos...

  📄 Previous chunk: estado-del-poder_chunk_004_pages_31-40.md
     Last line: ...las empresas tecnológicas afrontan diversos desafíos.

  📄 Next chunk: estado-del-poder_chunk_006_pages_51-60.md
     First line: No obstante, en la actualidad, las grandes empresas...
================================================================================
Translating with claude (with context from adjacent chunks)...
✓ Translation saved to: estado-del-poder_chunk_005_pages_41-50_English.md (took 4.23s)

================================================================================
Processing: estado-del-poder_chunk_006_pages_51-60.md
  Characters: 18,421
  First line: No obstante, en la actualidad, las grandes empresas...

  📄 Previous chunk: estado-del-poder_chunk_005_pages_41-50.md
     Last line: ...decidió cambiar la política sobre este tema.

  📄 Next chunk: estado-del-poder_chunk_007_pages_61-70.md
     First line: El impacto de estas decisiones fue significativo...
================================================================================
Translating with claude (with context from adjacent chunks)...
✓ Translation saved to: estado-del-poder_chunk_006_pages_51-60_English.md (took 3.87s)

...

================================================================================
Summary:
  Total files: 23
  Successfully translated: 23
  Failed: 0
================================================================================
```

## Troubleshooting

**API Key Not Found**:

```
Error: ANTHROPIC_API_KEY not found in environment variables
```

→ Create `.env` file with your API key

**Rate Limiting**:
→ Add delays between requests or use a different model tier

**Out of Context**:
→ Reduce `--context-lines` or split into smaller chunks

## See Also

- [chunk_pdf.md](chunk_pdf.md) - Split PDFs before translation
- [chunk_md.md](chunk_md.md) - Split markdown files
- [batch_convert_pdf_to_md.md](pdf_to_md.md) - Convert PDFs to markdown
