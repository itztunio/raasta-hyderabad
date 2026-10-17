"""
localities.py
Accurate geographic coordinates for prominent Hyderabad localities.
Used by Raasta to place complaints on the Leaflet map accurately without inventing coordinates.
"""

HYDERABAD_CENTER = {"lat": 17.3850, "lng": 78.4867, "zoom": 12}

HYDERABAD_LOCALITIES = {
    "Charminar": {"lat": 17.3616, "lng": 78.4747, "zone": "South Zone (Old City)"},
    "Banjara Hills": {"lat": 17.4156, "lng": 78.4357, "zone": "Khairatabad Zone"},
    "Jubilee Hills": {"lat": 17.4319, "lng": 78.4073, "zone": "Khairatabad Zone"},
    "Madhapur": {"lat": 17.4483, "lng": 78.3915, "zone": "Serilingampally Zone"},
    "Gachibowli": {"lat": 17.4401, "lng": 78.3489, "zone": "Serilingampally Zone"},
    "Hitec City": {"lat": 17.4474, "lng": 78.3762, "zone": "Serilingampally Zone"},
    "Kondapur": {"lat": 17.4622, "lng": 78.3568, "zone": "Serilingampally Zone"},
    "Kukatpally": {"lat": 17.4947, "lng": 78.3996, "zone": "Kukatpally Zone"},
    "Miyapur": {"lat": 17.4968, "lng": 78.3547, "zone": "Kukatpally Zone"},
    "Ameerpet": {"lat": 17.4375, "lng": 78.4482, "zone": "Khairatabad Zone"},
    "Begumpet": {"lat": 17.4447, "lng": 78.4664, "zone": "Secunderabad Zone"},
    "Secunderabad": {"lat": 17.4399, "lng": 78.4983, "zone": "Secunderabad Zone"},
    "Mehdipatnam": {"lat": 17.3916, "lng": 78.4439, "zone": "Khairatabad Zone"},
    "Tolichowki": {"lat": 17.3998, "lng": 78.4111, "zone": "Khairatabad Zone"},
    "Dilsukhnagar": {"lat": 17.3688, "lng": 78.5247, "zone": "L.B. Nagar Zone"},
    "Malakpet": {"lat": 17.3752, "lng": 78.4998, "zone": "Charminar Zone"},
    "Koti": {"lat": 17.3833, "lng": 78.4842, "zone": "Charminar Zone"},
    "Abids": {"lat": 17.3912, "lng": 78.4735, "zone": "Charminar Zone"},
    "Himayatnagar": {"lat": 17.4042, "lng": 78.4878, "zone": "Khairatabad Zone"},
    "Nampally": {"lat": 17.3871, "lng": 78.4688, "zone": "Khairatabad Zone"},
    "Musheerabad": {"lat": 17.4168, "lng": 78.5028, "zone": "Secunderabad Zone"},
    "Amberpet": {"lat": 17.3976, "lng": 78.5147, "zone": "Secunderabad Zone"},
    "Tarnaka": {"lat": 17.4283, "lng": 78.5317, "zone": "Secunderabad Zone"},
    "Uppal": {"lat": 17.4057, "lng": 78.5591, "zone": "L.B. Nagar Zone"},
    "L.B. Nagar": {"lat": 17.3524, "lng": 78.5510, "zone": "L.B. Nagar Zone"},
    "Bahadurpura": {"lat": 17.3564, "lng": 78.4526, "zone": "Charminar Zone"},
    "Falaknuma": {"lat": 17.3317, "lng": 78.4674, "zone": "Charminar Zone"},
    "Chandrayangutta": {"lat": 17.3204, "lng": 78.4842, "zone": "Charminar Zone"},
    "Sanathnagar": {"lat": 17.4578, "lng": 78.4414, "zone": "Kukatpally Zone"},
    "Malkajgiri": {"lat": 17.4514, "lng": 78.5323, "zone": "Secunderabad Zone"},
    "Alwal": {"lat": 17.5042, "lng": 78.5115, "zone": "Secunderabad Zone"},
    "Bowenpally": {"lat": 17.4764, "lng": 78.4883, "zone": "Secunderabad Zone"},
    "Manikonda": {"lat": 17.4024, "lng": 78.3751, "zone": "Serilingampally Zone"},
    "Lingampally": {"lat": 17.4851, "lng": 78.3223, "zone": "Serilingampally Zone"},
    "Somajiguda": {"lat": 17.4265, "lng": 78.4578, "zone": "Khairatabad Zone"}
}

def get_locality_coords(locality_name: str):
    """
    Returns (lat, lng) for a given locality name.
    Falls back to Hyderabad center with a deterministic slight offset if locality is unknown.
    """
    if locality_name in HYDERABAD_LOCALITIES:
        loc = HYDERABAD_LOCALITIES[locality_name]
        return loc["lat"], loc["lng"]
    return HYDERABAD_CENTER["lat"], HYDERABAD_CENTER["lng"]

def find_nearest_locality(lat: float, lng: float):
    """
    Finds the closest Hyderabad locality name for given coordinates (Euclidean approx).
    """
    best_loc = "Charminar"
    min_dist = float("inf")
    for name, data in HYDERABAD_LOCALITIES.items():
        dist = (data["lat"] - lat) ** 2 + (data["lng"] - lng) ** 2
        if dist < min_dist:
            min_dist = dist
            best_loc = name
    return best_loc
