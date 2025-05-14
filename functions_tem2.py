func_desp = {
    "traffic volume": """Provides traffic count data.

Example:
```python
def get_traffic_volume(sensor_id, date):
    query = f"SELECT * FROM traffic_data WHERE sensor_id = '{sensor_id}' AND date = '{date}'"
    return execute_query(query)
```""",

    "weather": """
- natural language queries: what's the weather in Manchester on 1 Jan 2023 and 2 Jan 2023?
- Python code:
$$$
import psycopg2
from datetime import datetime

def query_weather_data():
    conn_params = {
        "dbname": "manchester_p",
        "user": "postgres",
        "host": "localhost",
        "password": "zhaomin199" #this is the only correct password
    }
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        cur.execute("SELECT date, visibility, windspeed, max, min, precipitation, snowdepth, weatherextra FROM weather_data WHERE date >= '2023-01-01' AND date < '2023-01-03';")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print(query_weather_data())
$$$
""",

    "poi": """
- natural language queries: what's the POI near Manchester Piccadilly and Manchester Oxford Rd.?
- Python code:
$$$
import numpy as np
from geopy.geocoders import Nominatim
from psycopg2.pool import SimpleConnectionPool

# DB pool
db = SimpleConnectionPool(1, 10, dbname='manchester_p', user='postgres', host='localhost', password='zhaomin199') #this is the only correct config
# Geocoder
geolocator = Nominatim(user_agent='swe', timeout=10)

POIS = [
    ('shop', 'shops'),
    ('ede1', 'eating, drinking and entertainment places'),
    ('school', 'schools'),
    ('railway', 'railway stations'),
    ('tram', 'tram stops'),
    ('stadium', 'stadiums'),
    ('hospital', 'hospitals')
]

def haversine(lo1, la1, lo2, la2):
    lo1, la1, lo2, la2 = map(np.radians, map(float, (lo1, la1, lo2, la2)))
    dlo, dla = lo2-lo1, la2-la1
    a = np.sin(dla/2)**2 + np.cos(la1)*np.cos(la2)*np.sin(dlo/2)**2
    return 6371 * 2 * np.arcsin(np.sqrt(a))

def run_poi_bulk(location_names, radius=0.5): 
    # Input: list of place names (strings).
    # Returns: list of dicts with POI counts around each location.
    results = []
    for name in location_names:
        loc = geolocator.geocode(name)
        if not loc:
            results.append({'place': name, 'error': 'geocode failed'})
            continue
        lat, lon = loc.latitude, loc.longitude
        conn = db.getconn()
        cur = conn.cursor()
        entry = {'place': name}
        for table, label in POIS:
            cur.execute(f"SELECT lat, lon FROM {table}")
            entry[label] = sum(
                haversine(lon, lat, rlon, rlat) <= radius
                for rlat, rlon in cur.fetchall()
            )
        cur.close(); db.putconn(conn)
        results.append(entry)
    return results

# the input locations should in 'Manchester, UK' area
if __name__ == '__main__':
    names = ['Manchester Piccadilly, Manchester, UK', 'Oxford road, Manchester, UK']
    print(run_poi_bulk(names))
$$$
""",

    "road accident": """Provides recent road accident reports.

Example:
```python
def get_accidents(region, since):
    return accident_service.query(region, since)
```""",

    "road event": """Returns road events such as marathons or parades.

Example:
```python
def list_events(date):
    return event_lookup(date)
```"""
}
