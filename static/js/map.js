/**
 * map.js
 * Interactive civic map controller for Hyderabad using Leaflet and OpenStreetMap.
 */

let mapInstance = null;
let markersLayer = null;
let allComplaintsData = [];

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  setupMapFilters();
  loadMapComplaints();
});

function initMap() {
  const mapEl = document.getElementById("mainLeafletMap");
  if (!mapEl) return;

  // Hyderabad coordinates center
  const hydLat = 17.3850;
  const hydLng = 78.4867;

  mapInstance = L.map("mainLeafletMap", {
    zoomControl: true,
    scrollWheelZoom: true
  }).setView([hydLat, hydLng], 12);

  // Free OpenStreetMap Tile Layer
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(mapInstance);

  markersLayer = L.layerGroup().addTo(mapInstance);
}

function getMarkerColor(status) {
  switch (status) {
    case "Reported": return "#ef4444";
    case "Under Review": return "#f59e0b";
    case "Action Taken": return "#0284c7";
    case "Resolved": return "#10b981";
    default: return "#64748b";
  }
}

function createPinIcon(status) {
  const color = getMarkerColor(status);
  return L.divIcon({
    className: "civic-map-marker",
    html: `
      <div style="
        background-color: ${color};
        width: 22px;
        height: 22px;
        border-radius: 50%;
        border: 3px solid #ffffff;
        box-shadow: 0 2px 6px rgba(0,0,0,0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-size: 10px;
        font-weight: 800;
      ">
      </div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12]
  });
}

async function loadMapComplaints() {
  try {
    const res = await fetch("/api/complaints");
    if (!res.ok) throw new Error("Failed to load complaints");
    const data = await res.json();
    allComplaintsData = data.complaints || [];
    renderMarkers(allComplaintsData);
  } catch (err) {
    console.error("Error loading map points:", err);
  }
}

function renderMarkers(complaints) {
  if (!markersLayer) return;
  markersLayer.clearLayers();

  const feedEl = document.getElementById("mapComplaintsFeed");
  const countEl = document.getElementById("mapPinCount");
  if (countEl) countEl.textContent = complaints.length;

  if (feedEl) feedEl.innerHTML = "";

  complaints.forEach((c) => {
    const icon = createPinIcon(c.status);
    const marker = L.marker([c.latitude, c.longitude], { icon });

    const popupHtml = `
      <div style="font-family: 'Plus Jakarta Sans', sans-serif; min-width: 200px; padding: 4px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <strong style="font-family: monospace; color: #0284c7;">${c.tracking_id}</strong>
          ${getStatusBadge(c.status)}
        </div>
        <div style="font-size: 0.88rem; font-weight: 700; color: #0f172a; margin-bottom: 4px;">${c.category} Issue</div>
        <div style="font-size: 0.8rem; color: #475569; margin-bottom: 8px; line-height: 1.4;">${c.summary}</div>
        <div style="font-size: 0.74rem; color: #64748b; margin-bottom: 10px;">📍 ${c.locality}${c.landmark ? ' (' + c.landmark + ')' : ''}</div>
        <button onclick="openComplaintModal('${c.tracking_id}')" style="
          width: 100%;
          background: #0284c7;
          color: #ffffff;
          border: none;
          padding: 6px 10px;
          border-radius: 6px;
          font-size: 0.78rem;
          font-weight: 600;
          cursor: pointer;
        ">
          View Details & Timeline &rarr;
        </button>
      </div>
    `;

    marker.bindPopup(popupHtml);
    markersLayer.addLayer(marker);

    // Also populate sidebar item
    if (feedEl) {
      const item = document.createElement("div");
      item.style.cssText = "background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; font-size: 0.8rem; cursor: pointer;";
      item.innerHTML = `
        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
          <strong style="color: #0284c7; font-family: monospace;">${c.tracking_id}</strong>
          ${getStatusBadge(c.status)}
        </div>
        <div style="font-weight: 600; color: #0f172a;">${c.locality} &bull; ${c.category}</div>
        <div style="color: #64748b; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${c.raw_description}</div>
      `;
      item.addEventListener("click", () => {
        if (mapInstance) {
          mapInstance.setView([c.latitude, c.longitude], 15);
          marker.openPopup();
        }
      });
      feedEl.appendChild(item);
    }
  });
}

function setupMapFilters() {
  const categoryFilter = document.getElementById("mapCategoryFilter");
  const statusFilter = document.getElementById("mapStatusFilter");
  const localityJump = document.getElementById("mapLocalityJump");

  function applyFilters() {
    const selectedCat = categoryFilter.value;
    const selectedStatus = statusFilter.value;

    const filtered = allComplaintsData.filter((c) => {
      const matchCat = (selectedCat === "All" || c.category === selectedCat);
      const matchStatus = (selectedStatus === "All" || c.status === selectedStatus);
      return matchCat && matchStatus;
    });

    renderMarkers(filtered);
  }

  if (categoryFilter) categoryFilter.addEventListener("change", applyFilters);
  if (statusFilter) statusFilter.addEventListener("change", applyFilters);

  if (localityJump) {
    localityJump.addEventListener("change", () => {
      const selected = localityJump.options[localityJump.selectedIndex];
      const lat = parseFloat(selected.getAttribute("data-lat"));
      const lng = parseFloat(selected.getAttribute("data-lng"));

      if (lat && lng && mapInstance) {
        mapInstance.setView([lat, lng], 14, { animate: true });
      }
    });
  }
}
