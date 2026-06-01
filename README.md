# AI Gym Posture Detector

Webcam or video-based exercise analysis with MediaPipe Pose: skeleton overlay, rep counting, form score (0–100), and live feedback. CPU only.

## Exercises

| Exercise | Type |
|----------|------|
| Squat | reps |
| Deadlift | reps |
| Plank | hold |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

First run downloads the pose model into `assets/` (~6 MB).

## Run

```bash
python run.py
python run.py --exercise deadlift
python run.py --video assets/test_videos/squat.mp4 --exercise squat
```

Side view, full body in frame.

| Key | Action |
|-----|--------|
| `q` | Quit |
| `r` | Reset |
| `1` / `2` / `3` | Squat / Deadlift / Plank |

## Tests

```bash
pytest
```

## Stack

Python 3.12+, OpenCV, MediaPipe, NumPy, pytest
