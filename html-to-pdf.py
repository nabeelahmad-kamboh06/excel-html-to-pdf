import os
import random
import string
import html
import pandas as pd
import pdfkit

# Constants
EXCEL_FILE = "users11001-12000.xlsx"
OUTPUT_DIR = os.path.expanduser("~/Downloads/output_pdfs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Path to wkhtmltopdf binary (adjust if needed)
WKHTMLTOPDF_PATH = "/Users/nabeelahmad/.asdf/shims/wkhtmltopdf"
pdfkit_config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

# Utility functions
def random_string(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def sanitize_filename(filename):
    return "".join(c for c in filename if c.isalnum() or c in (' ', '_', '-', '.')).rstrip()

def escape_and_format_text(text: str) -> str:
    escaped = html.escape(text)
    return escaped.replace("\n", "<br>")

def ensure_styling(html_text: str) -> str:
    style_block = """
    <style>
      @page {
        size: A4;
        margin: 2cm;
      }
      html, body {
        margin: 0;
        padding: 0;
      }
      body {
        font-family: Arial, sans-serif;
        font-size: 12pt;
        line-height: 1.6;
        color: #000;
        background: #fff;
      }
      .content, .page-safe {
        max-width: 700px;
        margin: 0 auto;
        padding: 0;
        box-sizing: border-box;
        overflow-wrap: break-word;
        word-break: break-word;
        page-break-inside: auto;
      }
      p, li, td, th {
        page-break-inside: avoid;
      }
      h1, h2, h3 {
        page-break-after: avoid;
      }
      .page-break {
        page-break-after: always;
      }
    </style>
    """

    lower_html = html_text.lower()

    if "<head>" in lower_html:
        html_text = html_text.replace("<head>", f"<head>{style_block}", 1)
    elif "<html" in lower_html:
        html_text = html_text.replace("<html", f"<html><head>{style_block}</head>", 1)
    else:
        return wrap_html_content(html_text)

    if "class=\"page-safe\"" not in html_text:
        html_text = html_text.replace("<body>", "<body><div class=\"page-safe\">", 1)
        html_text = html_text.replace("</body>", "</div></body>", 1)

    return html_text

def wrap_html_content(body: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          @page {{
            size: A4;
            margin: 2cm;
          }}
          html, body {{
            height: 100%;
            margin: 0;
            padding: 0;
          }}
          body {{
            font-family: Arial, sans-serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #000;
            overflow-wrap: break-word;
            word-break: break-word;
          }}
          table, div, p {{
            page-break-inside: auto;
          }}
          .page-break {{
            page-break-after: always;
          }}
        </style>
      </head>
      <body>
        <div class="content">
          {body}
        </div>
      </body>
    </html>
    """

# Load Excel
df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
df = df[df['description'].notna()]  # Skip empty rows

# Process each row
for idx, row in df.iterrows():
    user_id = str(row.get("userID", "")).strip() or random_string()
    name = str(row.get("name", "")).strip() or "User" + random_string()
    html_description = str(row.get("description", "")).strip()

    if not html_description:
        print(f"[⚠] Skipped row {idx}: empty description.")
        continue

    if "<" not in html_description:
        html_description = escape_and_format_text(html_description)

    full_html = ensure_styling(html_description)
    filename = sanitize_filename(f"{name}_{user_id}.pdf")
    output_path = os.path.join(OUTPUT_DIR, filename)

    try:
        pdfkit.from_string(full_html, output_path, configuration=pdfkit_config)
        print(f"[✓] Saved: {filename}")
    except Exception as e:
        print(f"[✗] Failed: {filename} => {e}")
