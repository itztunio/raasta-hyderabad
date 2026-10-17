"""
rule_engine.py
Transparent, rule-based civic analysis engine for Raasta.
Provides:
1. Category classification (Drainage, Garbage, Streetlight, Roads, Water Supply, Other)
   with support for English and Roman Urdu vocabulary.
2. Severity estimation (Low, Medium, High, Critical) with explainable rule traces.
3. Concise plain-language summary generation.
4. Potential duplicate complaint detection using text similarity and locality matching.

NOTE: This engine uses deterministic, transparent heuristic rules and does NOT rely
on paid or black-box AI APIs, ensuring complete inspectability.
"""

import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Any

# ==============================================================================
# 1. BILINGUAL VOCABULARY DICTIONARIES (English + Roman Urdu)
# ==============================================================================

CATEGORY_RULES = {
    "Drainage": {
        "keywords": [
            # English
            "drain", "drainage", "sewage", "sewer", "gutter", "manhole", "overflow",
            "overflowing", "clogged", "stagnant", "foul smell", "stink", "choked",
            "stormwater", "nalah", "nala", "pipeline leakage", "sludge",
            # Roman Urdu / Deccani Urdu
            "naali", "nali", "naala", "gutter", "badboo", "ubal", "choke", "kichad",
            "mori", "ganda pani", "paani jam", "pani jama", "gutter toot", "manhole khula",
            "overflow ho", "gandagi", "kachra nala", "sewage pani"
        ],
        "weight": 1.2
    },
    "Garbage": {
        "keywords": [
            # English
            "garbage", "trash", "waste", "debris", "dump", "dumping", "dustbin",
            "litter", "rubbish", "dumper", "refuse", "sanitation", "sweeping",
            "stench", "rot", "dead animal", "uncleaned",
            # Roman Urdu / Deccani Urdu
            "kachra", "kachrey", "kuda", "kooda", "safai", "dastbin", "kachra dabba",
            "kachra gadi", "badboo", "sadhan", "kachra phela", "gandagi", "kooda daan",
            "safai nahi", "kachra nahi uthaya", "kachra phek", "safai karamchari"
        ],
        "weight": 1.0
    },
    "Streetlight": {
        "keywords": [
            # English
            "streetlight", "street light", "lamp", "pole", "light pole", "bulb",
            "darkness", "pitch dark", "flickering", "wiring", "electric pole",
            "blackout", "illumination", "transformer sparking", "hanging wire",
            # Roman Urdu / Deccani Urdu
            "light", "batti", "pole", "bijli", "andhera", "andhera hai", "bulb phoot",
            "light band", "light nahi jal rahi", "khamba", "tar latak", "spark ho",
            "current", "bijli ka pole", "roshni nahi", "chamk", "fuse"
        ],
        "weight": 1.1
    },
    "Roads": {
        "keywords": [
            # English
            "road", "pothole", "potholes", "crater", "asphalt", "tar", "divider",
            "footpath", "sidewalk", "speed breaker", "cave-in", "excavation",
            "trench", "damaged road", "traffic hazard", "uneven road", "patchwork",
            # Roman Urdu / Deccani Urdu
            "sadak", "sarak", "rasta", "raasta", "khadda", "khadde", "gaddha", "gadde",
            "footpath", "speedbreaker", "road toot", "khudai", "pathar", "gitti",
            "sadak kharab", "rasta band", "ch चलने mein takleef", "fisal", "pothole"
        ],
        "weight": 1.0
    },
    "Water Supply": {
        "keywords": [
            # English
            "water supply", "drinking water", "tap", "pipeline", "water pressure",
            "no water", "contaminated water", "dirty water", "muddy water",
            "water tanker", "leakage", "burst pipe", "pipe burst", "smelly water",
            # Roman Urdu / Deccani Urdu
            "peene ka pani", "pani nahi", "paani nahi", "nal", "pipe toot", "borewell",
            "tanker", "ganda pani", "kala pani", "badboodar pani", "pani band",
            "motor", "pressure kam", "pani ki line", "supply nahi aayi", "do din se pani"
        ],
        "weight": 1.2
    }
}

# ==============================================================================
# 2. SEVERITY RULES (Transparent Heuristics)
# ==============================================================================

CRITICAL_TRIGGERS = [
    # English
    "open manhole", "manhole uncovered", "live wire", "hanging wire", "electric shock",
    "sparking", "accident risk", "fatal", "hospital road", "school gate", "cave in",
    "flooding inside house", "severely submerged", "ambulance blocked", "deep trench",
    # Roman Urdu
    "khula manhole", "manhole khula hai", "current lag", "tar latak", "khatra", "jaan ka khatra",
    "bada hadsa", "accident ho sakta", "school ke paas", "hospital ka rasta", "pani ghar mein",
    "doob gaya", "sparking ho rahi", "current aara"
]

HIGH_TRIGGERS = [
    # English
    "completely blocked", "entire street dark", "heavy overflow", "3 days", "4 days",
    "week", "no drinking water", "pipeline burst", "impassable", "overflowing for days",
    "dead animal decomposing", "large potholes", "traffic jam", "foul stench inside",
    # Roman Urdu
    "teen din se", "chaar din se", "hafta ho gaya", "bohot zyada", "poori sadak band",
    "pani bilkul nahi", "pipeline phat", "gari phans", "kachra sad raha", "bachon ko takleef",
    "pure mohalle mein", "poora andhera", "chalna mushkil"
]

LOW_TRIGGERS = [
    # English
    "minor", "small crack", "flickers sometimes", "painted line", "curb",
    "leaf litter", "slow leak", "cosmetic", "mild", "signboard",
    # Roman Urdu
    "thoda sa", "halka", "kabhi kabhi", "chhota khadda", "aahista"
]

# ==============================================================================
# 3. CORE RULE-BASED CLASSIFICATION
# ==============================================================================

def clean_text(text: str) -> str:
    """Normalize text to lowercase without excessive punctuation."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    return ' '.join(text.split())

def classify_complaint(text: str) -> Tuple[str, float, List[str]]:
    """
    Classifies complaint into one of:
    Drainage, Garbage, Streetlight, Roads, Water Supply, Other.
    Returns: (category, confidence_score, matched_keywords)
    """
    cleaned = clean_text(text)
    scores: Dict[str, float] = {}
    matched: Dict[str, List[str]] = {}

    for category, config in CATEGORY_RULES.items():
        score = 0.0
        found_words = []
        for kw in config["keywords"]:
            # Check whole keyword/phrase match
            pattern = r'\b' + re.escape(kw) + r'\b'
            matches = len(re.findall(pattern, cleaned))
            if matches > 0:
                score += (matches * 1.5 * config["weight"])
                found_words.append(kw)
        scores[category] = score
        matched[category] = found_words

    # Sort categories by score
    sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_cat, best_score = sorted_cats[0]

    if best_score < 1.0:
        return "Other", 0.40, ["General civic problem / no strong keyword match"]

    # Compute a normalized confidence between 0.65 and 0.98
    confidence = min(0.98, 0.60 + (best_score * 0.08))
    return best_cat, round(confidence, 2), matched[best_cat]

# ==============================================================================
# 4. SEVERITY ESTIMATOR WITH TRANSPARENT REASONING
# ==============================================================================

def estimate_severity(text: str, category: str) -> Dict[str, Any]:
    """
    Determines severity level: Low, Medium, High, Critical
    Provides transparent explanation of why this severity was assigned.
    """
    cleaned = clean_text(text)

    # 1. Critical Hazard Check
    matched_critical = [t for t in CRITICAL_TRIGGERS if re.search(r'\b' + re.escape(t) + r'\b', cleaned)]
    if matched_critical:
        return {
            "level": "Critical",
            "score": 4,
            "badge_color": "danger",
            "reason": f"Immediate safety or public health hazard triggered by keyword(s): '{', '.join(matched_critical)}'."
        }

    # 2. High Urgency Check
    matched_high = [t for t in HIGH_TRIGGERS if re.search(r'\b' + re.escape(t) + r'\b', cleaned)]
    if matched_high:
        return {
            "level": "High",
            "score": 3,
            "badge_color": "warning",
            "reason": f"Prolonged or severe civic disruption indicated by term(s): '{', '.join(matched_high)}'."
        }

    # 3. Category-specific automatic baselines
    if category == "Drainage" and ("stagnant" in cleaned or "badboo" in cleaned or "smell" in cleaned):
        return {
            "level": "High",
            "score": 3,
            "badge_color": "warning",
            "reason": "Drainage overflow with foul odor/stagnant water presents mosquito breeding and hygiene concerns."
        }

    if category == "Streetlight" and ("dark" in cleaned or "andhera" in cleaned or "night" in cleaned):
        return {
            "level": "Medium",
            "score": 2,
            "badge_color": "info",
            "reason": "Unlit street poses nocturnal pedestrian and vehicular safety concern."
        }

    # 4. Low Urgency Check
    matched_low = [t for t in LOW_TRIGGERS if re.search(r'\b' + re.escape(t) + r'\b', cleaned)]
    if matched_low:
        return {
            "level": "Low",
            "score": 1,
            "badge_color": "secondary",
            "reason": f"Non-hazardous maintenance item detected by indicator(s): '{', '.join(matched_low)}'."
        }

    # Default baseline
    return {
        "level": "Medium",
        "score": 2,
        "badge_color": "info",
        "reason": "Standard civic complaint requiring scheduled field inspection."
    }

# ==============================================================================
# 5. SUMMARY GENERATION (Deterministic, Rule-Based)
# ==============================================================================

def generate_summary(text: str, category: str, locality: str) -> str:
    """
    Produces a crisp 1-sentence standardized administrative summary.
    """
    text_clean = text.strip()
    first_sentence = text_clean.split('.')[0].strip()
    if len(first_sentence) > 90:
        first_sentence = first_sentence[:87] + "..."

    # Formulate clean administrative title/summary
    if category != "Other":
        return f"{category} grievance reported in {locality}: \"{first_sentence}\""
    return f"Civic grievance reported in {locality}: \"{first_sentence}\""

# ==============================================================================
# 6. DUPLICATE COMPLAINT DETECTION
# ==============================================================================

def compute_similarity(str1: str, str2: str) -> float:
    """
    Calculates composite text similarity using Jaccard word-overlap and SequenceMatcher.
    """
    s1 = set(clean_text(str1).split())
    s2 = set(clean_text(str2).split())

    if not s1 or not s2:
        return 0.0

    # Jaccard word overlap
    intersection = len(s1.intersection(s2))
    union = len(s1.union(s2))
    jaccard = intersection / union if union > 0 else 0.0

    # Sequence matcher on raw cleaned strings
    seq = SequenceMatcher(None, clean_text(str1), clean_text(str2)).ratio()

    # Composite metric: 60% Jaccard + 40% Sequence
    return (0.60 * jaccard) + (0.40 * seq)

def check_for_duplicates(new_text: str, new_locality: str, new_category: str,
                         existing_complaints: List[Dict[str, Any]],
                         similarity_threshold: float = 0.45) -> Tuple[bool, Dict[str, Any] | None, float]:
    """
    Scans recent complaints in the database to detect potential duplicates.
    Requires:
      1. Same locality
      2. Same category (or both related to roads/drainage)
      3. Composite text similarity >= threshold (default 45%)
    Returns: (is_duplicate, duplicate_complaint_dict, similarity_score)
    """
    best_match = None
    best_score = 0.0

    for comp in existing_complaints:
        # Don't compare with resolved complaints if they were resolved long ago,
        # but active complaints (Reported, Under Review, Action Taken) are primary candidates
        if comp.get("status") == "Resolved":
            continue

        comp_locality = comp.get("locality", "")
        # Must be in the exact same locality
        if comp_locality.strip().lower() != new_locality.strip().lower():
            continue

        comp_category = comp.get("category", "")
        if comp_category != new_category and comp_category != "Other" and new_category != "Other":
            continue

        score = compute_similarity(new_text, comp.get("raw_description", ""))
        if score > best_score:
            best_score = score
            best_match = comp

    if best_match and best_score >= similarity_threshold:
        return True, best_match, round(best_score * 100, 1)

    return False, None, round(best_score * 100, 1)

# ==============================================================================
# 7. CONSOLIDATED ANALYZER (One-Call Function)
# ==============================================================================

def analyze_complaint(description: str, locality: str, existing_complaints: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Runs full analysis pipeline for a complaint.
    Returns:
      - category
      - confidence
      - matched_keywords
      - severity (level, reason, score)
      - summary
      - duplicate_info (is_duplicate, duplicate_of_id, similarity_pct)
    """
    if existing_complaints is None:
        existing_complaints = []

    category, confidence, matched_keywords = classify_complaint(description)
    severity_info = estimate_severity(description, category)
    summary = generate_summary(description, category, locality)
    is_dup, dup_comp, dup_pct = check_for_duplicates(description, locality, category, existing_complaints)

    return {
        "category": category,
        "confidence": confidence,
        "matched_keywords": matched_keywords,
        "severity": severity_info["level"],
        "severity_score": severity_info["score"],
        "severity_reason": severity_info["reason"],
        "summary": summary,
        "is_duplicate": is_dup,
        "duplicate_of": dup_comp["tracking_id"] if dup_comp else None,
        "duplicate_similarity": dup_pct if is_dup else 0.0,
        "engine_type": "Deterministic Rule-Based NLP (English & Roman Urdu Heuristics)"
    }
