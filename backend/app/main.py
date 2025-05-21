from pathlib import Path
import shutil, uuid, re, time, json
from datetime import datetime, timezone
import aiofiles
from fastapi import FastAPI, UploadFile, File, HTTPException  # Added HTTPException
from fastapi.concurrency import (
    run_in_threadpool,
)  # Added for running sync code in thread pool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import magic  # Added import for python-magic

from app.safe_html import sanitize_html
from fastapi_utils.tasks import repeat_every

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
TEMP_DIR = UPLOAD_DIR / "temp"
FINAL_DIR = UPLOAD_DIR / "final"

# Define allowed image MIME types
ALLOWED_IMAGE_MIME_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
# Define allowed image extensions (lowercase)
ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "webp"]


for d in [UPLOAD_DIR, TEMP_DIR, FINAL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    # Validate file extension
    ext = file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid image extension.")

    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = TEMP_DIR / filename

    content = await file.read()
    await file.seek(0)  # Reset file pointer after reading for magic

    # Validate MIME type using python-magic, run in thread pool to avoid blocking
    mime_type = await run_in_threadpool(magic.from_buffer, content, mime=True)
    if mime_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type: {mime_type}. Only JPEG, PNG, GIF, WEBP are allowed.",
        )

    # Basic check: ensure extension matches detected mime type (optional, but good practice)
    # This is a simplified check. More robust mapping might be needed for all cases.
    expected_ext_for_mime = {
        "image/jpeg": ["jpg", "jpeg"],
        "image/png": ["png"],
        "image/gif": ["gif"],
        "image/webp": ["webp"],
    }
    if ext not in expected_ext_for_mime.get(mime_type, []):
        raise HTTPException(
            status_code=400,
            detail=f"File extension '{ext}' does not match detected image type '{mime_type}'.",
        )

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    return {"url": f"/uploads/temp/{filename}"}


@app.post("/api/save")
def save_html(data: dict):
    raw_html = data.get("html", "")

    used_images = set(re.findall(r'/uploads/temp/([^"]+)', raw_html))

    for filename in used_images:
        src = TEMP_DIR / filename
        dst = FINAL_DIR / filename
        if src.exists():
            shutil.move(str(src), str(dst))
            raw_html = raw_html.replace(
                f"/uploads/temp/{filename}", f"/uploads/final/{filename}"
            )

    safe_html = sanitize_html(raw_html)

    data_to_save = {
        "html": safe_html,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with open("test.db", "wb") as f:
        f.write(json.dumps(data_to_save).encode("utf-8"))
    return {"status": "ok"}


@app.get("/api/load")
def load_html():
    try:
        with open("test.db", "rb") as f:
            content_bytes = f.read()
        if content_bytes:
            doc = json.loads(content_bytes.decode("utf-8"))
            return {"html": doc.get("html", "")}
    except FileNotFoundError:
        return {"html": ""}  # Return empty if file doesn't exist
    except json.JSONDecodeError:
        return {"html": ""}  # Return empty if file content is not valid JSON
    return {"html": ""}


@app.on_event("startup")
@repeat_every(seconds=3600)
def cleanup_temp_images():
    now = time.time()
    for file in TEMP_DIR.glob("*"):
        if file.stat().st_mtime < now - 3600:
            file.unlink()
