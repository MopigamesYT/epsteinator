#!/usr/bin/env python3

#!/usr/bin/env python3
import pymupdf
import sys
import os
import readline
import glob
from pathlib import Path

def setup_readline():
    """Configure readline for path autocompletion."""
    # Enable tab completion
    readline.parse_and_bind("tab: complete")

    # Set completer function
    readline.set_completer(path_completer)

    # Set delimiters (exclude '/' to keep path components together)
    readline.set_completer_delims(' \t\n;')

def path_completer(text, state):
    """
    Custom completer for file paths.
    This function is called by readline for tab completion.
    """
    # Expand user home directory
    text = os.path.expanduser(text)

    # If text is empty, start from current directory
    if not text:
        text = './'

    # Get the directory and file parts
    if os.path.isdir(text):
        # If it's a directory, add /* to list contents
        search_path = os.path.join(text, '*')
    else:
        # Otherwise, glob for matching paths
        search_path = text + '*'

    # Get all matching paths
    matches = glob.glob(search_path)

    # Add trailing slash to directories
    matches = [m + '/' if os.path.isdir(m) else m for m in matches]

    # Filter for PDF files if we're beyond just directory navigation
    if text and not text.endswith('/'):
        # Prioritize PDF files but keep directories
        pdf_matches = [m for m in matches if m.endswith('.pdf') or os.path.isdir(m.rstrip('/'))]
        if pdf_matches:
            matches = pdf_matches

    # Return the match for the current state
    try:
        return matches[state]
    except IndexError:
        return None

def get_path_with_completion(prompt):
    """Get a file path from user with tab completion enabled."""
    setup_readline()

    while True:
        try:
            path = input(prompt).strip()

            # Expand user home directory and environment variables
            path = os.path.expanduser(os.path.expandvars(path))

            # Remove quotes if present
            path = path.strip('\'"')

            if os.path.isfile(path):
                return path
            else:
                print(f"Error: File '{path}' not found. Please try again.\n")
        except KeyboardInterrupt:
            print("\n\nOperation cancelled.")
            sys.exit(0)

def get_user_input():
    """Collect user input for PDF redaction parameters."""
    print("=== PDF Redaction Tool ===")
    print("(Use TAB for path autocompletion)\n")

    # Get input PDF path with autocompletion
    pdf_path = get_path_with_completion("Enter the path to the PDF file: ")

    # Get text to redact
    print("\nEnter text to redact (you can add multiple terms):")
    print("Type each term and press Enter. When done, press Enter on an empty line.")

    terms_to_redact = []
    while True:
        term = input(f"Term #{len(terms_to_redact) + 1} (or press Enter to finish): ").strip()
        if not term:
            if terms_to_redact:
                break
            print("You must enter at least one term to redact.")
        else:
            terms_to_redact.append(term)

    # Case sensitivity option
    case_sensitive = input("\nCase sensitive search? (y/n, default: y): ").strip().lower()
    case_sensitive = case_sensitive != 'n'

    # Redaction color
    print("\nChoose redaction color:")
    print("1. Black (default)")
    print("2. White")
    print("3. Custom RGB")
    color_choice = input("Enter choice (1-3): ").strip()

    if color_choice == "2":
        fill_color = (1, 1, 1)
    elif color_choice == "3":
        try:
            r = float(input("Red (0-1): "))
            g = float(input("Green (0-1): "))
            b = float(input("Blue (0-1): "))
            fill_color = (r, g, b)
        except ValueError:
            print("Invalid RGB values. Using black.")
            fill_color = (0, 0, 0)
    else:
        fill_color = (0, 0, 0)

    # Output path with autocompletion
    default_output = str(Path(pdf_path).parent / f"{Path(pdf_path).stem}_redacted.pdf")
    print(f"\nOutput path (press Enter for default: {default_output})")

    setup_readline()
    output_path = input("Output path: ").strip()

    if not output_path:
        output_path = default_output
    else:
        # Expand path
        output_path = os.path.expanduser(os.path.expandvars(output_path))
        output_path = output_path.strip('\'"')

    return {
        'input_path': pdf_path,
        'terms': terms_to_redact,
        'case_sensitive': case_sensitive,
        'fill_color': fill_color,
        'output_path': output_path
    }

def redact_pdf(input_path, terms, case_sensitive=True, fill_color=(0, 0, 0), output_path=None):
    """
    Redact specified terms from a PDF document.

    Args:
        input_path: Path to input PDF file
        terms: List of strings to redact
        case_sensitive: Whether search should be case sensitive
        fill_color: RGB tuple for redaction color (values 0-1)
        output_path: Path for output PDF (optional)

    Returns:
        Dictionary with redaction statistics
    """
    try:
        # Open the PDF
        doc = pymupdf.open(input_path)

        # Statistics tracking
        stats = {term: 0 for term in terms}
        total_redactions = 0

        # Process each page
        for page_num, page in enumerate(doc, 1):
            page_redactions = 0

            for term in terms:
                # Search for the term
                search_flags = pymupdf.TEXT_PRESERVE_WHITESPACE
                if not case_sensitive:
                    search_flags |= pymupdf.TEXT_PRESERVE_LIGATURES

                text_instances = page.search_for(term, flags=search_flags)

                # Add redaction annotations
                for inst in text_instances:
                    page.add_redact_annot(inst, fill=fill_color)
                    stats[term] += 1
                    page_redactions += 1
                    total_redactions += 1

            # Apply redactions on this page
            if page_redactions > 0:
                page.apply_redactions()
                print(f"Page {page_num}: {page_redactions} redaction(s) applied")

        # Set output path if not provided
        if output_path is None:
            output_path = str(Path(input_path).parent / f"{Path(input_path).stem}_redacted.pdf")

        # Save the redacted PDF
        doc.save(output_path)
        doc.close()

        # Print summary
        print("\n=== Redaction Summary ===")
        print(f"Total redactions: {total_redactions}")
        for term, count in stats.items():
            print(f"  '{term}': {count} instance(s)")
        print(f"\nSaved to: {output_path}")

        return {
            'success': True,
            'total_redactions': total_redactions,
            'stats': stats,
            'output_path': output_path
        }

    except Exception as e:
        print(f"\nError during redaction: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Main function with interactive or CLI mode."""
    # Check if arguments provided (CLI mode)
    if len(sys.argv) > 1:
        print("CLI mode not yet implemented. Running in interactive mode.\n")

    # Interactive mode
    try:
        params = get_user_input()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")
        sys.exit(0)

    print("\n=== Starting Redaction ===")
    result = redact_pdf(
        input_path=params['input_path'],
        terms=params['terms'],
        case_sensitive=params['case_sensitive'],
        fill_color=params['fill_color'],
        output_path=params['output_path']
    )

    if result['success']:
        print("\n✓ Redaction completed successfully!")
    else:
        print("\n✗ Redaction failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
