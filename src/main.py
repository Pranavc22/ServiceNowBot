import os

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from io import BytesIO

from agents.servicenow_agent import ServiceNowAgent
from helpers.text_extraction import TranscriptReader
from models import PushStoriesRequest, PushStoriesResponse
from pipeline import sn_pipeline
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ServiceNow AI Agents API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],             # <-- for production, replace with list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# temporary in-memory storage
TRANSCRIPTS = {}

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

@app.post("/extract-transcript")
async def extract_transcript(file: UploadFile = File(...)):
    try:
        contents = await file.read() 
        ext = os.path.splitext(file.filename)[-1]  
        reader = TranscriptReader(BytesIO(contents), ext)
        text = reader.read()
        
        # Store temporarily
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
    
@app.post("/push-stories", response_model=PushStoriesResponse)
async def push_stories(payload: PushStoriesRequest):
    sn_agent = ServiceNowAgent()
    if not payload.confirmed_stories:
        raise HTTPException(status_code=400, detail="No confirmed stories provided")

    created_stories = []

    for story in payload.confirmed_stories:
        try:
            if story.action_type.lower() == "create":
                result = sn_agent.create_story(
                    requested_for_sys_id=payload.requestor_sys_id,
                    short_description=story.short_desc,
                    acceptance_criteria=story.acceptance_criteria,
                    assigned_to_sys_id=payload.requestor_sys_id
                )
                created_stories.append(result.get("result", {}))

            elif story.action_type.lower() == "update":
                update_payload = {}
                if story.acceptance_criteria:
                    update_payload["acceptance_criteria"] = story.acceptance_criteria

                if not update_payload:
                    created_stories.append({
                        "error": "No update fields provided",
                        "short_desc": story.short_desc
                    })
                    continue

                result = sn_agent.update_story(
                    short_desc=story.short_desc,
                    updates=update_payload
                )
                created_stories.append(result.get("result", {}))

            else:
                created_stories.append({
                    "error": f"Unknown action_type '{story.action_type}'",
                    "short_desc": story.short_desc
                })

        except Exception as e:
            created_stories.append({"error": str(e), "short_desc": story.short_desc})

    return {"created_stories": created_stories}
