import cv2
import os
import math

def compute_target_frames(duration_sec: float) -> int:
    if duration_sec <= 10:
        return 200
    extra_blocks = math.floor((duration_sec - 10) / 10)
    return 200 + extra_blocks * 150


def extract_frames(video_path: str, output_dir: str):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps

    target_frames = compute_target_frames(duration_sec)
    target_frames = min(target_frames, total_frames)

    os.makedirs(output_dir, exist_ok=True)

    step = total_frames / target_frames
    frame_indices = [int(i * step) for i in range(target_frames)]

    saved = 0
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        success, frame = cap.read()
        if not success:
            continue

        cv2.imwrite(
            os.path.join(output_dir, f"frame_{saved:05d}.jpg"),
            frame
        )
        saved += 1

    cap.release()

    return {
        "duration_sec": round(duration_sec, 2),
        "frames_extracted": saved,
        "frames_dir": output_dir
    }
