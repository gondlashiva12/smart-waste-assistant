# Smart Waste Assistant

Two features, one app, both running on-device:

1. **Scan Item** — photograph a single item, get told which bin it goes in
2. **Report Bin** — photograph a public bin/area, flag overflow/littering,
   and if flagged, one-tap forward a pre-filled report to GHMC via WhatsApp

Built for the Snapdragon® AI Lab Build & Present Challenge.

```
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

**Item classifier** (plastic / paper / organic / e-waste / hazardous):
use a public dataset like **TrashNet**, remapped to these five folders,
then:
```bash
python train_classifier.py --data ./dataset/items --out item_classifier
```

**Bin classifier** (clean / moderate / overflowing): no public dataset
matches this exact task, so collect your own — a few dozen phone photos
per class (search "overflowing bin", "clean street" for reference
examples, plus your own local photos) is enough for a hackathon-scale
model:
```bash
python train_classifier.py --data ./dataset/bins --out bin_classifier
```

Each run produces `models/<name>.onnx` and a matching `_labels.txt` —
drop these in and restart the app; it'll use the real model automatically
and the UI will stop showing the "placeholder heuristic" note.

---

## 3. Deploying on the Snapdragon NPU

Once you have a trained `.onnx` model and access to the HP Omnibook:

1. Install the Qualcomm AI Hub tooling:
   ```bash
   pip install qai-hub qai-hub-models
   ```
2. Use Qualcomm AI Hub to compile your ONNX model for the Hexagon NPU
   (targeting your Snapdragon X Elite/Plus device). This produces a
   QNN-compatible context binary.
3. No code changes are needed beyond that — `item_classifier.py` and
   `bin_classifier.py` already prefer `QNNExecutionProvider` automatically
   when it's available on the system:
   ```python
   providers = ["QNNExecutionProvider", "CPUExecutionProvider"] if "QNNExecutionProvider" in available \
       else ["CPUExecutionProvider"]
   ```
4. **Benchmark CPU vs NPU** on the same test image and log the latency
   difference — this is your evidence for "Technical Implementation."

If you can't get device time until late: finish and fully test everything
on CPU first, then treat the Snapdragon run as a final verification +
benchmark, not first-time debugging.

---

## 4. About the GHMC integration — be precise about this in your write-up

This app does **not** have an official integration with GHMC's backend
(no such public API exists, and building one wasn't feasible in a
hackathon timeframe). What it actually does:

- Pre-fills a WhatsApp message (issue type, GPS coordinates, a Google
  Maps link, timestamp) addressed to **GHMC's real public sanitation
  complaint WhatsApp number** (8125966586 at time of writing — verify
  this is still current before your demo)
- Lets the user save the captured photo to attach themselves, since
  WhatsApp's click-to-chat links can't attach photos automatically
  (a WhatsApp platform limitation, not something this app works around)
- The user still taps "send" in WhatsApp — nothing is sent silently

Describe it in your submission as **"a smart-assist layer on top of
GHMC's existing complaint channel"**, not an official government
integration. This is honest, still a genuinely useful feature, and won't
fall apart under a judge's first follow-up question. Mention "full API
integration once GHMC provides one" as future work if you want to note
the natural next step.

---

## 5. Project structure

| File | Purpose |
|---|---|
| `app.py` | Flask server, both API routes |
| `classifiers/item_classifier.py` | Item → waste category |
| `classifiers/bin_classifier.py` | Bin photo → clean/moderate/overflowing |
| `classifiers/heuristics.py` | Offline fallback logic (placeholder) |
| `report_ghmc.py` | Builds the WhatsApp deep link |
| `report_routes.py` | `/api/report-link` endpoint |
| `train_classifier.py` | Fine-tunes MobileNetV2 → exports ONNX |
| `templates/`, `static/` | Tabbed camera UI |

---

## 6. Submission checklist

- [ ] Train both models on real data (Section 2) — don't submit on the
      heuristic fallback alone
- [ ] Get at least one real run + latency benchmark on the Snapdragon NPU
- [ ] Record a 2–3 min demo: scan an item → report an overflowing bin →
      show the WhatsApp handoff
- [ ] Write-up frames the GHMC piece accurately (Section 4) — don't
      overclaim official integration
- [ ] Submit before Sep 30, 11:59 PM IST — early, not at the deadline
