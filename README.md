# AI Gym Posture Detector

Computer-vision app that analyzes gym exercises from a **webcam** or a **video file**
(e.g. a clip filmed on your phone at the gym). It detects body landmarks with
**MediaPipe Pose**, draws a skeleton, counts repetitions, and scores your form
in real time. Runs on CPU — no GPU required.

## Features

- Real-time pose landmarks + skeleton overlay (MediaPipe Tasks API)
- **Rep counting** via an angle-driven finite-state machine
- **Form Score 0–100** with an A–F grade and per-set average
- Live, exercise-specific **form feedback** (depth, back angle, hip sag, etc.)
- Two input modes: **webcam** or **video file**
- Switch exercises live with number keys
- Extensible engine: add a new exercise by writing one small class

## Supported exercises

| Exercise | Type | Form checks |
|----------|------|-------------|
| **Squat** | reps | depth, chest up, knees past toes |
| **Deadlift** | reps | hip hinge, flat back, tall lockout |
| **Plank** | hold (time) | body straight, hip sag / pike |

> Why these three? They track cleanly from a **side view** with 2D pose
> estimation. Lying lifts (bench/dumbbell press) are intentionally excluded —
> the bench and bar occlude the body and 2D pose is unreliable there.

## Requirements

- Python 3.12+
- Webcam (or a video file)

## Setup

```bash
cd ai-gym-posture-detector
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

On first run the app downloads a small MediaPipe pose model into `assets/` (~6 MB).

## Run

```bash
# Webcam, squat (default)
python run.py

# Pick an exercise
python run.py --exercise deadlift
python run.py --exercise plank

# Analyze a video filmed on your phone
python run.py --video assets/test_videos/my_squats.mp4 --exercise squat
```

Film yourself **from the side** with your full body in frame.

### Controls

| Key | Action |
|-----|--------|
| `q` | Quit |
| `r` | Reset reps / score |
| `1` | Squat |
| `2` | Deadlift |
| `3` | Plank |

## Tests

```bash
pytest
```

## Project layout

```
app/
  main.py            # Webcam/video loop
  pose_detector.py   # MediaPipe Pose (Tasks API) + drawing
  landmarks.py       # Named landmark access
  angle_utils.py     # Angle math (pure functions)
  overlay.py         # HUD: reps, form score, feedback
  exercises/
    base.py          # FSM rep counting, form score, duration holds
    squat.py
    deadlift.py
    plank.py
    __init__.py      # Exercise registry
assets/test_videos/  # Put sample clips here
outputs/
tests/
run.py
```

## How it works

1. **Pose** — MediaPipe returns 33 body landmarks per frame.
2. **Angles** — joint angles (knee, hip, torso, body line) are computed from
   the more-visible body side and smoothed over a short window.
3. **State machine** — the primary angle drives stages (`up → down → up`); a rep
   is counted on a full cycle, with a minimum-duration filter against jitter.
4. **Form score** — each exercise runs form rules that deduct points and emit
   feedback; the score maps to an A–F grade, averaged per set.

## Tech stack

- Python · OpenCV · MediaPipe · NumPy · pytest

## License

MIT (add a LICENSE file before publishing).
