"""
GHMC reporting module.

Builds a WhatsApp "click-to-chat" deep link pre-filled with the report
details (severity, location, timestamp), pointed at GHMC's sanitation
complaint WhatsApp number. WhatsApp's click-to-chat API cannot attach a
photo automatically (this is a WhatsApp platform limitation, not
something we can work around) - the user attaches the photo themselves
once the chat opens. This is a deliberate, honest design choice rather
than a shortcut: no official GHMC API access is needed, and nothing is
sent without the citizen's final tap.

IMPORTANT: verify this number is still current before your demo -
municipal helpline numbers do change. As of writing, GHMC's sanitation
WhatsApp complaint line is 8125966586.
"""

from urllib.parse import quote

GHMC_WHATSAPP_NUMBER = "918125966586"  # country code + number, no "+" or spaces


def build_ghmc_report_link(severity: str, latitude: float = None, longitude: float = None,
                            address: str = None, timestamp: str = None) -> str:
    """


    severity: e.g. "overflowing bin", "littering / open dumping"
    latitude/longitude: from the browser's geolocation API, if granted
    address: optional human-readable location if you reverse-geocoded it
    timestamp: ISO string; caller supplies this so it reflects capture time
    """
    lines = [
        "Sanitation complaint (auto-generated report):",
        f"Issue: {severity}",
    ]

    if address:
        lines.append(f"Location: {address}")
    if latitude is not None and longitude is not None:
        lines.append(f"GPS: {latitude:.6f}, {longitude:.6f}")
        lines.append(f"Map: https://maps.google.com/?q={latitude:.6f},{longitude:.6f}")
    if timestamp:
        lines.append(f"Reported at: {timestamp}")

    lines.append("")
    lines.append("(Photo attached separately - please see attachment)")

    message = "\n".join(lines)
    return f"https://wa.me/{GHMC_WHATSAPP_NUMBER}?text={quote(message)}"
