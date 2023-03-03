import sqlite3


def dbConnectAndSetUp(db_con, db_c):
    known_tbl_set = {"tbl_historical_aircraft_data",
                     "tbl_current_flights", "tbl_airline_id"}

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
