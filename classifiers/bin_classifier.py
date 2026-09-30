"""
Bin overflow / littering classifier.

Same three-tier pattern as item_classifier.py: trained ONNX model, if
present -> zero-shot CLIP (recommended default, no training needed) ->
offline edge/color heuristic as a last-resort fallback. See README.md
for training/converting a real model.
"""

import os

from classifiers.clip_backend import zero_shot_classify
from classifiers.heuristics import extract_features, load_image_bgr

STATES = ["clean", "moderate", "overflowing"]

_CLIP_PROMPTS = {
    "clean": "a photo of a clean, empty, or tidy waste bin or street area",
    "moderate": "a photo of a waste bin that is partially full or an area with some scattered litter",
    "overflowing": "a photo of an overflowing waste bin or a street covered in garbage and litter",
}

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "bin_classifier.onnx")
_LABELS_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "bin_labels.txt")

_ONNX_SESSION = None
_ONNX_LABELS = None


def _try_load_onnx():
    global _ONNX_SESSION, _ONNX_LABELS

    if _ONNX_SESSION is not None:
        return _ONNX_SESSION

    if not os.path.exists(_MODEL_PATH):
        return None

    import onnxruntime as ort

    available = ort.get_available_providers()
    providers = ["QNNExecutionProvider", "CPUExecutionProvider"] if "QNNExecutionProvider" in available \
        else ["CPUExecutionProvider"]

    _ONNX_SESSION = ort.InferenceSession(_MODEL_PATH, providers=providers)

    if os.path.exists(_LABELS_PATH):
        with open(_LABELS_PATH, "r", encoding="utf-8") as f:
            _ONNX_LABELS = [line.strip() for line in f if line.strip()]
    else:
        _ONNX_LABELS = STATES

    return _ONNX_SESSION


def _classify_with_model(image_bgr):
    import cv2
    import numpy as np

    session = _ONNX_SESSION
    input_name = session.get_inputs()[0].name

    resized = cv2.resize(image_bgr, (224, 224))
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype("float32") / 255.0
    chw = np.transpose(rgb, (2, 0, 1))
    batch = np.expand_dims(chw, axis=0)

    outputs = session.run(None, {input_name: batch})
    scores = outputs[0][0]
    best_idx = int(scores.argmax())
    confidence = float(scores[best_idx])
    label = _ONNX_LABELS[best_idx] if best_idx < len(_ONNX_LABELS) else "unknown"

    return label, confidence


def _classify_with_heuristic(image_bgr):
    features = extract_features(image_bgr)

    # Higher edge density + higher color variance -> more visual clutter,
    # which is a rough (not accurate) proxy for overflow/littering.
    clutter_score = (features["edge_density"] * 0.6) + (min(features["color_std"] / 80.0, 1.0) * 0.4)

    if clutter_score > 0.35:
        return "overflowing", round(min(0.4 + clutter_score, 0.9), 2)
    if clutter_score > 0.20:
        return "moderate", round(0.4 + clutter_score * 0.3, 2)
    return "clean", round(0.5, 2)


def check_bin(image_bytes: bytes):
    """
    Returns: {
        "state": "clean" | "moderate" | "overflowing",
        "confidence": float,
        "source": "model" | "heuristic",
    }
    """
    image_bgr = load_image_bgr(image_bytes)

    session = _try_load_onnx()
    if session is not None:
        state, confidence = _classify_with_model(image_bgr)
        source = "model"
    else:
        state, confidence = zero_shot_classify(image_bgr, _CLIP_PROMPTS)
        if state is not None:
            source = "clip"
        else:
            state, confidence = _classify_with_heuristic(image_bgr)
            source = "heuristic"

    return {
        "state": state,
        "confidence": confidence,
        "source": source,
    }
