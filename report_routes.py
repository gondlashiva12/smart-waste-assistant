"""
Flask route for the "Report to GHMC" feature.

Add this to your main app.py:

    from report_ghmc import build_ghmc_report_link

and register the /api/report-link route below (or import report_routes
and call app.register_blueprint(report_routes.bp)).
"""

from flask import Blueprint, jsonify, request

from report_ghmc import build_ghmc_report_link

bp = Blueprint("report_routes", __name__)


@bp.route("/api/report-link")
def report_link():
    severity = request.args.get("severity", "overflowing bin")
    timestamp = request.args.get("timestamp")

    latitude = request.args.get("latitude", type=float)
    longitude = request.args.get("longitude", type=float)

    url = build_ghmc_report_link(
        severity=severity,
        latitude=latitude,
        longitude=longitude,
        timestamp=timestamp,
    )
    return jsonify({"url": url})
