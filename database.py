"""
database.py
SQLite database manager for Raasta — Hyderabad's Smart Civic Problem Solver.
Manages persistent storage for complaints and public progress timelines.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raasta.db")

def get_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite schema if not already created."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tracking_id TEXT UNIQUE NOT NULL,
        citizen_name TEXT DEFAULT 'Anonymous Citizen',
        citizen_phone TEXT DEFAULT '',
        locality TEXT NOT NULL,
        landmark TEXT DEFAULT '',
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        raw_description TEXT NOT NULL,
        category TEXT NOT NULL,
        severity TEXT NOT NULL,
        severity_reason TEXT NOT NULL,
        summary TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Reported',
        is_duplicate INTEGER DEFAULT 0,
        duplicate_of TEXT DEFAULT '',
        duplicate_similarity REAL DEFAULT 0.0,
        admin_notes TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        note TEXT NOT NULL,
        updated_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (complaint_id) REFERENCES complaints (id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

def generate_tracking_id(cursor) -> str:
    """Generates unique civic tracking ID like HYD-2026-1001."""
    cursor.execute("SELECT COUNT(*) FROM complaints")
    count = cursor.fetchone()[0]
    return f"HYD-2026-{1000 + count + 1}"

def add_complaint(data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserts a new complaint and creates initial timeline entry."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    tracking_id = generate_tracking_id(cursor)

    cursor.execute("""
        INSERT INTO complaints (
            tracking_id, citizen_name, citizen_phone, locality, landmark,
            latitude, longitude, raw_description, category, severity,
            severity_reason, summary, status, is_duplicate, duplicate_of,
            duplicate_similarity, admin_notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tracking_id,
        data.get("citizen_name") or "Anonymous Citizen",
        data.get("citizen_phone", ""),
        data["locality"],
        data.get("landmark", ""),
        float(data["latitude"]),
        float(data["longitude"]),
        data["raw_description"],
        data["category"],
        data["severity"],
        data["severity_reason"],
        data["summary"],
        "Reported",
        1 if data.get("is_duplicate") else 0,
        data.get("duplicate_of", "") or "",
        float(data.get("duplicate_similarity", 0.0)),
        "",
        now,
        now
    ))

    complaint_id = cursor.lastrowid

    # Create initial timeline record
    cursor.execute("""
        INSERT INTO timeline (complaint_id, status, note, updated_by, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        complaint_id,
        "Reported",
        "Citizen submitted grievance via Raasta civic web portal. Initial rule-based severity and category assigned.",
        "System Engine",
        now
    ))

    conn.commit()
    conn.close()

    return get_complaint_by_id(complaint_id)

def get_complaint_by_id(complaint_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves single complaint by primary key id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_complaint_by_tracking_id(tracking_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves single complaint by public tracking ID (e.g. HYD-2026-1001)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints WHERE UPPER(tracking_id) = UPPER(?)", (tracking_id.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_complaints(category: str = None, status: str = None, locality: str = None,
                       search: str = None, severity: str = None) -> List[Dict[str, Any]]:
    """Fetches complaints with optional filtering and search."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM complaints WHERE 1=1"
    params = []

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if status and status != "All":
        query += " AND status = ?"
        params.append(status)

    if locality and locality != "All":
        query += " AND locality = ?"
        params.append(locality)

    if severity and severity != "All":
        query += " AND severity = ?"
        params.append(severity)

    if search:
        s = f"%{search.strip()}%"
        query += " AND (tracking_id LIKE ? OR raw_description LIKE ? OR locality LIKE ? OR landmark LIKE ? OR summary LIKE ?)"
        params.extend([s, s, s, s, s])

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_timeline_for_complaint(complaint_id: int) -> List[Dict[str, Any]]:
    """Retrieves chronological progress events for a complaint."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM timeline WHERE complaint_id = ? ORDER BY id ASC", (complaint_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_complaint_status(complaint_id: int, new_status: str, admin_note: str = "", admin_name: str = "Admin Desk") -> bool:
    """Updates complaint status, saves admin remarks, and appends a timeline entry."""
    valid_statuses = ["Reported", "Under Review", "Action Taken", "Resolved"]
    if new_status not in valid_statuses:
        return False

    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE complaints
        SET status = ?, admin_notes = ?, updated_at = ?
        WHERE id = ?
    """, (new_status, admin_note or "", now, complaint_id))

    note_text = admin_note if admin_note else f"Status transitioned to '{new_status}' by {admin_name}."
    cursor.execute("""
        INSERT INTO timeline (complaint_id, status, note, updated_by, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        complaint_id,
        new_status,
        note_text,
        admin_name,
        now
    ))

    conn.commit()
    conn.close()
    return True

def get_stats() -> Dict[str, Any]:
    """Computes high-level platform statistics for homepage and dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM complaints")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Reported'")
    reported = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Under Review'")
    under_review = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Action Taken'")
    action_taken = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'")
    resolved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE is_duplicate = 1")
    duplicates = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE severity IN ('High', 'Critical')")
    high_priority = cursor.fetchone()[0]

    # Category counts
    cursor.execute("SELECT category, COUNT(*) as count FROM complaints GROUP BY category")
    cat_counts = {row["category"]: row["count"] for row in cursor.fetchall()}

    conn.close()

    return {
        "total": total,
        "reported": reported,
        "under_review": under_review,
        "action_taken": action_taken,
        "resolved": resolved,
        "duplicates": duplicates,
        "high_priority": high_priority,
        "category_counts": cat_counts
    }

def seed_initial_data_if_empty():
    """Seeds realistic Hyderabad civic complaints if database is newly initialized."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM complaints")
    count = cursor.fetchone()[0]
    conn.close()

    if count > 0:
        return

    from localities import HYDERABAD_LOCALITIES
    from rule_engine import analyze_complaint

    seed_items = [
        {
            "citizen_name": "Syed Rizwan",
            "citizen_phone": "9849012345",
            "locality": "Charminar",
            "landmark": "Near Gulzar Houz circle",
            "raw_description": "Gutter ubal raha hai aur sadak par ganda pani fail gaya hai, khula manhole khatra bana hua hai.",
            "status": "Reported"
        },
        {
            "citizen_name": "Pooja Reddy",
            "citizen_phone": "9701023456",
            "locality": "Madhapur",
            "landmark": "Opposite Inorbit Mall junction",
            "raw_description": "Main streetlights are completely off for the last 3 days. Pitch dark stretch causing high risk for two wheelers and night pedestrians.",
            "status": "Under Review"
        },
        {
            "citizen_name": "K. Venkatesh",
            "citizen_phone": "9988776655",
            "locality": "Kukatpally",
            "landmark": "Near KPHB Phase 3 ground",
            "raw_description": "Large garbage dump accumulation not cleared for a week. Heavy foul smell and stray dogs tearing plastic bags on the walkway.",
            "status": "Action Taken"
        },
        {
            "citizen_name": "Mohammed Farhan",
            "citizen_phone": "9848112233",
            "locality": "Mehdipatnam",
            "landmark": "Pillar No 45, PVNR Expressway",
            "raw_description": "Sadak pe bohot bada khaddha hai, heavy rain se asphalt toot gaya aur gaadi fisal rahi hai.",
            "status": "Resolved"
        },
        {
            "citizen_name": "Ananya Sharma",
            "citizen_phone": "9618033445",
            "locality": "Banjara Hills",
            "landmark": "Road No 12, near cancer hospital turn",
            "raw_description": "Drinking water supply pipeline burst. Clean municipal water leaking onto the main road since morning.",
            "status": "Under Review"
        },
        {
            "citizen_name": "Ramesh Goud",
            "citizen_phone": "9959144556",
            "locality": "Secunderabad",
            "landmark": "Near Clock Tower market lane",
            "raw_description": "Kachra dabba toot gaya aur kooda raste par bikhar gaya hai, safai nahi hui do din se.",
            "status": "Reported"
        },
        {
            "citizen_name": "Mirza Baig",
            "citizen_phone": "9849988776",
            "locality": "Tolichowki",
            "landmark": "Near Paramount Colony entrance",
            "raw_description": "Sewage pipeline choked. Wastewater backing up near residential entrance with severe foul smell.",
            "status": "Action Taken"
        },
        {
            "citizen_name": "Sneha Joshi",
            "citizen_phone": "9100223344",
            "locality": "Gachibowli",
            "landmark": "Near DLF Cybercity Back Gate",
            "raw_description": "Streetlight pole wiring loose and hanging dangerously near sidewalk. Sparking observed during evening drizzle.",
            "status": "Reported"
        }
    ]

    for item in seed_items:
        loc_data = HYDERABAD_LOCALITIES.get(item["locality"], {"lat": 17.3850, "lng": 78.4867})
        analysis = analyze_complaint(item["raw_description"], item["locality"], [])
        
        comp_payload = {
            "citizen_name": item["citizen_name"],
            "citizen_phone": item["citizen_phone"],
            "locality": item["locality"],
            "landmark": item["landmark"],
            "latitude": loc_data["lat"],
            "longitude": loc_data["lng"],
            "raw_description": item["raw_description"],
            "category": analysis["category"],
            "severity": analysis["severity"],
            "severity_reason": analysis["severity_reason"],
            "summary": analysis["summary"],
            "is_duplicate": False,
            "duplicate_of": "",
            "duplicate_similarity": 0.0
        }
        comp = add_complaint(comp_payload)
        
        # If seed item had non-Reported status, update it to create realistic timelines
        if item["status"] != "Reported":
            if item["status"] == "Under Review":
                update_complaint_status(comp["id"], "Under Review", "Verification team assigned to inspect the site.", "Ward Officer 12")
            elif item["status"] == "Action Taken":
                update_complaint_status(comp["id"], "Under Review", "Verification completed. Work order issued to field team.", "Ward Officer 08")
                update_complaint_status(comp["id"], "Action Taken", "Field sanitation crew dispatched with clearance machinery.", "Sanitation Supervisor")
            elif item["status"] == "Resolved":
                update_complaint_status(comp["id"], "Under Review", "Site inspection verified road depression.", "Roads Dept Engineer")
                update_complaint_status(comp["id"], "Action Taken", "Road repair truck laid cold mix asphalt.", "Road Maintenance Crew")
                update_complaint_status(comp["id"], "Resolved", "Pothole filled and surface leveled. Inspection photos filed.", "Quality Inspector")
