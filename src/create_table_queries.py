# historical flight table
hist_flight = (
    """CREATE TABLE tbl_historical_aircraft_data(
    ICAO_id INTEGER NOT NULL PRIMARY KEY,
    airframe TEXT,
    airline TEXT,
    trip_counter INTEGER,
    ping_counter INTEGER,
    total_distance_across_flights INTEGER
    );""")

airline_id = (
    """CREATE TABLE tbl_airline_id(
    ICAO_airline_id TEXT UNIQUE NOT NULL,
    full_text_airline TEXT NOT NULL
    );""")

airframe_id = (
        """
        CREATE TABLE tbl_airframe_id(
            ICAO_id INTEGER NOT NULL PRIMARY KEY,
            airframe TEXT,
            airline TEXT
            );""")

api_call_tracker = (
        """CREATE TABLE tbl_api_call_tracker(
            daily_count INTEGER NOT NULL,
            time_start INTEGER NOT NULL,
            time_to_reset INTEGER NOT NULL,
            last_call INTEGER,
            avg_calls INTEGER
            );""")

# sql queries are accessed via dictionary
create_table_queries_dict = {"tbl_historical_aircraft_data": hist_flight,
                             "tbl_airline_id": airline_id,
                             "tbl_api_call_tracker": api_call_tracker}
