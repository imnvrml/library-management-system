"""Export the Markdown documents in docs/ to PDF (docs/pdf/) with headless Google Chrome.

    pip install markdown        # only needed for this script, not for the application
    python scripts/build_pdfs.py

Set CHROME to the browser executable if it is not found automatically.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "pdf"
DOCUMENTS = [
    ("requirements.md", "A_Requirements_Specification"),
    ("models.md", "B_Analysis_and_Design_Models"),
    ("test-plan.md", "C_Test_Plan_and_Test_Report"),
    ("traceability.md", "D_Traceability_Matrix"),
    ("change-request.md", "E_Change_Request_CR-01"),
    ("code-review.md", "F_Code_Review_Checklist"),
    ("reflection.md", "G_Reflection"),
]

CSS = """
@page { size: A4; margin: 16mm 14mm; }
body { font: 10.5pt/1.45 "Segoe UI", Arial, sans-serif; color: #111; }
h1 { font-size: 19pt; border-bottom: 2px solid #333; padding-bottom: 4px; }
h2 { font-size: 14pt; margin-top: 18px; break-after: avoid; }
h3, h4 { font-size: 11.5pt; break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 12px; font-size: 8.6pt; }
th, td { border: 1px solid #999; padding: 3px 5px; vertical-align: top; text-align: left; }
th { background: #eee; }
tr { break-inside: avoid; }
code { font-family: Consolas, monospace; font-size: 8.8pt; background: #f3f3f3; padding: 0 2px; }
pre { background: #f3f3f3; padding: 6px; font-size: 8.8pt; white-space: pre-wrap; }
img { max-width: 100%; max-height: 235mm; display: block; margin: 6px auto; break-inside: avoid; }
blockquote { border-left: 3px solid #999; margin: 6px 0; padding-left: 10px; color: #333; }
"""


def find_chrome() -> str:
    candidates = [os.environ.get("CHROME", ""), shutil.which("chrome") or "", shutil.which("google-chrome") or "",
                  r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                  r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]
    for c in candidates:
        if c and Path(c).exists():
            return c
    sys.exit("Chrome not found: set the CHROME environment variable.")


def main() -> None:
    chrome = find_chrome()
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for source, name in DOCUMENTS:
            text = (DOCS / source).read_text(encoding="utf-8")
            body = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
            # <base> makes relative image links such as models/img/use-case.png work from the temp folder
            html = (f"<!doctype html><html><head><meta charset='utf-8'><base href='{DOCS.as_uri()}/'>"
                    f"<title>{name}</title><style>{CSS}</style></head><body>{body}</body></html>")
            page = Path(tmp) / f"{name}.html"
            page.write_text(html, encoding="utf-8")
            pdf = OUT / f"{name}.pdf"
            subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                            "--allow-file-access-from-files", f"--print-to-pdf={pdf}", page.as_uri()],
                           check=True, capture_output=True)
            print(f"{pdf.relative_to(ROOT)}  ({pdf.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
