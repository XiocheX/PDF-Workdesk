# PDF Workdesk

A lightweight local PDF editor built with Flask and PyMuPDF. The application runs entirely on your machine, opens a browser-based editor for PDF pages, and supports common document tasks such as page operations, text editing, highlights, redactions, form filling, image insertion, and optional OCR.

## Features

- Open local PDF files without uploading them to a remote service
- View and manipulate individual pages
- Rotate, move, duplicate, remove, and insert blank pages
- Add text and edit existing text on a page
- Highlight, whiteout, and redact regions
- Insert images into documents
- Merge a second PDF into the current document
- Export selected pages or save protected PDFs with a password
- Optional OCR for scanned documents via Tesseract language data

## Project structure

- `index.html` – browser UI for the PDF editor
- `pdfsxt.py` – Flask server and PDF manipulation logic
- `requirements.txt` – Python dependencies
- `start.bat` – Windows launcher that creates a virtual environment and starts the app

## Requirements

- Python 3.10+
- A local browser

Install dependencies:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell or Command Prompt, use the included launcher instead:

```powershell
start.bat
```

## Run it

```bash
python pdfsxt.py
```

The app starts on `http://127.0.0.1:5173` by default and automatically opens the browser window.

## Optional OCR setup

If you want to use the OCR tool:

1. Download the English Tesseract language file (`eng.traineddata`)
2. Put it in a folder named `tessdata` next to the project
3. Restart the app

Example:

```text
PDF Workdesk/
  tessdata/
    eng.traineddata
```

## Notes

- The app is designed for local use only and keeps file processing on the same computer.
- It does not rely on a cloud PDF service for editing or export.
- The default export action can save a password-protected PDF using the same password for both user and owner access.

## Troubleshooting

- If you see a missing dependency error, run `pip install -r requirements.txt`.
- If OCR is unavailable, make sure `tessdata/eng.traineddata` exists and the app can find it.
- If the browser does not open automatically, open `http://127.0.0.1:5173` manually.
