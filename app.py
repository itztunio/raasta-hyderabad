"""
app.py
Raasta — Hyderabad's Smart Civic Problem Solver
Flask Application Server

Routes:
- GET  /                     : Homepage with citizen stats and quick tools
- GET  /report               : Complaint reporting form (English / Roman Urdu)
- GET  /complaints           : Public complaints list with live status tracking
- GET  /map                  : Fullscreen interactive civic map of Hyderabad
- GET  /admin                : Protected demo admin dashboard
- POST /admin/login          : Admin demo authentication
- GET  /admin/logout         : Admin logout
- POST /api/preview          : Real-time rule-based preview (category, severity, duplicates)
- POST /api/complaints       : Submit a new complaint
- GET  /api/complaints       : Fetch complaints with query filters
- GET  /api/complaint/<id>   : Fetch single complaint with timeline
- POST /api/admin/status     : Update complaint status & add timeline entry
- GET  /api/stats            : Platform summary metrics
- GET  /api/localities       : List of Hyderabad localities & GPS coordinates
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import secrets

from database import (
    init_db, seed_initial_data_if_empty, add_complaint, get_all_complaints,
    get_complaint_by_id, get_complaint_by_tracking_id, update_complaint_status,
    get_timeline_for_complaint, get_stats
)
from rule_engine import analyze_complaint
from localities import HYDERABAD_LOCALITIES, HYDERABAD_CENTER, get_locality_coords, find_nearest_locality

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(16))

# Demo Admin Credentials (Educational / Prototype Use)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me-locally")
ADMIN_PASSWORD = "admin123"

# Initialize DB on start
with app.app_context():
    init_db()
    seed_initial_data_if_empty()

# ==============================================================================
# HTML TEMPLATE ROUTES
# ==============================================================================

@app.route("/")
def index():
    stats = get_stats()
    recent_complaints = get_all_complaints()[:5]
    return render_template(
        "index.html",
        stats=stats,
        recent_complaints=recent_complaints,
        localities=HYDERABAD_LOCALITIES
    )

@app.route("/report")
def report():
    return render_template(
        "report.html",
        localities=HYDERABAD_LOCALITIES,
        hyderabad_center=HYDERABAD_CENTER
    )

@app.route("/complaints")
def complaints():
    track_param = request.args.get("track", "").strip()
    category_param = request.args.get("category", "All")
    status_param = request.args.get("status", "All")
    locality_param = request.args.get("locality", "All")
    search_param = request.args.get("search", "").strip()

    all_complaints = get_all_complaints(
        category=category_param,
        status=status_param,
        locality=locality_param,
        search=search_param or track_param
    )

    return render_template(
        "complaints.html",
        complaints=all_complaints,
        localities=HYDERABAD_LOCALITIES,
        selected_category=category_param,
        selected_status=status_param,
        selected_locality=locality_param,
        search_query=search_param or track_param,
        track_param=track_param
    )

@app.route("/map")
def map_view():
    return render_template(
        "map_view.html",
        localities=HYDERABAD_LOCALITIES,
        hyderabad_center=HYDERABAD_CENTER
    )

@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        return render_template("admin_login.html")
    
    stats = get_stats()
    all_complaints = get_all_complaints()
    return render_template(
        "admin.html",
        stats=stats,
        complaints=all_complaints,
        localities=HYDERABAD_LOCALITIES
    )

@app.route("/admin/login", methods=["POST"])
def admin_login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session["is_admin"] = True
        return redirect(url_for("admin"))
    
    return render_template(
        "admin_login.html",
        error="Invalid demo credentials. Use 'admin' and 'admin123'."
    )

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin"))

# ==============================================================================
# REST API ENDPOINTS
# ==============================================================================

@app.route("/api/preview", methods=["POST"])
def api_preview():
    """
    Real-time rule-based grievance analysis.
    Takes description & locality, runs transparent NLP, detects duplicates.
    """
    data = request.get_json() or {}
    description = data.get("description", "").strip()
    locality = data.get("locality", "Charminar").strip()

    if not description:
        return jsonify({"error": "Description cannot be empty"}), 400

    existing = get_all_complaints()
    analysis = analyze_complaint(description, locality, existing)
    return jsonify(analysis)

@app.route("/api/complaints", methods=["GET", "POST"])
def api_complaints():
    if request.method == "POST":
        data = request.get_json() or {}
        raw_description = data.get("description", "").strip()
        locality = data.get("locality", "").strip()
        landmark = data.get("landmark", "").strip()
        citizen_name = data.get("citizen_name", "").strip() or "Anonymous Citizen"
        citizen_phone = data.get("citizen_phone", "").strip()
        
        lat = data.get("latitude")
        lng = data.get("longitude")

        if not raw_description or not locality:
            return jsonify({"error": "Description and Locality are mandatory fields."}), 400

        # Validate or resolve coordinates
        if lat is None or lng is None:
            default_lat, default_lng = get_locality_coords(locality)
            lat, lng = default_lat, default_lng

        try:
            lat = float(lat)
            lng = float(lng)
        except (ValueError, TypeError):
            lat, lng = get_locality_coords(locality)

        # Run transparent rule engine
        existing = get_all_complaints()
        analysis = analyze_complaint(raw_description, locality, existing)

        complaint_payload = {
            "citizen_name": citizen_name,
            "citizen_phone": citizen_phone,
            "locality": locality,
            "landmark": landmark,
            "latitude": lat,
            "longitude": lng,
            "raw_description": raw_description,
            "category": analysis["category"],
            "severity": analysis["severity"],
            "severity_reason": analysis["severity_reason"],
            "summary": analysis["summary"],
            "is_duplicate": analysis["is_duplicate"],
            "duplicate_of": analysis["duplicate_of"] or "",
            "duplicate_similarity": analysis["duplicate_similarity"]
        }

        created = add_complaint(complaint_payload)
        return jsonify({
            "success": True,
            "complaint": created,
            "analysis": analysis,
            "message": f"Complaint successfully filed with Tracking ID: {created['tracking_id']}"
        }), 201

    # GET method - fetch complaints
    category = request.args.get("category")
    status = request.args.get("status")
    locality = request.args.get("locality")
    search = request.args.get("search")
    severity = request.args.get("severity")

    complaints_list = get_all_complaints(
        category=category,
        status=status,
        locality=locality,
        search=search,
        severity=severity
    )
    return jsonify({"complaints": complaints_list})

@app.route("/api/complaint/<tracking_id>", methods=["GET"])
def api_get_complaint(tracking_id):
    """Retrieves full details and timeline for a complaint."""
    complaint = get_complaint_by_tracking_id(tracking_id)
    if not complaint:
        # Check by numeric ID as fallback
        if tracking_id.isdigit():
            complaint = get_complaint_by_id(int(tracking_id))
    
    if not complaint:
        return jsonify({"error": "Complaint not found"}), 404

    timeline = get_timeline_for_complaint(complaint["id"])
    return jsonify({
        "complaint": complaint,
        "timeline": timeline
    })

@app.route("/api/admin/status", methods=["POST"])
def api_admin_update_status():
    """Allows demo admin to update status and add notes."""
    if not session.get("is_admin"):
        return jsonify({"error": "Unauthorized. Please login to the demo admin portal."}), 403

    data = request.get_json() or {}
    complaint_id = data.get("complaint_id")
    new_status = data.get("status")
    admin_note = data.get("admin_note", "").strip()
    officer_name = data.get("officer_name", "").strip() or "GHMC Ward Officer (Demo)"

    if not complaint_id or not new_status:
        return jsonify({"error": "complaint_id and status are required."}), 400

    success = update_complaint_status(
        complaint_id=int(complaint_id),
        new_status=new_status,
        admin_note=admin_note,
        admin_name=officer_name
    )

    if not success:
        return jsonify({"error": "Invalid status or update failed."}), 400

    updated = get_complaint_by_id(int(complaint_id))
    timeline = get_timeline_for_complaint(int(complaint_id))

    return jsonify({
        "success": True,
        "complaint": updated,
        "timeline": timeline,
        "message": f"Status updated to '{new_status}' successfully."
    })

@app.route("/api/stats", methods=["GET"])
def api_stats():
    return jsonify(get_stats())

@app.route("/api/localities", methods=["GET"])
def api_localities():
    return jsonify({
        "center": HYDERABAD_CENTER,
        "localities": HYDERABAD_LOCALITIES
    })

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
