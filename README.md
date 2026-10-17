# Raasta — Hyderabad's Smart Civic Problem Solver
> **"Report a problem. Find a solution. Track the change."**

A modern, transparent, community-driven web application tailored for citizens across Hyderabad's wards and municipal zones. Raasta enables residents to voice civic issues in both **English and Roman Urdu**, automatically categorizes complaints, evaluates severity using deterministic transparent rules (with zero paid AI fees), identifies potential duplicate complaints, and tracks progress through field resolution on an interactive OpenStreetMap.

---

## 🏛️ Civic Educational Prototype Notice
> **Disclaimer:** Raasta is an educational simulation and civic technology prototype for Hyderabad citizens. It is **not** officially connected to or dispatched by the Greater Hyderabad Municipal Corporation (GHMC), HMDA, or HMWS&SB.

---

## 🚀 Features at a Glance

1. **Modern Hyderabad-Themed Homepage**:
   - Clean civic layout with real-time grievance counters (Total, Reported, In Progress, Resolved).
   - Instant Tracking ID lookup box (`HYD-2026-XXXX`).
   - Recent grievances feed from wards like Charminar, Madhapur, Kukatpally, Mehdipatnam, etc.

2. **Bilingual Grievance Filing (English & Roman Urdu)**:
   - Supports everyday local expressions (e.g., *"Sadak pe bada khaddha hai"*, *"Gutter overflow ho raha hai"*, *"Light band hai andhera hai"*, *"Peene ka pani nahi aa raha"*).
   - One-click template pills to test common civic scenarios instantly.

3. **Transparent Rule-Based Triage (Zero Paid AI)**:
   - Categorizes into: **Drainage**, **Garbage**, **Streetlight**, **Roads**, **Water Supply**, or **Other**.
   - Determines severity: **Low**, **Medium**, **High**, or **Critical** based on explicit, inspectable safety triggers (e.g., *"khula manhole"*, *"current lag sakta hai"*, *"open wire"*).
   - Outputs clear reasoning explaining *why* the priority was assigned.

4. **Duplicate Prevention Engine**:
   - Uses text similarity (Jaccard word-overlap + sequence matching) across open grievances in the same locality.
   - Alerts citizens and administrators if a neighbor already reported the same issue nearby, preventing duplicated field efforts.

5. **Permanent SQLite Database with Resolution Timelines**:
   - Stores all grievances with unique IDs (`HYD-2026-1001`).
   - Maintains a verifiable audit timeline:
     $$\text{Reported} \longrightarrow \text{Under Review} \longrightarrow \text{Action Taken} \longrightarrow \text{Resolved}$$

6. **Interactive Leaflet & OpenStreetMap**:
   - Centered on Hyderabad (`17.3850, 78.4867`) with 35+ verified locality coordinates.
   - Color-coded pins (🔴 Red: Reported, 🟠 Amber: Under Review, 🔵 Blue: Action Taken, 🟢 Green: Resolved).
   - Ward selector that auto-pans the map directly to areas like Banjara Hills, Jubilee Hills, Secunderabad, Begumpet, Dilsukhnagar, etc.

7. **Protected Demo Admin Dashboard**:
   - Protected console for ward officers (Username: `admin`, Password: `admin123`).
   - Review complaints, view duplicate warnings, update statuses, and log official progress notes.

---

## 📁 Beginner's Guide: Project Structure Explained Simply

| File / Folder | What It Does (In Simple Terms) |
|---|---|
| [`app.py`](app.py) | **The Main Engine:** Starts the Flask web server, connects web pages with the database, and provides API endpoints. |
| [`database.py`](database.py) | **The Memory:** Creates and manages the SQLite database (`raasta.db`), records grievances, and tracks status history. |
| [`rule_engine.py`](rule_engine.py) | **The Brain:** Deterministic Python code that reads English & Roman Urdu words, classifies categories, assigns severity, and detects duplicates. |
| [`localities.py`](localities.py) | **The Map Coordinates:** Stores genuine GPS coordinates for 35+ Hyderabad localities so pins never invent random locations. |
| [`templates/`](templates/) | **The HTML Pages:** User-facing layouts for the Homepage, Report Form, Public Registry, Interactive Map, and Admin Console. |
| [`static/css/`](static/css/) | **The Styles:** Colors, cards, badges, mobile responsiveness, and clean typography. |
| [`static/js/`](static/js/) | **Interactive Logic:** Manages Leaflet maps, live preview updates as you type, and popup modals. |
| [`test_app.py`](test_app.py) | **Automated Tests:** Python test suite verifying that every feature works properly without errors. |

---

## 💻 Simple Windows Setup & Run Instructions

### Step 1: Open PowerShell or Command Prompt
Open your terminal and navigate to the project directory:
```powershell
cd C:\Users\DELL\.gemini\antigravity\scratch\raasta_hyderabad
```

### Step 2: Install Flask (if not already installed)
```powershell
pip install -r requirements.txt
```

### Step 3: Run the Automated Tests (Optional, verifies everything)
```powershell
python test_app.py
```
You should see: `Ran 10 tests ... OK`.

### Step 4: Start the Raasta Web Application
```powershell
python app.py
```

### Step 5: Open in Your Browser
Open your favorite web browser and visit:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Demo Admin Credentials
To test the administrative status update features:
- **URL**: [http://127.0.0.1:5000/admin](http://127.0.0.1:5000/admin)
- **Username**: `admin`
- **Password**: `admin123`
