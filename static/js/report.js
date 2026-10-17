/**
 * report.js
 * Handles interactive map picking, Roman Urdu quick pills,
 * real-time debounced rule preview, and complaint submission.
 */

let pickerMap = null;
let pickerMarker = null;
let previewDebounceTimer = null;

document.addEventListener("DOMContentLoaded", () => {
  initPickerMap();
  setupLocalityListener();
  setupUrduPillListeners();
  setupLivePreviewListener();
  setupFormSubmit();
});

/**
 * Initializes the Leaflet map picker
 */
function initPickerMap() {
  const mapElement = document.getElementById("pickerMap");
  if (!mapElement) return;

  const initialLat = 17.3850;
  const initialLng = 78.4867;

  pickerMap = L.map("pickerMap").setView([initialLat, initialLng], 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(pickerMap);

  // Custom pin icon
  const pinIcon = L.divIcon({
    className: "custom-map-pin",
    html: `<div style="background-color: #0284c7; width: 18px; height: 18px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });

  pickerMarker = L.marker([initialLat, initialLng], {
    draggable: true,
    icon: pinIcon
  }).addTo(pickerMap);

  // Map click updates marker & coords
  pickerMap.on("click", (e) => {
    updateCoordinates(e.latlng.lat, e.latlng.lng);
  });

  // Marker drag updates coords
  pickerMarker.on("dragend", (e) => {
    const latlng = e.target.getLatLng();
    updateCoordinates(latlng.lat, latlng.lng);
  });
}

/**
 * Updates coordinates input fields & display
 */
function updateCoordinates(lat, lng) {
  const latFixed = parseFloat(lat.toFixed(5));
  const lngFixed = parseFloat(lng.toFixed(5));

  document.getElementById("latInput").value = latFixed;
  document.getElementById("lngInput").value = lngFixed;
  document.getElementById("coordsDisplay").textContent = `${latFixed}, ${lngFixed}`;

  if (pickerMarker) {
    pickerMarker.setLatLng([latFixed, lngFixed]);
  }
}

/**
 * Listen for locality selection to center map
 */
function setupLocalityListener() {
  const localitySelect = document.getElementById("localitySelect");
  if (!localitySelect) return;

  localitySelect.addEventListener("change", () => {
    const selectedOption = localitySelect.options[localitySelect.selectedIndex];
    const lat = parseFloat(selectedOption.getAttribute("data-lat"));
    const lng = parseFloat(selectedOption.getAttribute("data-lng"));

    if (lat && lng && pickerMap) {
      pickerMap.setView([lat, lng], 14);
      updateCoordinates(lat, lng);
      document.getElementById("nearestLocalityTag").textContent = `Selected: ${selectedOption.value}`;
    }

    // Trigger preview re-evaluation with updated locality
    triggerRulePreview();
  });
}

/**
 * Quick-fill sample phrases in Roman Urdu & English
 */
function setupUrduPillListeners() {
  const pills = document.querySelectorAll(".urdu-pill");
  const descInput = document.getElementById("descriptionInput");

  pills.forEach((pill) => {
    pill.addEventListener("click", () => {
      const text = pill.getAttribute("data-text");
      if (descInput && text) {
        descInput.value = text;
        descInput.focus();
        triggerRulePreview();
        showToast("Sample text loaded into description.", "info");
      }
    });
  });
}

/**
 * Debounced live rule engine preview
 */
function setupLivePreviewListener() {
  const descInput = document.getElementById("descriptionInput");
  if (!descInput) return;

  descInput.addEventListener("input", () => {
    clearTimeout(previewDebounceTimer);
    previewDebounceTimer = setTimeout(triggerRulePreview, 350);
  });
}

async function triggerRulePreview() {
  const descInput = document.getElementById("descriptionInput");
  const localitySelect = document.getElementById("localitySelect");

  const description = descInput ? descInput.value.trim() : "";
  const locality = localitySelect ? localitySelect.value : "";

  const previewCat = document.getElementById("previewCategory");
  const previewConf = document.getElementById("previewConfidence");
  const previewSev = document.getElementById("previewSeverity");
  const previewReason = document.getElementById("previewReason");
  const previewKw = document.getElementById("previewKeywords");
  const dupAlert = document.getElementById("duplicateAlertBox");

  if (!description) {
    if (previewCat) previewCat.innerHTML = `<span class="badge badge-category">Awaiting input...</span>`;
    if (previewConf) previewConf.textContent = "-- %";
    if (previewSev) previewSev.innerHTML = `<span class="badge badge-sev-low">Low</span>`;
    if (previewReason) previewReason.textContent = "Start typing problem description above to see transparent heuristic rule evaluation.";
    if (previewKw) previewKw.innerHTML = `<span style="font-size: 0.78rem; color: #94a3b8;">None</span>`;
    if (dupAlert) dupAlert.style.display = "none";
    return;
  }

  try {
    const res = await fetch("/api/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description, locality: locality || "Charminar" })
    });

    if (!res.ok) return;
    const data = await res.json();

    // 1. Category
    if (previewCat) {
      previewCat.innerHTML = `<span class="badge badge-category" style="font-size: 0.88rem;">🏷️ ${data.category}</span>`;
    }

    // 2. Confidence
    if (previewConf) {
      const confPct = Math.round(data.confidence * 100);
      previewConf.textContent = `${confPct}% Rule Match`;
    }

    // 3. Severity
    if (previewSev) {
      previewSev.innerHTML = getSeverityBadge(data.severity);
    }

    // 4. Reason
    if (previewReason) {
      previewReason.innerHTML = `<strong>Rule Trace:</strong> ${data.severity_reason}`;
    }

    // 5. Matched Keywords
    if (previewKw) {
      if (data.matched_keywords && data.matched_keywords.length > 0) {
        previewKw.innerHTML = data.matched_keywords
          .map(kw => `<span class="badge" style="background:#e2e8f0; color:#1e293b; font-size:0.75rem;">${kw}</span>`)
          .join(" ");
      } else {
        previewKw.innerHTML = `<span style="font-size: 0.78rem; color: #94a3b8;">No specific keyword triggers matched</span>`;
      }
    }

    // 6. Duplicate Alert
    if (dupAlert) {
      if (data.is_duplicate) {
        dupAlert.style.display = "block";
        dupAlert.innerHTML = `
          <div class="duplicate-alert-banner">
            ⚠️ <strong>Potential Duplicate Detected:</strong><br>
            A matching complaint (<strong>${data.duplicate_of}</strong>) was recently filed in ${locality} with ${data.duplicate_similarity}% similarity.
          </div>
        `;
      } else {
        dupAlert.style.display = "none";
      }
    }
  } catch (err) {
    console.error("Preview error:", err);
  }
}

/**
 * Handle form submission
 */
function setupFormSubmit() {
  const form = document.getElementById("complaintForm");
  const submitBtn = document.getElementById("submitBtn");

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const locality = document.getElementById("localitySelect").value;
    const description = document.getElementById("descriptionInput").value.trim();
    const landmark = document.getElementById("landmarkInput").value.trim();
    const citizen_name = document.getElementById("citizenName").value.trim();
    const citizen_phone = document.getElementById("citizenPhone").value.trim();
    const latitude = parseFloat(document.getElementById("latInput").value);
    const longitude = parseFloat(document.getElementById("lngInput").value);

    if (!locality) {
      showToast("Please choose a Hyderabad locality.", "error");
      return;
    }
    if (!description) {
      showToast("Please enter the problem description.", "error");
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Lodging Grievance...</span>`;

    try {
      const res = await fetch("/api/complaints", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          locality,
          description,
          landmark,
          citizen_name,
          citizen_phone,
          latitude,
          longitude
        })
      });

      const result = await res.json();
      if (!res.ok) {
        throw new Error(result.error || "Submission failed.");
      }

      showToast(result.message, "success");

      // Reset form
      form.reset();
      triggerRulePreview();

      // Open detail modal with newly created complaint
      setTimeout(() => {
        openComplaintModal(result.complaint.tracking_id);
      }, 500);

    } catch (err) {
      showToast(err.message || "An error occurred while submitting.", "error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
        Submit Civic Grievance
      `;
    }
  });
}
