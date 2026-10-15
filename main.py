import io
import json
import os

import pdfplumber
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import InferenceClient

load_dotenv()  # loads HF_TOKEN from the .env file

app = FastAPI(title="PDF to Table API")

# CORS lets the frontend (running on another port / file) call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")
MAX_FILE_MB = 10
CHUNK_SIZE = 5000  # characters sent to the model per request

client = InferenceClient(token=HF_TOKEN)


# ---------- helper functions ----------

def read_pdf_bytes_check(file: UploadFile, data: bytes):
    """Validate file type and size."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    if len(data) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File larger than {MAX_FILE_MB} MB")


def extract_text(pdf_bytes: bytes) -> str:
    """Extract plain text from every page of the PDF."""
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text.strip()


def extract_tables(pdf_bytes: bytes):
    """Extract real tables (with lines) directly, no AI needed."""
    all_rows = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                all_rows.extend(table)
    return all_rows


def split_text(text: str, size: int = CHUNK_SIZE):
    """Split long text into chunks so it fits the model's limit."""
    return [text[i:i + size] for i in range(0, len(text), size)]


def clean_json(output: str) -> dict:
    """Models sometimes wrap JSON in ```json fences. Remove and parse."""
    output = output.replace("```json", "").replace("```", "").strip()
    start, end = output.find("{"), output.rfind("}")
    if start != -1 and end != -1:
        output = output[start:end + 1]
    return json.loads(output)


def text_to_table(chunk: str) -> dict:
    """Send one chunk of text to Hugging Face and get columns + rows."""
    prompt = f"""Convert the following document text into a table.
Return ONLY valid JSON, no explanation, in exactly this format:
{{"columns": ["col1", "col2"], "rows": [["v1", "v2"], ["v3", "v4"]]}}

Text:
{chunk}"""

    try:
        response = client.chat_completion(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.1,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Hugging Face error: {e}")

    output = response.choices[0].message.content
    try:
        return clean_json(output)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Model returned invalid JSON")


# ---------- API routes ----------

@app.get("/")
def home():
    return {"message": "Server is running. Open /docs to test."}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """PDF -> text -> Hugging Face model -> columns & rows (JSON)."""
    if not HF_TOKEN:
        raise HTTPException(status_code=500, detail="HF_TOKEN missing in .env file")

    pdf_bytes = await file.read()
    read_pdf_bytes_check(file, pdf_bytes)

    text = extract_text(pdf_bytes)
    if not text:
        raise HTTPException(
            status_code=422,
            detail="No text found. The PDF may be scanned (needs OCR).",
        )

    columns, rows = None, []
    for chunk in split_text(text):
        result = text_to_table(chunk)
        if columns is None:
            columns = result.get("columns", [])
        rows.extend(result.get("rows", []))

    return {"columns": columns or [], "rows": rows}


@app.post("/upload-tables")
async def upload_tables(file: UploadFile = File(...)):
    """PDF -> real tables directly using pdfplumber (no AI)."""
    pdf_bytes = await file.read()
    read_pdf_bytes_check(file, pdf_bytes)

    table = extract_tables(pdf_bytes)
    if not table:
        raise HTTPException(status_code=422, detail="No tables found in this PDF")

    return {"columns": table[0], "rows": table[1:]}
