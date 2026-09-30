"""
Smart Waste Assistant - Flask backend.

Two modes, one app:
  1. Scan Item     -> classifies a photographed item into a waste category
  2. Report Bin    -> checks a photographed bin/area for overflow/littering,
                       and if flagged, offers a one-tap WhatsApp handoff to
                       GHMC's real sanitation complaint line.
"""

from flask import Flask, jsonify, render_template, request

from classifiers.bin_classifier import check_bin
from classifiers.item_classifier import classify_item
from report_routes import bp as report_bp

app = Flask(__name__)
app.register_blueprint(report_bp)


@app.after_request
def add_no_cache_headers(response):
    # Prevent any browser/proxy from caching the classification results
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan-item", methods=["POST"])
def scan_item():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image_bytes = request.files["image"].read()

    try:
        result = classify_item(image_bytes)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(result)


@app.route("/api/check-bin", methods=["POST"])
def check_bin_route():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image_bytes = request.files["image"].read()

    try:
        result = check_bin(image_bytes)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(result)


@app.route("/api/health-check")
def health_check():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
