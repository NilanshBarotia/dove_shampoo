from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil

from video_to_frames import extract_frames

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
FRAMES_DIR = Path("frames")

UPLOAD_DIR.mkdir(exist_ok=True)
FRAMES_DIR.mkdir(exist_ok=True)

@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    video_path = UPLOAD_DIR / file.filename

    # Save video
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Frame output folder per video
    frames_out = FRAMES_DIR / file.filename.replace(".", "_")

    # Extract frames
    frame_info = extract_frames(
        video_path=str(video_path),
        output_dir=str(frames_out)
    )

    return {
        "status": "success",
        "video_path": str(video_path.resolve()),
        "frames_dir": frame_info["frames_dir"],
        "frames_extracted": frame_info["frames_extracted"],
        "duration_sec": frame_info["duration_sec"]
    }
