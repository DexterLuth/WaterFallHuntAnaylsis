import requests
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

# Arizona bounding box
LAT_MIN, LAT_MAX = 31.33, 37.00
LON_MIN, LON_MAX = -114.82, -109.05
STEP_DEG = 0.5  # grid resolution in degrees
DATE = "2026-05-22"
TZID = "America/Phoenix"

# Build grid
lat_pts = np.arange(LAT_MIN, LAT_MAX + STEP_DEG, STEP_DEG)
lon_pts = np.arange(LON_MIN, LON_MAX + STEP_DEG, STEP_DEG)
grid = [(round(lat, 4), round(lon, 4)) for lat in lat_pts for lon in lon_pts]
print(f"Querying {len(grid)} points over Arizona ({STEP_DEG}° grid) for {DATE}…")


def fetch_sun(lat, lon):
    url = "https://api.sunrise-sunset.org/json"
    r = requests.get(
        url,
        params={
            "lat": lat,
            "lng": lon,
            "date": DATE,
            "formatted": 0,
            "tzid": TZID,
        },
        timeout=10,
    )
    r.raise_for_status()
    res = r.json()["results"]
    return {
        "lat": lat,
        "lon": lon,
        "sunrise": res["sunrise"],
        "sunset": res["sunset"],
        "solar_noon": res["solar_noon"],
        "day_length_sec": res["day_length"],
        "civil_twilight_begin": res["civil_twilight_begin"],
        "civil_twilight_end": res["civil_twilight_end"],
        "nautical_twilight_begin": res["nautical_twilight_begin"],
        "nautical_twilight_end": res["nautical_twilight_end"],
        "astronomical_twilight_begin": res["astronomical_twilight_begin"],
        "astronomical_twilight_end": res["astronomical_twilight_end"],
    }


rows = []
errors = []
with ThreadPoolExecutor(max_workers=8) as ex:
    futures = {ex.submit(fetch_sun, lat, lon): (lat, lon) for lat, lon in grid}
    for i, future in enumerate(as_completed(futures), 1):
        lat, lon = futures[future]
        try:
            rows.append(future.result())
        except Exception as e:
            errors.append((lat, lon, str(e)))
        if i % 20 == 0 or i == len(grid):
            print(f"  {i}/{len(grid)} done")

sun_df = pd.DataFrame(rows).sort_values(["lat", "lon"]).reset_index(drop=True)

# Add day_length in hours for readability
sun_df["day_length_hr"] = (sun_df["day_length_sec"] / 3600).round(4)

sun_df.to_csv("arizona_sunrise_sunset.csv", index=False)
print(f"\nSaved {len(sun_df)} rows → arizona_sunrise_sunset.csv")
if errors:
    print(f"Errors: {errors}")
