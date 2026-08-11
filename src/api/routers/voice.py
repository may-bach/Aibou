import re
import edge_tts
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/voice", tags=["voice"])

VOICE_PROFILES = [
    {
        "id": "en-US-ChristopherNeural",
        "name": "Christopher",
        "gender": "Male",
        "style": "Chill & Confident (Default)",
        "description": "Natural, confident companion tone."
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy",
        "gender": "Male",
        "style": "Casual Co-Author",
        "description": "Energetic and conversational."
    },
    {
        "id": "en-US-EricNeural",
        "name": "Eric",
        "gender": "Male",
        "style": "Sharp & Direct",
        "description": "Punchy, clear, and focused."
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny",
        "gender": "Female",
        "style": "Expressive & Vibrant",
        "description": "Warm, engaging, and articulate."
    },
    {
        "id": "en-US-AnaNeural",
        "name": "Ana",
        "gender": "Female",
        "style": "Casual & Soft",
        "description": "Relaxed and friendly tone."
    }
]

def clean_markdown_for_tts(text: str) -> str:
    # Strip code blocks, links, and markdown formatting so TTS reads cleanly
    text = re.sub(r'```[\s\S]*?```', ' [code snippet omitted] ', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'[*_]{1,3}(.*?)[*_]{1,3}', r'\1', text)
    text = re.sub(r'^[*\-+>]\s+', '', text, flags=re.MULTILINE)
    # Phonetic fix: Ensure TTS pronounces Aibou as "Eye-boh" (ai-bo) instead of "Eye-boo"
    text = re.sub(r'\bAibou\b', 'Aibo', text)
    text = re.sub(r'\baibou\b', 'aibo', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


@router.get("/voices")
async def get_available_voices():
    return {"voices": VOICE_PROFILES}

@router.get("/speak")
async def stream_speech(
    text: str = Query(..., min_length=1, max_length=5000),
    voice: str = Query("en-US-ChristopherNeural")
):
    clean_text = clean_markdown_for_tts(text)
    if not clean_text:
        raise HTTPException(status_code=400, detail="Text content is empty after stripping markdown.")

    try:
        communicate = edge_tts.Communicate(text=clean_text, voice=voice)

        async def audio_generator():
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]

        return StreamingResponse(
            audio_generator(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline",
                "Cache-Control": "public, max-age=3600"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice synthesis error: {str(e)}")
