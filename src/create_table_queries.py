# historical flight table
hist_flight = (
    """CREATE TABLE tbl_historical_aircraft_data(
    ICAO_id INTEGER NOT NULL PRIMARY KEY,
    airframe TEXT,
    airline TEXT,
    trip_counter INTEGER,
    ping_counter INTEGER
    );""")

cur_flights = (
    """CREATE TABLE tbl_current_flights(
    ICAO_id INTEGER NOT NULL PRIMARY KEY,
    airframe TEXT,
    airline TEXT,
    proj_origin TEXT,
    proj_dest TEXT
    );""")

airline_id = (
    """CREATE TABLE tbl_airline_id(
    ICAO_airline_id INTEGER NOT NULL PRIMARY KEY,
    full_text_airline TEXT
    );""")

# sql queries are accessed via dictionary
create_table_queries_dict = {"tbl_historical_aircraft_data": hist_flight,
                             "tbl_current_flights": cur_flights,
                             "tbl_airline_id": airline_id}
