import os
import glob
import re
import warnings
import shutil
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from markdownify import markdownify as md

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def repair_table_structure(md_text):
    """
    Master function to fix broken Markdown tables.
    1. SWAP: Moves the separator line (|---|) to be BELOW the header row.
    2. RESIZE: Fixes the separator line to match the column count of the header.
    """
    lines = md_text.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # DETECT SEPARATOR LINE (e.g., |---|---|)
        if re.match(r'^\s*\|[\s\-\|:]+\|\s*$', line) and '-' in line:
            
            # CHECK: Is this separator at the TOP of the table? (i.e., before the text?)
            # Look at the NEXT line
            if i + 1 < len(lines) and '|' in lines[i+1] and not re.match(r'^\s*\|[\s\-\|:]+\|\s*$', lines[i+1]):
                
                # FOUND IT! The separator is first, text is second.
                # SWAP THEM: Put Text (Header) first, Separator second.
                header_row = lines[i+1]
                separator_row = line
                
                # NOW RESIZE THE SEPARATOR to match the header's column count
                # Count pipes in header row and subtract 1 to get column count
                col_count = header_row.count('|') - 1
                if col_count > 0:
                    new_separator = '|' + '|'.join([' --- '] * col_count) + '|'
                else:
                    new_separator = separator_row # Fallback

                # Append in correct order
                fixed_lines.append(header_row)
                fixed_lines.append(new_separator)
                
                # Skip the next line since we just used it
                i += 2
                continue
            
            # CHECK: Is this separator in the MIDDLE (normal), but wrong width?
            else:
                # Just resize it based on the PREVIOUS line (the header)
                # Look back at the last added line
                if fixed_lines and '|' in fixed_lines[-1]:
                    prev_row = fixed_lines[-1]
                    col_count = prev_row.count('|') - 1
                    if col_count > 0:
                        new_separator = '|' + '|'.join([' --- '] * col_count) + '|'
                        fixed_lines.append(new_separator)
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
                i += 1

        else:
            # Normal text line, just add it
            fixed_lines.append(line)
            i += 1
            
    return '\n'.join(fixed_lines)

def clean_and_convert():
    # --- CONFIGURATION ---
    # Search in 'html10k' folder OR current folder
    search_patterns = [os.path.join("html10k", "*.html"), "*.html"]
    html_files = []
    for pattern in search_patterns:
        html_files.extend(glob.glob(pattern))
    html_files = list(set(html_files))

    output_dir = "mds"
    if not os.path.exists("mds"):
        os.makedirs("mds")

    if not html_files:
        print("No HTML files found.")
        return

    print(f"Found {len(html_files)} HTML files. Starting conversion...")

    for file_path in html_files:
        ticker = os.path.basename(os.path.splitext(file_path)[0])
        md_filename = os.path.join(output_dir, f"{ticker}.md")
        print(f"Processing {ticker}...", end=" ")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_content = f.read()

            # 1. PRE-CLEANING
            raw_content = re.sub(r'<\?xml.*?\?>', '', raw_content, flags=re.DOTALL)

            # 2. PARSE
            soup = BeautifulSoup(raw_content, 'lxml')

            # 3. AGGRESSIVE CLEANING
            for tag in soup.find_all(['ix:header', 'script', 'style', 'head', 'meta', 'noscript', 'link']):
                tag.decompose()
            
            for tag in soup.find_all(attrs={"style": re.compile(r"display:\s*none", re.I)}):
                tag.decompose()
            
            # Remove images
            for img in soup.find_all('img'):
                img.decompose()

            # Unwrap data
            unwrap_tags = ['ix:nonnumeric', 'ix:continuation', 'span', 'div', 'font', 'b', 'i', 'u', 'center']
            for tag_name in unwrap_tags:
                for tag in soup.find_all(tag_name):
                    tag.unwrap()

            # 4. MARKDOWN CONVERSION
            clean_html = str(soup)
            markdown_text = md(
                clean_html, 
                heading_style="ATX", 
                strip=['a'], 
                newline_style="BACKSLASH"
            )

            # 5. POST-PROCESSING (REGEX CLEANUP)

            # A. Remove Repetitive "Table of Contents"
            # Replace the FIRST one with a placeholder
            markdown_text = markdown_text.replace("Table of Contents", "@@@MAIN_TOC@@@", 1)
            # Delete ALL others
            markdown_text = markdown_text.replace("Table of Contents", "")
            # Restore the first one
            markdown_text = markdown_text.replace("@@@MAIN_TOC@@@", "# Table of Contents")

            # B. Financial Glue
            markdown_text = re.sub(r'\|\s*\$\s*\|\s*', '| $', markdown_text)
            markdown_text = re.sub(r'\|\s*%\s*\|', '% |', markdown_text)
            markdown_text = re.sub(r'\|\s*\(\s*\|\s*', '| (', markdown_text)
            markdown_text = re.sub(r'\|\s*\)\s*\|', ') |', markdown_text)

            # C. Table Squeezer (The "20 columns to 5" fixer)
            markdown_text = re.sub(r'\|(\s*\|)+', '|', markdown_text)

            # D. Remove Empty Rows
            markdown_text = re.sub(r'^\s*\|[\s\|]*\|\s*$', '', markdown_text, flags=re.MULTILINE)

            # E. Whitespace Cleanup
            markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)

            # 6. REPAIR STRUCTURE (SWAP & RESIZE)
            # This aligns the headers and moves the separator line to the correct spot
            markdown_text = repair_table_structure(markdown_text)

            with open(md_filename, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
            
            print(f"-> Saved clean Markdown to {md_filename}")
        except Exception as e:
            print(f"-> Failed: {e}")
    shutil.rmtree("html10k")
if __name__ == "__main__":
    clean_and_convert()