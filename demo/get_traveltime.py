import requests

def get_journey_time(from_station, to_station="940GZZLUAGL"):
    url = f"https://api.tfl.gov.uk/Journey/JourneyResults/{from_station}/to/{to_station}"
    params = {
        # Add your API credentials if registered, optional for light use
        # "app_id": "...",
        # "app_key": "..."
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        journey = data['journeys'][0]
        duration = journey['duration']
        return duration
    else:
        print(f"Error fetching journey from {from_station} to {to_station}")
        return None

# Example:
stations = ["940GZZLUCAR", "940GZZLUCAR", "940GZZLUODS"]
for station in stations:
    duration = get_journey_time(station)
    print(f"{station} → Bank: {duration} minutes")
