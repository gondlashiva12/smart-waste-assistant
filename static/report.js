/**
 * Report-to-GHMC flow.
 *
 * Call reportToGHMC(severity) after your on-device model flags a bin as
 * overflowing/littered. It grabs the device location (with graceful
 * fallback if denied), asks the backend to build the pre-filled WhatsApp
 * message, and opens it. The user still attaches the photo and taps
 * send in WhatsApp themselves - this code never sends anything silently.
 */

async function reportToGHMC(severity) {
  const timestamp = new Date().toISOString();

  function openReportLink(latitude, longitude) {
    const params = new URLSearchParams({ severity, timestamp });
    if (latitude != null && longitude != null) {
      params.set("latitude", latitude);
      params.set("longitude", longitude);
    }

    fetch(`/api/report-link?${params.toString()}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.url) {
          window.open(data.url, "_blank");
        } else {
          alert("Could not build the report link. Please try again.");
        }
      })
      .catch(() => alert("Could not reach the server to build the report link."));
  }

  if (!navigator.geolocation) {
    openReportLink(null, null);
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => openReportLink(position.coords.latitude, position.coords.longitude),
    () => {
      // Location denied or unavailable - still let the report go through without GPS.
      openReportLink(null, null);
    },
    { timeout: 5000 }
  );
}
