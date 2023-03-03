import sqlite3
import funcs1
import requests


def main():

    # set up data base => establish vars [1]
    db_con = sqlite3.connect("flight_db.db")
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

    # testing
    for frame in states:
        print(frame)


if __name__ == "__main__":
    main()
