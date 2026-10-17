/**
 * admin.js
 * Admin portal status updating and duplicate review controller.
 */

document.addEventListener("DOMContentLoaded", () => {
  setupAdminModal();
  setupAdminFormSubmit();
});

function setupAdminModal() {
  const modal = document.getElementById("adminUpdateModal");
  const closeBtn = document.getElementById("adminModalCloseBtn");
  const cancelBtn = document.getElementById("adminCancelBtn");

  if (closeBtn && modal) {
    closeBtn.addEventListener("click", () => {
      modal.style.display = "none";
    });
  }

  if (cancelBtn && modal) {
    cancelBtn.addEventListener("click", () => {
      modal.style.display = "none";
    });
  }

  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.style.display = "none";
      }
    });
  }
}

/**
 * Opens admin status update modal
 */
function openAdminUpdateModal(complaintId, trackingId, currentStatus, category, locality) {
  const modal = document.getElementById("adminUpdateModal");
  const trackingBadge = document.getElementById("adminModalTrackingId");
  const idInput = document.getElementById("adminModalComplaintId");
  const overview = document.getElementById("adminModalOverview");
  const statusSelect = document.getElementById("adminStatusSelect");
  const noteText = document.getElementById("adminNoteText");

  if (!modal) return;

  idInput.value = complaintId;
  trackingBadge.textContent = trackingId;
  overview.innerHTML = `<strong>${category}</strong> in <strong>${locality}</strong> (Current Status: <code>${currentStatus}</code>)`;
  statusSelect.value = currentStatus;
  noteText.value = "";

  modal.style.display = "flex";
}

/**
 * Handles status update AJAX submit
 */
function setupAdminFormSubmit() {
  const form = document.getElementById("adminUpdateForm");
  const submitBtn = document.getElementById("adminSubmitBtn");
  const modal = document.getElementById("adminUpdateModal");

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const complaint_id = document.getElementById("adminModalComplaintId").value;
    const status = document.getElementById("adminStatusSelect").value;
    const admin_note = document.getElementById("adminNoteText").value.trim();
    const officer_name = document.getElementById("adminOfficerName").value.trim() || "Ward Officer (Admin)";

    submitBtn.disabled = true;
    submitBtn.textContent = "Updating Status...";

    try {
      const res = await fetch("/api/admin/status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          complaint_id,
          status,
          admin_note,
          officer_name
        })
      });

      const result = await res.json();
      if (!res.ok) {
        throw new Error(result.error || "Update failed.");
      }

      showToast(result.message, "success");

      // Update badge in table row
      const badgeCell = document.getElementById(`status-badge-${complaint_id}`);
      if (badgeCell) {
        badgeCell.innerHTML = getStatusBadge(status);
      }

      modal.style.display = "none";
    } catch (err) {
      showToast(err.message || "Failed to update status", "error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Save & Dispatch Update";
    }
  });
}
