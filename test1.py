# #!/usr/bin/env python3
# import psycopg2
# from datetime import datetime

# def query_weather_data():
#     """
#     Connect to the manchester_p database and query 2 records from the weather_data table.
#     """
#     # Connection parameters
#     conn_params = {
#         "dbname": "manchester_p",
#         "user": "postgres",
#         "host": "localhost",
#         "password": "zhaomin199"  # If password is not needed for local connections
#     }
    
#     try:
#         # Establish connection
#         print("Connecting to PostgreSQL database...")
#         conn = psycopg2.connect(**conn_params)
        
#         # Create a cursor
#         cur = conn.cursor()
        
#         # Execute the query to get two records
#         print("Executing query...")
#         cur.execute("SELECT * FROM weather_data ORDER BY date LIMIT 2")
        
#         # Fetch the results
#         rows = cur.fetchall()
        
#         # Print the results
#         print("\nWeather Data Results:")
#         print("====================")
#         print(rows)
#         # for row in rows:
#         #     date = row[0]
#         #     max_temp = row[1]
#         #     min_temp = row[2]
#         #     precipitation = row[3]
#         #     windspeed = row[4]
            
#         #     print(f"Date: {date}")
#         #     print(f"Max Temperature: {max_temp}°C")
#         #     print(f"Min Temperature: {min_temp}°C")
#         #     print(f"Precipitation: {precipitation} mm")
#         #     print(f"Wind Speed: {windspeed} km/h")
#         #     print("--------------------")
        
#         # Close the cursor and connection
#         cur.close()
#         conn.close()
#         print("Database connection closed.")
        
#     except Exception as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     query_weather_data()


# # You are an expert PostgreSQL assistant. Your task is to translate the 'natural language query' into executable 'Python code' (inculding SQL).
# - Analyze the user's question carefully.
# - Generate comlete Python code to fulfill the request. You can obtain and quote some necessary information from the following example.
# - **Important:** Enclose the 'Python code' within *** python ... *** markdown block.
# - Do not include explanations outside the code block unless specifically asked.
# - If you are given an error message from a previous attempt, analyze the error and the 'Python code' that caused it, then provide a corrected 'Python code' in the *** python ... *** block.

# # Example:
# - natural language queries: what's the weather in Manchester on 1 Jan 2023 and 2 Jan 2023?
# - Python code:
# ***
# import psycopg2
# from datetime import datetime

# def query_weather_data():
#     conn_params = {
#         "dbname": "manchester_p",
#         "user": "postgres",
#         "host": "localhost",
#         "password": "zhaomin199" #this is the only correct password
#     }
#     try:
#         conn = psycopg2.connect(**conn_params)
#         cur = conn.cursor()
#         cur.execute("SELECT * FROM weather_data WHERE date >= '2023-01-01' AND date < '2023-01-03';)
#         rows = cur.fetchall()
#         cur.close()
#         conn.close()
#         return rows
        
#     except Exception as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     print(query_weather_data())
# ***
# # Okey, let's design and generate Python code for the new query:
# - natural language queries: what's the weather in Manchester on 1 Jan 2023 and 2 Jan 2023?

# [(datetime.date(2023, 1, 1), Decimal('25.0'), Decimal('9.9'), Decimal('9.8'), Decimal('4.9'), Decimal('0.5'), None, 'rain'), (datetime.date(2023, 1, 2), Decimal('30.9'), Decimal('7.0'), Decimal('7.9'), Decimal('0.4'), Decimal('0.2'), None, 'rain')]




# import psycopg2
# from datetime import datetime

# def query_weather_data():
    # conn_params = {
    #     "dbname": "manchester_p",
    #     "user": "postgres",
    #     "host": "localhost",
    #     "password": "zhaomin199" #this is the only correct password
    # }
#     try:
#         conn = psycopg2.connect(**conn_params)
#         cur = conn.cursor()
#         cur.execute("SELECT * FROM weather_data WHERE date >= '2023-01-01' AND date < '2023-01-03';")
#         rows = cur.fetchall()
#         cur.close()
#         conn.close()
#         return rows
        
#     except Exception as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     print(query_weather_data())


# import numpy as np
# from psycopg2.pool import SimpleConnectionPool
# from psycopg2 import connect

# # DB pool
# db = SimpleConnectionPool(1, 10, dbname='manchester_p', user='postgres', host='localhost', password='zhaomin199')

# def haversine(lo1, la1, lo2, la2):
#     lo1, la1, lo2, la2 = map(np.radians, map(float, (lo1, la1, lo2, la2)))
#     dlo, dla = lo2-lo1, la2-la1
#     a = np.sin(dla/2)**2 + np.cos(la1)*np.cos(la2)*np.sin(dlo/2)**2
#     return 6371 * 2 * np.arcsin(np.sqrt(a))

# POIS = [
#     ('shop', 'shops'),
#     ('ede1', 'eating, drinking and entertainment places'),
#     ('school', 'schools'),
#     ('railway', 'railway stations'),
#     ('tram', 'tram stops'),
#     ('stadium', 'stadiums'),
#     ('hospital', 'hospitals')
# ]


# def run_poi_bulk(positions, radius=0.5):
#     results = []
#     for name, lat, lon in positions:
#         conn = db.getconn()
#         cur = conn.cursor()
#         entry = {'place': name}
#         for table, label in POIS:
#             cur.execute(f"SELECT lat, lon FROM {table}")
#             entry[label] = sum(haversine(lon, lat, rlon, rlat) <= radius for rlat, rlon in cur.fetchall())
#         cur.close(); db.putconn(conn)
#         results.append(entry)
#     return results

# # Example
# if __name__=='__main__':
#     pts = [('Piccadilly Gardens',53.4810,-2.2440),('MediaCityUK',53.4543,-2.2886)]
#     print(run_poi_bulk(pts))

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
    """
    Input: list of place names (strings).
    Returns: list of dicts with POI counts around each location.
    """
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













from camel.toolkits.code_execution import CodeExecutionToolkit
def main():
    toolkit = CodeExecutionToolkit(sandbox="subprocess", require_confirm=False)
    cga_code0= """
print('hello world')
return "hello"
"""
    try:
        result = toolkit.execute_code(cga_code0)
        return result
    except Exception as e:
        error_message = str(e)
        return error_message
if __name__ == '__main__':
    print(main())


