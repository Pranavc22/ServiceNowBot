import os

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from io import BytesIO

from helpers.text_extraction import TranscriptReader
from pipeline import sn_pipeline

app = FastAPI(title="ServiceNow AI Agents API", version="0.1.0")

# temporary in-memory storage
TRANSCRIPTS = {}

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

@app.post("/extract-transcript")
async def extract_transcript(file: UploadFile = File(...)):
    try:
        # reader = TranscriptReader(file.file)
        contents = await file.read()  # Read file into memory
        ext = os.path.splitext(file.filename)[-1]  # Get extension from uploaded filename
        reader = TranscriptReader(BytesIO(contents), ext)
        text = reader.read()
        # Store transcript in-memory under filename (replace with DB later)
        TRANSCRIPTS[file.filename] = text
        
        return {"message": "Upload successful!", "filename": file.filename}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")
    
@app.get("/summarize-transcript/{filename}")
async def summarize_transcript(filename: str):
    if filename not in TRANSCRIPTS:
        raise HTTPException(status_code=404, detail="Transcript not found")

    transcript = TRANSCRIPTS[filename]
    try:
        result = sn_pipeline.invoke({"transcript": transcript})
        return result["summary_json"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {e}")