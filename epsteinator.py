#!/usr/bin/env python3
import pymupdf
import sys
import os
import re
import readline
import glob
import argparse
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    # Backgrounds
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_BLUE = '\033[44m'

    @classmethod
    def disable(cls):
        """Disable colors (for non-TTY output)."""
        for attr in dir(cls):
            if not attr.startswith('_') and attr.isupper():
                setattr(cls, attr, '')


# Disable colors if not a TTY
if not sys.stdout.isatty():
    Colors.disable()

C = Colors  # Short alias


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
                print(f"{C.RED}Error:{C.RESET} File '{C.YELLOW}{path}{C.RESET}' not found. Please try again.\n")
        except KeyboardInterrupt:
            print(f"\n\n{C.YELLOW}Operation cancelled.{C.RESET}")
            sys.exit(0)

def get_user_input():
    """Collect user input for PDF redaction parameters."""
    print(f"\n{C.BOLD}{C.MAGENTA}╔══════════════════════════════════════╗{C.RESET}")
    print(f"{C.BOLD}{C.MAGENTA}║{C.RESET}     {C.BOLD}{C.WHITE}PDF Redaction Tool{C.RESET}              {C.BOLD}{C.MAGENTA}║{C.RESET}")
    print(f"{C.BOLD}{C.MAGENTA}╚══════════════════════════════════════╝{C.RESET}")
    print(f"{C.DIM}(Use TAB for path autocompletion){C.RESET}\n")

    # Get input PDF path with autocompletion
    pdf_path = get_path_with_completion(f"{C.CYAN}[1/5]{C.RESET} {C.BOLD}PDF file path:{C.RESET} ")
    print(f"      {C.GREEN}✓{C.RESET} {C.DIM}{pdf_path}{C.RESET}")

    # Regex mode option
    use_regex = input(f"\n{C.CYAN}[2/5]{C.RESET} {C.BOLD}Use regular expressions?{C.RESET} {C.DIM}(y/n, default: n):{C.RESET} ").strip().lower()
    use_regex = use_regex == 'y'
    print(f"      {C.GREEN}✓{C.RESET} {C.DIM}{'Regex mode' if use_regex else 'Literal mode'}{C.RESET}")

    # Get text to redact
    print(f"\n{C.CYAN}[3/5]{C.RESET} {C.BOLD}Terms to redact{C.RESET}")
    if use_regex:
        print(f"      {C.DIM}Enter regex patterns (press Enter on empty line when done){C.RESET}")
    else:
        print(f"      {C.DIM}Enter text terms (press Enter on empty line when done){C.RESET}")

    terms_to_redact = []
    while True:
        prompt = "Pattern" if use_regex else "Term"
        term = input(f"      {C.YELLOW}#{len(terms_to_redact) + 1}{C.RESET} {prompt}: ").strip()
        if not term:
            if terms_to_redact:
                break
            print(f"      {C.RED}!{C.RESET} You must enter at least one {'pattern' if use_regex else 'term'}.")
        else:
            if use_regex:
                # Validate regex
                try:
                    re.compile(term)
                    terms_to_redact.append(term)
                    print(f"         {C.GREEN}✓{C.RESET} {C.DIM}Pattern added{C.RESET}")
                except re.error as e:
                    print(f"         {C.RED}✗{C.RESET} Invalid regex: {e}")
            else:
                terms_to_redact.append(term)
                print(f"         {C.GREEN}✓{C.RESET} {C.DIM}Term added{C.RESET}")

    print(f"      {C.GREEN}✓{C.RESET} {C.DIM}{len(terms_to_redact)} term(s) to redact{C.RESET}")

    # Case sensitivity option
    case_sensitive = input(f"\n{C.CYAN}[4/5]{C.RESET} {C.BOLD}Case sensitive?{C.RESET} {C.DIM}(y/n, default: y):{C.RESET} ").strip().lower()
    case_sensitive = case_sensitive != 'n'
    print(f"      {C.GREEN}✓{C.RESET} {C.DIM}{'Case sensitive' if case_sensitive else 'Case insensitive'}{C.RESET}")

    # Redaction color
    print(f"\n{C.CYAN}[5/5]{C.RESET} {C.BOLD}Redaction color{C.RESET}")
    print(f"      {C.DIM}1.{C.RESET} {C.WHITE}{C.BG_RED} Black {C.RESET} {C.DIM}(default){C.RESET}")
    print(f"      {C.DIM}2.{C.RESET} {C.WHITE} White {C.RESET}")
    print(f"      {C.DIM}3.{C.RESET} {C.MAGENTA}Custom RGB{C.RESET}")
    color_choice = input(f"      Choice {C.DIM}(1-3):{C.RESET} ").strip()

    if color_choice == "2":
        fill_color = (1, 1, 1)
        color_name = "White"
    elif color_choice == "3":
        try:
            r = float(input(f"      {C.RED}R{C.RESET} {C.DIM}(0-1):{C.RESET} "))
            g = float(input(f"      {C.GREEN}G{C.RESET} {C.DIM}(0-1):{C.RESET} "))
            b = float(input(f"      {C.BLUE}B{C.RESET} {C.DIM}(0-1):{C.RESET} "))
            fill_color = (r, g, b)
            color_name = f"RGB({r:.1f}, {g:.1f}, {b:.1f})"
        except ValueError:
            print(f"      {C.YELLOW}!{C.RESET} Invalid values, using black.")
            fill_color = (0, 0, 0)
            color_name = "Black"
    else:
        fill_color = (0, 0, 0)
        color_name = "Black"
    print(f"      {C.GREEN}✓{C.RESET} {C.DIM}{color_name}{C.RESET}")

    # Output path with autocompletion
    default_output = str(Path(pdf_path).parent / f"{Path(pdf_path).stem}_redacted.pdf")
    print(f"\n{C.CYAN}[Output]{C.RESET} {C.BOLD}Save location{C.RESET}")
    print(f"      {C.DIM}Press Enter for: {default_output}{C.RESET}")

    setup_readline()
    output_path = input(f"      Path: ").strip()

    if not output_path:
        output_path = default_output
    else:
        # Expand path
        output_path = os.path.expanduser(os.path.expandvars(output_path))
        output_path = output_path.strip('\'"')
    print(f"      {C.GREEN}✓{C.RESET} {C.DIM}{output_path}{C.RESET}")

    return {
        'input_path': pdf_path,
        'terms': terms_to_redact,
        'case_sensitive': case_sensitive,
        'fill_color': fill_color,
        'output_path': output_path,
        'use_regex': use_regex
    }

def redact_pdf(input_path, terms, case_sensitive=True, fill_color=(0, 0, 0), output_path=None, use_regex=False):
    """
    Redact specified terms from a PDF document.

    Args:
        input_path: Path to input PDF file
        terms: List of strings or regex patterns to redact
        case_sensitive: Whether search should be case sensitive
        fill_color: RGB tuple for redaction color (values 0-1)
        output_path: Path for output PDF (optional)
        use_regex: Whether to treat terms as regular expressions

    Returns:
        Dictionary with redaction statistics
    """
    try:
        # Open the PDF
        doc = pymupdf.open(input_path)

        # Statistics tracking
        stats = {term: 0 for term in terms}
        total_redactions = 0

        # Compile regex patterns if needed
        if use_regex:
            re_flags = 0 if case_sensitive else re.IGNORECASE
            patterns = []
            for term in terms:
                try:
                    patterns.append((term, re.compile(term, re_flags)))
                except re.error as e:
                    print(f"Invalid regex '{term}': {e}")
                    return {'success': False, 'error': f"Invalid regex '{term}': {e}"}

        # Process each page
        for page_num, page in enumerate(doc, 1):
            page_redactions = 0

            if use_regex:
                # Extract page text for regex matching
                page_text = page.get_text()

                for term, pattern in patterns:
                    # Find all matches
                    for match in pattern.finditer(page_text):
                        matched_text = match.group()
                        # Search for the matched text in the page to get coordinates
                        text_instances = page.search_for(matched_text)
                        for inst in text_instances:
                            page.add_redact_annot(inst, fill=fill_color)
                            stats[term] += 1
                            page_redactions += 1
                            total_redactions += 1
            else:
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
                print(f"  {C.DIM}Page {page_num}:{C.RESET} {C.YELLOW}{page_redactions}{C.RESET} redaction(s)")

        # Set output path if not provided
        if output_path is None:
            output_path = str(Path(input_path).parent / f"{Path(input_path).stem}_redacted.pdf")

        # Save the redacted PDF
        doc.save(output_path)
        doc.close()

        # Print summary
        print(f"\n{C.BOLD}{C.CYAN}┌─────────────────────────────────────┐{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}│{C.RESET}        {C.BOLD}Redaction Summary{C.RESET}           {C.BOLD}{C.CYAN}│{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}└─────────────────────────────────────┘{C.RESET}")
        print(f"  {C.BOLD}Total:{C.RESET} {C.GREEN}{total_redactions}{C.RESET} redaction(s)\n")
        for term, count in stats.items():
            bar_len = min(count, 20)
            bar = f"{C.MAGENTA}{'█' * bar_len}{C.RESET}"
            print(f"  {C.DIM}'{C.RESET}{term}{C.DIM}'{C.RESET}")
            print(f"    {bar} {C.BOLD}{count}{C.RESET}")
        print(f"\n  {C.BOLD}Saved to:{C.RESET} {C.GREEN}{output_path}{C.RESET}")

        return {
            'success': True,
            'total_redactions': total_redactions,
            'stats': stats,
            'output_path': output_path
        }

    except Exception as e:
        print(f"\n{C.RED}Error during redaction:{C.RESET} {e}")
        return {
            'success': False,
            'error': str(e)
        }

def parse_color(color_str):
    """Parse color argument into RGB tuple."""
    color_str = color_str.lower().strip()
    if color_str == 'black':
        return (0, 0, 0)
    elif color_str == 'white':
        return (1, 1, 1)
    else:
        try:
            parts = color_str.split(',')
            if len(parts) == 3:
                return tuple(float(p.strip()) for p in parts)
        except ValueError:
            pass
        print(f"Invalid color '{color_str}'. Using black.")
        return (0, 0, 0)


def main():
    """Main function with interactive or CLI mode."""
    # Check if arguments provided (CLI mode)
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(
            description='Redact specified terms from PDF documents.',
            epilog='Run without arguments for interactive mode with tab completion.'
        )
        parser.add_argument('input', help='Input PDF file path')
        parser.add_argument('terms', nargs='+', help='Terms to redact')
        parser.add_argument('-o', '--output', help='Output file path')
        parser.add_argument('-i', '--ignore-case', action='store_true',
                            help='Case-insensitive search')
        parser.add_argument('-c', '--color', default='black',
                            help='Redaction color: black, white, or R,G,B (0-1)')
        parser.add_argument('-r', '--regex', action='store_true',
                            help='Treat terms as regular expressions')

        args = parser.parse_args()

        if not os.path.isfile(args.input):
            print(f"{C.RED}Error:{C.RESET} File '{args.input}' not found.")
            sys.exit(1)

        print(f"\n{C.BOLD}{C.BLUE}▶ Starting Redaction...{C.RESET}\n")
        result = redact_pdf(
            input_path=args.input,
            terms=args.terms,
            case_sensitive=not args.ignore_case,
            fill_color=parse_color(args.color),
            output_path=args.output,
            use_regex=args.regex
        )
    else:
        # Interactive mode
        try:
            params = get_user_input()
        except KeyboardInterrupt:
            print(f"\n\n{C.YELLOW}Operation cancelled.{C.RESET}")
            sys.exit(0)

        print(f"\n{C.BOLD}{C.BLUE}▶ Starting Redaction...{C.RESET}\n")
        result = redact_pdf(
            input_path=params['input_path'],
            terms=params['terms'],
            case_sensitive=params['case_sensitive'],
            fill_color=params['fill_color'],
            output_path=params['output_path'],
            use_regex=params['use_regex']
        )

    if result['success']:
        print(f"\n{C.GREEN}{C.BOLD}✓ Redaction completed successfully!{C.RESET}\n")
    else:
        print(f"\n{C.RED}{C.BOLD}✗ Redaction failed!{C.RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
