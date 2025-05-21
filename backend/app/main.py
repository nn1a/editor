from pathlib import Path
import shutil, uuid, re, time, json
from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

for d in [UPLOAD_DIR, TEMP_DIR, FINAL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = TEMP_DIR / filename
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
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
