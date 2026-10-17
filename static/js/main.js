/**
 * main.js
 * Common UI helpers, toast notifications, and modal tracking controllers for Raasta.
 */

// Mobile Navigation Toggle
document.addEventListener("DOMContentLoaded", () => {
  const mobileToggle = document.getElementById("mobileToggle");
  const navMenu = document.getElementById("navMenu");

  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener("click", () => {
      navMenu.classList.toggle("open");
    });
  }

  // Modal Close Listeners
  const modal = document.getElementById("complaintModal");
  const closeBtn = document.getElementById("modalCloseBtn");
  if (closeBtn && modal) {
    closeBtn.addEventListener("click", () => {
      modal.style.display = "none";
    });
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.style.display = "none";
      }
    });
  }
});

/**
 * Shows non-blocking toast alert
 */
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${message}</span>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

/**
 * Returns HTML badge string for status
 */
function getStatusBadge(status) {
  let badgeClass = "badge-status-reported";
  if (status === "Under Review") badgeClass = "badge-status-review";
  if (status === "Action Taken") badgeClass = "badge-status-action";
  if (status === "Resolved") badgeClass = "badge-status-resolved";

  return `<span class="badge ${badgeClass}">${status}</span>`;
}

/**
 * Returns HTML badge string for severity
 */
function getSeverityBadge(severity) {
  let badgeClass = "badge-sev-medium";
  if (severity === "Critical") badgeClass = "badge-sev-critical";
  if (severity === "High") badgeClass = "badge-sev-high";
  if (severity === "Low") badgeClass = "badge-sev-low";

  return `<span class="badge ${badgeClass}">${severity} Severity</span>`;
}

/**
 * Renders the 4-step progress bar
 */
function renderProgressBar(currentStatus) {
  const steps = ["Reported", "Under Review", "Action Taken", "Resolved"];
  const currentIndex = steps.indexOf(currentStatus);

  let html = `<div class="tracker-steps">`;
  steps.forEach((step, idx) => {
    let stateClass = "";
    if (idx < currentIndex) stateClass = "completed";
    else if (idx === currentIndex) stateClass = "active";

    html += `
      <div class="tracker-step ${stateClass}">
        <div class="tracker-dot">${idx + 1}</div>
        <div class="tracker-step-title">${step}</div>
      </div>
    `;
  });
  html += `</div>`;
  return html;
}

/**
 * Fetches single complaint data from /api/complaint/<id> and opens the details modal
 */
async function openComplaintModal(trackingId) {
  const modal = document.getElementById("complaintModal");
  const modalTitle = document.getElementById("modalTitle");
  const trackingBadge = document.getElementById("modalTrackingBadge");
  const modalBody = document.getElementById("modalBodyContent");

  if (!modal || !modalBody) return;

  modalBody.innerHTML = `
    <div style="text-align: center; padding: 30px; color: #64748b;">
      Loading grievance details for <strong>${trackingId}</strong>...
    </div>
  `;
  modal.style.display = "flex";

  try {
    const res = await fetch(`/api/complaint/${encodeURIComponent(trackingId)}`);
    if (!res.ok) {
      throw new Error("Complaint not found");
    }
    const data = await res.json();
    const c = data.complaint;
    const timeline = data.timeline || [];

    trackingBadge.textContent = c.tracking_id;
    modalTitle.textContent = `${c.category} Issue — ${c.locality}`;

    let duplicateHtml = "";
    if (c.is_duplicate) {
      duplicateHtml = `
        <div class="duplicate-alert-banner">
          ⚠️ <strong>Potential Duplicate Notice:</strong> This issue matches previous complaint
          <strong><a href="javascript:void(0)" onclick="openComplaintModal('${c.duplicate_of}')" style="color: inherit; text-decoration: underline;">${c.duplicate_of}</a></strong>
          in ${c.locality} (Similarity: ${c.duplicate_similarity}%).
        </div>
      `;
    }

    let timelineItemsHtml = "";
    timeline.forEach((item) => {
      timelineItemsHtml += `
        <div class="timeline-item">
          <div class="timeline-dot"></div>
          <div class="timeline-time">${item.created_at} &bull; <span class="timeline-by">${item.updated_by}</span></div>
          <div style="font-weight: 600; color: #0f172a; margin-top: 2px;">Status: ${item.status}</div>
          <div class="timeline-note">${item.note}</div>
        </div>
      `;
    });

    modalBody.innerHTML = `
      ${duplicateHtml}
      
      <div style="margin-bottom: 16px;">
        ${renderProgressBar(c.status)}
      </div>

      <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px;">
        ${getStatusBadge(c.status)}
        ${getSeverityBadge(c.severity)}
        <span class="badge badge-category">${c.category}</span>
        <span class="badge" style="background:#f1f5f9; color:#475569;">📍 ${c.locality}${c.landmark ? ' (' + c.landmark + ')' : ''}</span>
      </div>

      <div style="margin-bottom: 14px;">
        <h4 style="font-size: 0.88rem; color: #475569; margin-bottom: 4px; text-transform: uppercase;">Citizen Description</h4>
        <p style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; font-size: 0.92rem; line-height: 1.5;">
          ${c.raw_description}
        </p>
      </div>

      <div style="margin-bottom: 14px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 12px;">
        <h4 style="font-size: 0.82rem; color: #166534; text-transform: uppercase; margin-bottom: 2px;">Transparent Rule-Based Diagnosis</h4>
        <div style="font-size: 0.86rem; color: #14532d;">${c.severity_reason}</div>
      </div>

      <div style="margin-top: 20px;">
        <h4 style="font-size: 0.9rem; font-weight: 700; color: #0f172a; margin-bottom: 10px;">Resolution Timeline & Verification Logs</h4>
        <div class="timeline-list">
          ${timelineItemsHtml}
        </div>
      </div>

      <div style="margin-top: 24px; padding-top: 14px; border-top: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: #64748b;">
        <span>GPS: ${c.latitude.toFixed(4)}, ${c.longitude.toFixed(4)}</span>
        <span>Lodged: ${c.created_at}</span>
      </div>
    `;
  } catch (err) {
    modalBody.innerHTML = `
      <div style="padding: 24px; text-align: center; color: #b91c1c;">
        <h4>Grievance Not Found</h4>
        <p style="font-size: 0.9rem; margin-top: 6px;">Unable to find grievance with tracking reference: <strong>${trackingId}</strong>.</p>
      </div>
    `;
  }
}
