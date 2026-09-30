import os

from classifiers.category_info import CATEGORIES, CATEGORY_INFO, SUBCATEGORY_PROMPTS
from classifiers.clip_backend import zero_shot_classify
from classifiers.heuristics import load_image_bgr

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "item_classifier.onnx")
_LABELS_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "item_labels.txt")

_ONNX_SESSION = None
_ONNX_LABELS = None

# Precompute just the {subtype_label: prompt} mapping for the CLIP call.
_SUBCATEGORY_PROMPT_MAP = {label: prompt for label, (_category, prompt) in SUBCATEGORY_PROMPTS.items()}
_SUBCATEGORY_GROUP_MAP = {label: category for label, (category, _prompt) in SUBCATEGORY_PROMPTS.items()}


def _try_load_onnx():
    """Load the ONNX model once, if the file exists. Returns None if unavailable."""
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
        _ONNX_LABELS = CATEGORIES

    return _ONNX_SESSION


def _classify_with_model(image_bgr):
    """Trained model gives a top-level category only (no sub-category) unless you extend it."""
    import cv2
    import numpy as np

    session = _ONNX_SESSION
    input_name = session.get_inputs()[0].name

    resized = cv2.resize(image_bgr, (224, 224))
    # Match the ImageNet preprocessing used by train_classifier.py. Feeding
    # [0, 1] pixels here instead of normalized pixels makes the trained model
    # see a very different input distribution and can wreck its predictions.
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype("float32") / 255.0
    mean = np.asarray([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.asarray([0.229, 0.224, 0.225], dtype=np.float32)
    rgb = (rgb - mean) / std
    chw = np.transpose(rgb, (2, 0, 1))
    batch = np.expand_dims(chw, axis=0)

    outputs = session.run(None, {input_name: batch})
    scores = outputs[0][0].astype("float64")
    scores -= scores.max()
    probabilities = np.exp(scores) / np.exp(scores).sum()
    best_idx = int(probabilities.argmax())
    confidence = float(probabilities[best_idx])
    category = _ONNX_LABELS[best_idx] if best_idx < len(_ONNX_LABELS) else "unknown"

    # A low score is not a useful disposal recommendation. Abstain instead.
    if confidence < 0.45:
        return "unknown", None, confidence

    return category, None, confidence


def _classify_with_heuristic(image_bgr):
    """Do not guess a disposal category from image color or edge statistics."""
    return "unknown", None, 0.0


def classify_item(image_bytes: bytes):
    """
    Returns: {
        "category": str,
        "sub_category": str or None,
        "confidence": float,
        "bin": str,
        "guidance": str,
        "separations": [str, ...],
        "description": str,
        "positive_impact_percent": int,
        "negative_impact_percent": int,
        "explanation": str,
        "source": "model" | "clip" | "heuristic",
    }
    """
    image_bgr = load_image_bgr(image_bytes)

    session = _try_load_onnx()
    if session is not None:
        category, sub_category, confidence = _classify_with_model(image_bgr)
        source = "model"
    else:
        sub_category, confidence = zero_shot_classify(
            image_bgr, _SUBCATEGORY_PROMPT_MAP, _SUBCATEGORY_GROUP_MAP
        )
        if sub_category is not None:
            category, _prompt = SUBCATEGORY_PROMPTS[sub_category]
            if category != "unknown" and confidence < 0.40:
                category, sub_category = "unknown", None
            source = "clip"
        else:
            category, sub_category, confidence = _classify_with_heuristic(image_bgr)
            source = "heuristic"

    info = CATEGORY_INFO.get(category, CATEGORY_INFO["hazardous"])

    return {
        "category": category,
        "sub_category": sub_category,
        "confidence": round(confidence, 2),
        "bin": info["bin"],
        "guidance": info["guidance"],
        "separations": info["separations"],
        "description": info["description"],
        "positive_impact_percent": info["positive_impact_percent"],
        "negative_impact_percent": info["negative_impact_percent"],
        "explanation": info["explanation"],
        "source": source,
    }
