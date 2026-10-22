---
name: pdf-editor
description: Handle PDF editing workflows for local document cleanup, page management, text changes, annotations, and export. Use when working with PDFs, document editing, OCR, forms, or scanned documents in this project.
---

# PDF Editor

## Purpose

This project contains a local PDF editor built with Flask and PyMuPDF. It is designed for editing PDFs entirely on the user's machine without uploading documents to a remote service.

## Day-to-day workflow

1. Start the app with `python pdfsxt.py` or `start.bat` on Windows.
2. Open a PDF from disk or drag a file into the browser UI.
3. Use the page rail to select pages and perform page operations.
4. Choose a tool from the toolbar for text changes, highlighting, redaction, whiteout, image insertion, or form filling.
5. Export the result as a new PDF or save selected pages.

## Core capabilities

- Open, merge, and export PDFs
- Rotate, move, delete, duplicate, and add blank pages
- Add or rewrite text on page positions
- Highlight, redact, or whiteout regions
- Insert images into PDFs
- Fill interactive form fields
- Run OCR for scanned pages using Tesseract language data
- Save password-protected PDFs when needed

## Codebase notes

- The browser UI is in `index.html`.
- The server and document logic live in `pdfsxt.py`.
- The local app listens on `127.0.0.1` and defaults to port `5173`.
- PDF processing uses PyMuPDF (`fitz`), and OCR support depends on a `tessdata` folder with trained language data.

## Safe editing rules

- Prefer local file operations over remote uploads.
- Keep edits deterministic and document-specific.
- When using OCR, confirm the correct language data is available before invoking it.
- Avoid modifying unrelated project files when fixing PDF workflows.

## Common tasks

### Run the editor

```bash
python pdfsxt.py
```

### Install dependencies

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### Verify OCR support

Check that `tessdata/eng.traineddata` exists before running OCR.

## Validation checklist

Before closing a PDF editing task:

- [ ] The requested edit is applied to the correct page or selection
- [ ] Export or download works as expected
- [ ] No unrelated files were changed
- [ ] OCR dependencies are checked when OCR is involved
- [ ] The result remains local to the machine

## Related files

- [README.md](../../README.md)
- [index.html](../../index.html)
- [pdfsxt.py](../../pdfsxt.py)
