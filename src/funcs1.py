import sqlite3
import requests
import time
from enum import Enum
from collections import deque


def dbConnectAndSetUp(db_con, db_c):
    from create_table_queries import create_table_queries_dict

    # create set from keys of dict which calls correct SQL queries
    known_tbl_set = set(iter(create_table_queries_dict))

    # get all tables from master schema table
    db_c.execute("SELECT name FROM sqlite_master")
    tup = db_c.fetchall()
    cur_schema_l = []
    for cur_tup in tup:
        cur_schema_l.append(cur_tup[0])
    cur_schema_s = set(cur_schema_l)

    # create set of missing known tables based on schema master
    missing_tbl_set = known_tbl_set - cur_schema_s

    if len(missing_tbl_set) != 0:
        # warn user => allow creation?
        print(("[[ MISSING TABLES ]] => {}"
               .format(missing_tbl_set)))
        return False, missing_tbl_set
    else:
        print("All known schemas present in db .... ")
    return True, known_tbl_set


def dbCreateTables(db_c, db_con, tbl_set):
    # iterate through and create tables
    from create_table_queries import create_table_queries_dict
    for tbl in tbl_set:
        db_c.execute(create_table_queries_dict[tbl])
        db_con.commit()

    db_c.execute("SELECT name FROM sqlite_master")
    print("Tables added ... ", end=" ")
    for tbl in db_c.fetchall():
        print(tbl)

    # api_call_tracker will only have one row => create this row
    # determine proper time values
    # current unix time - known time of 3/3/23 floored by seconds/day
    times = getStartAndUpdateTimes()
    db_c.execute((
        "INSERT INTO tbl_api_call_tracker VALUES({}, {}, {}, NULL, NULL);"
        .format(0, times[0], times[1])
        ))
    db_con.commit()


def getStartAndUpdateTimes():
    days_elapsed = ((time.time() - 1677830400) // 86400)
    adj_start_time = 1677830400 + (86400 * days_elapsed)
    time_to_update = adj_start_time + 86400
    return adj_start_time, time_to_update


# could be changed to accept defualt args for lat/long vars
def reqOpenApi(db_c, db_con, coord):
    # check api caller
    db_c.execute("SELECT * FROM tbl_api_call_tracker")
    api_track_tup = db_c.fetchone()

    if time.time() > api_track_tup[2]:
        # if daily time limit exceeded => get updated times limits
        times = getStartAndUpdateTimes()
        # first value will be daily_count
        db_c.execute((
            """UPDATE tbl_api_call_tracker
            SET daily_count={}, time_start={}, time_to_reset={}"""
            .format(0, times[0], times[1])))
        # commit changes to db
        db_con.commit()
    elif api_track_tup[0] >= 4000:
        print("Max number of daily \'GET STATE\' API calls made.")
        # FAILED api call returns empty list
        return []

    from open_api_auth import auth_info
    api_ad = "https://opensky-network.org/api/states/all"
    req = requests.get(api_ad, auth=auth_info, params=coord)

    # update db with time and correct call count
    db_c.execute((
        """UPDATE tbl_api_call_tracker
        SET daily_count=daily_count+1, last_call={}"""
        .format(time.time())))
    db_con.commit()

    print(req.url)
    return req.json()["states"]


# used for hex conversion
class hex(Enum):
    a = 10
    b = 11
    c = 12
    d = 13
    e = 14
    f = 15


def hexToInt(hex_str):
    ires = 0
    exp = 0
    mult = 0
    for riter in reversed(hex_str):
        if riter.isalpha():
            mult = hex[riter].value
        else:
            mult = int(riter)
        ires += mult * 16 ** exp
        exp += 1
    return ires


class fixed_sized_dict():
    def __init__(self, asize):
        self.max_size = asize
        self.fixed_dict = dict()
        self.queue = deque()  # keep track of what's not been used recently

    def insert_value(self, key, value):
        # hash key-value
        self.fixed_dict[key] = value
        # append to rhs of queue
        self.queue.append(key)

        # if max dictionary size reached
        # delete the last element to be used (left size of deque)
        if len(self.fixed_dict) > self.max_size:
            print("Removing dictionary element to maintain size...")
            del self.fixed_dict[self.queue.popleft()]

    def get_value(self, key):
        return self.fixed_dict[key]

    def check_existance(self, key):
        return key in self.fixed_dict


# multithread safe [to optimize]
def getICAOAsInt(states, icao_dict):
    # iterate over each frame in api
    for frame in states:
        if icao_dict.check_existance(frame[0]):
            frame[0] = icao_dict.get_value(frame[0])
        else:
            base10_icao = hexToInt(frame[0])
            icao_dict.insert_value(frame[0], base10_icao)
            frame[0] = base10_icao
