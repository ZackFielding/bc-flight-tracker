import sqlite3
import funcs1
import requests
import multiprocessing
import time


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

    # init fixed sized dict of icao codes to reduce
    # need for hex => int conversion after each API call
    # icao_dict = funcs1.fixed_sized_dict(50)

    t0 = time.perf_counter_ns()

    # ============= NOT WORKING ==========================================
    # I can't seem to create shared memory with the custom class (Value())
    # Need to look into using pipes or queues to get this to work,
    # or just don't use multiprocessing in this case
    states_midway = len(states)//2
    # for locking dict
    fsd_lock = multiprocessing.Lock()
    # sharing dict between process
    fsd_shared = multiprocessing.Value(funcs1.fixed_sized_dict, 50)

    process_tup = ()
    process_tup[0] = multiprocessing.Process(target=funcs1.getICAOAsInt,
                                             args=(states, 0, states_midway,
                                                   fsd_shared, fsd_lock))

    process_tup[1] = multiprocessing.Process(target=funcs1.getICAOAsInt,
                                             args=(states, states_midway,
                                                   len(states),
                                                   fsd_shared, fsd_lock))

    map(lambda process: process.start(), process_tup)
    map(lambda process: process.join(),  process_tup)

    ttotal = time.perf_counter_ns() - t0
    print("{}ns elapsed.".format(ttotal))

    # `states` now has base 10 integer for ICAO
    for frame in states:
        print(frame)


if __name__ == "__main__":
    main()
