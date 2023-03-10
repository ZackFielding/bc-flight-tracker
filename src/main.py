import sqlite3
import funcs1
import flight
import time


if __name__ == "__main__":

    # set up data base => establish vars [1]
    db_str = "flight_db.db"
    db_con = sqlite3.connect(db_str)
    db_c = db_con.cursor()

    # set up database [2]
    db_connect_tup_ret = funcs1.dbConnectAndSetUp(db_con, db_c)

    if not db_connect_tup_ret[0]:
        user_in = input("Create missing tables [Y/N]:")
        if user_in == "Y" or user_in == "y":
            funcs1.dbCreateTables(db_c, db_con, db_connect_tup_ret[1])

    # now that all tables have been checked to exist in db
    # pull data from live API
    # lat min, long min, lat max, long max
    bc_coord_dict = {"lamin": "48.1", "lomin": "-139.3",
                     "lamax": "60.3", "lomax": "-113.7"}
    states = funcs1.reqOpenApi(db_c, db_con, bc_coord_dict)
    funcs1.getICAOAsInt(states)
    CURRENT_FLIGHT_CLASS = flight.current_flights(db_str)
    CURRENT_FLIGHT_CLASS.updateCurrentFlightInstances(states)

    # testing
    api_call_count = 1
    while api_call_count < 60:
        # testing only => will be automated post-test
        print("Waiting for next API call", end=" ")
        for _ in range(30):
            print(".", end="", flush=True)
            time.sleep(2)

        print("\n", end="")

        # get states => convert to int => update current flight class
        states = funcs1.reqOpenApi(db_c, db_con, bc_coord_dict)
        funcs1.getICAOAsInt(states)
        CURRENT_FLIGHT_CLASS.updateCurrentFlightInstances(states)
