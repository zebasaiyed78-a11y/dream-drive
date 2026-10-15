# PDF to Table Backend (FastAPI + Hugging Face)

Frontend uploads a PDF -> backend extracts text -> Hugging Face model
converts it into rows and columns -> JSON is returned.

## Setup (VS Code terminal)

1. Create and activate a virtual environment
   python -m venv venv
   venv\Scripts\activate          (Windows)
   source venv/bin/activate       (Mac/Linux)

2. Install libraries
   pip install -r requirements.txt

3. Create a file named .env (copy .env.example) and paste your
   Hugging Face token (huggingface.co -> Settings -> Access Tokens)
   HF_TOKEN=hf_xxxxxxxxxxxx

4. Run the server
   uvicorn main:app --reload

5. Test
   - Open http://127.0.0.1:8000/docs  (Swagger UI) and try POST /upload
   - OR open test.html in the browser

## Endpoints
- GET  /               health check
- POST /upload         PDF -> AI (Hugging Face) -> {"columns": [...], "rows": [[...]]}
- POST /upload-tables  PDF -> pdfplumber tables only (no AI)

## Notes
- Long PDFs are split into chunks and the rows are merged.
- Scanned PDFs need OCR (pytesseract / TrOCR) - not included.
- Never commit .env (the token is secret).
