# Epsteinator

A PDF redaction tool that permanently removes specified text from PDF documents.

## Installation

```bash
pip install pymupdf
```

## Usage

### Interactive Mode

Run without arguments for an interactive experience with tab completion:

```bash
python epsteinator.py
```

### CLI Mode

```bash
python epsteinator.py <input.pdf> <term1> [term2 ...] [options]
```

**Options:**
- `-o, --output <path>` - Output file path (default: `<input>_redacted.pdf`)
- `-i, --ignore-case` - Case-insensitive search
- `-c, --color <color>` - Redaction color: `black` (default), `white`, or `R,G,B` values (0-1)
- `-r, --regex` - Treat terms as regular expressions

**Examples:**

```bash
# Redact a single term
python epsteinator.py document.pdf "secret"

# Redact multiple terms
python epsteinator.py document.pdf "secret" "confidential" "classified"

# Case-insensitive with custom output
python epsteinator.py document.pdf "name" -i -o output.pdf

# White redaction boxes
python epsteinator.py document.pdf "redact me" --color white

# Custom RGB color (gray)
python epsteinator.py document.pdf "text" --color 0.5,0.5,0.5

# Regex: redact email addresses
python epsteinator.py document.pdf "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" -r

# Regex: redact phone numbers (xxx-xxx-xxxx format)
python epsteinator.py document.pdf "\d{3}-\d{3}-\d{4}" -r

# Regex: redact SSN patterns
python epsteinator.py document.pdf "\d{3}-\d{2}-\d{4}" -r

# Regex: redact dates (MM/DD/YYYY)
python epsteinator.py document.pdf "\d{2}/\d{2}/\d{4}" -r
```

## Features

- Permanent redaction (text is removed, not just covered)
- Multiple search terms or regex patterns
- Regular expression support for pattern matching
- Case-sensitive or case-insensitive matching
- Customizable redaction colors
- Tab completion for file paths in interactive mode
- Redaction statistics per term/pattern
