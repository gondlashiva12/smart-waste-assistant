
        ┌── Scan Item ──► [item_classifier] ──► category + bin guidance
camera ─┤
        └── Report Bin ─► [bin_classifier] ──► clean/moderate/overflowing
                                 │
                          (if flagged) ──► WhatsApp deep link to GHMC
                                            (pre-filled: severity, GPS, time)
```

---

## 1. Local setup

```bash
cd waste_assistant
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`, allow camera access, switch between the
**Scan Item** and **Report Bin** tabs.

**The app works immediately with no training step**, using a simple
offline heuristic (color/edge analysis in `classifiers/heuristics.py`)
as a placeholder. This is clearly labeled in the UI ("placeholder
heuristic - swap in a trained model") and in code comments — it exists
so you always have a working, demoable app, not as your final AI model.
**Train the real models (Section 2) before your submission.**

---

## 2. Training the real models

Both classifiers auto-load a trained ONNX model from `models/` if present,
and only fall back to the heuristic if the file is missing. So training
is a drop-in swap — no other code changes needed.

