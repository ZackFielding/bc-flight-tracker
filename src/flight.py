import sqlite3


class flight():
    def __init__(self, state, db_con):
        self.icao = state[0]
        self.call_sign = state[1]
        # async?
        self.setAirline(db_con)
        self.setAirframe(db_con)
        # ####
        self.origin_country = state[2]
        self.last_contact_epoch = int(state[4])
        self.contact_counter = 1
        self.longitude = int(state[5])
        self.latitude = int(state[6])
        # computed using haversine function
        # once a second distance comes in
        self.total_distance = 0

        # remainder of attributes depend on if plane is on ground
        if state[8] == "false":
            # [current, max]
            self.altitude = [int(state[7]), int(state[7])]
            # list (compute summary stats once landed?)
            self.velocity = [int(state[9])]
            # list
            self.heading = [int(state[10])]
        else:
            self.altitude = [0, 0]
            self.velocity = [0]
            self.heading = []

    def setAirframe(self, db_con):
        db_c = db_con.cursor()
        # create new row if aircraft has not been seen
        # aircraft itself, NOT ITS TYPE
        db_c.execute("""
                    INSERT INTO tbl_airframe_id
                    VALUES(?,?,?)
                    ON CONFLICT(ICAO_id)
                    DO NOTHING;

                    SELECT airframe FROM tbl_airframe_id
                    WHERE ICAO_id=?;
                    """, (self.icao, "missing", self.airline, self.icao))
        db_con.commit()
        self.airframe = (db_con.fetchone())[0]

    def checkForAirframe(self, db_con):
        db_c = db_con.cursor()
        db_c.execute("SELECT airframe FROM tbl_airframe_id WHERE ICAO=?",
                     (self.icao,))
        # assume that it has been updated
        # take the chance that it's still `missing`
        self.airframe = (db_c.fetchone())[0]

    def setAirline(self, db_con):
        # insert airline into id table if it isn't already
        icao_airline_code = self.call_sign[:3]
        db_c = db_con.cursor()
        db_c.execute("""
                     INSERT INTO tbl_airline_id(ICAO_airline_id, full_text_airline)
                     VALUES(?, "missing")
                     ON CONFLICT(ICAO_airline_id)
                     DO NOTHING;

                     SELECT full_text_airline FROM tbl_airline_id
                     WHERE ICAO_airline_id=?
                     """, (icao_airline_code, icao_airline_code))
        db_con.commit()

        # set airline attibute to assoc full airline string
        self.airline = (db_c.fetchone())[0]

    def updateFlight(self, state, db_con):
        self.checkForAirframe(db_con)
        # update last contact time
        self.last_contact_epoch = state[4]
        # update contact counter
        self.contact_counter += 1
        # update long and latitude
        self.longitude = state[5]
        self.latitude = state[6]

        # only update these if plane is airborne
        if state[8] == "false":
            self.total_distance += haversine(
                (self.longitude, int(state[5]),
                 self.latitude, int(state[6])))

            # update altitude
            self.altitude[0] = state[7]
            if self.altitude[0] > self.altitude[1]:
                self.altitude[1] = self.altitude[0]

            # append current velocity and heading to respective lists
            self.velocity.append(state[9])
            self.heading.append(state[10])


# haversine assums a perfect sphere => the earth is not
# but this should be accurate up to 0.5% error (good enough for this impl.)
def haversine(long_prev, long_cur, lat_prev, lat_cur):
    from math import sin, cos, sqrt, asin, pi

    def degToRad(val):
        return val * pi / 180

    # current = 2, previous = 1
    # cur - prev
    def sin_sq(cur, prev):
        return sin((degToRad(cur-prev))/2) ** 2

    lat_sin = sin_sq(lat_cur, lat_prev)
    long_sin = sin_sq(long_cur, long_prev)
    earth_radius_sq_km = 12713.5046284

    ground_dist = earth_radius_sq_km * asin(sqrt(lat_sin
                                                 + cos(degToRad(lat_prev))
                                                 * cos(degToRad(lat_cur))
                                                 * long_sin))
    return ground_dist


# creates/controls flight instances
class current_flights():
    cur_flight_dict = dict()
    db_con = None

    def __init__(self, database_string):
        current_flights.db_con = sqlite3.connect(database_string)

    def updateCurrentFlightInstances(self, states_list):
        api_set = set()
        # add or update current flights
        for state in states_list:
            # mark as seen (i.e., is a current flight)
            api_set.add(state[0])
            # if already a current flight
            # get flight instance && call its update member func
            if state[0] in current_flights.cur_flight_dict:
                flight_instance = current_flights.cur_flight_dict[state[0]]

                # NOT TESTED wt/ checkForAirframe()
                # currently passing db connection => might be better to
                # create class wide attributes to create cursors from
                flight_instance.updateFlight(state, current_flights.db_con)
            else:
                # create new flight
                current_flights.cur_flight_dict[state[0]] = flight(
                        state,
                        current_flights.db_con
                        )

        # remove any flights that are gone since last api call
        # create list of cur flights => view will cause run time error
        # due to deletions (cur_flights_dict should not be very big)
        # TO DO:
        # filter flights => only add flights that have had at least
        # 2 air measurements
        count_flights_removed = 0
        for a in list(current_flights.cur_flight_dict):
            if a not in api_set:
                # get flight instance
                flight_instance = current_flights.cur_flight_dict[a]

                # compute average velocity
                from math import fsum
                avg_vel = (fsum(flight_instance.velocity)
                           /
                           len(flight_instance.velocity))

                # convert heading array into byte array for BLOB insertion
                heading_as_byte = bytearray(len(flight_instance.heading))

                for idx, head_val in flight_instance.heading:
                    heading_as_byte[idx] = head_val

                db_c = current_flights.db_con.cursor()

                # [first time program has seen this airframe]
                # create table for if it doesn't exist
                # table names that are integers need explicit quotes
                icao_string_formatted = "'{}'".format(flight_instance.icao)
                db_c.execute("""
                            CREATE TABLE IF NOT EXISTS {}(
                                call_sign TEXT NOT NULL,
                                airframe TEXT NOT NULL,
                                airline TEXT NOT NULL,
                                origin_country TEXT NOT NULL,
                                contact_counter INTEGER,
                                ground_distance INTEGER,
                                max_altitude INTEGER,
                                avg_velocity INTEGER,
                                heading_array BLOB
                                );
                             """.format(icao_string_formatted))

                current_flights.db_con.commit()

                db_c.execute("""INSERT INTO {} VALUES(?,?,?,?,?,?,?,?,?);"""
                             .format(icao_string_formatted),
                             (flight_instance.call_sign,
                              flight_instance.airframe,
                              flight_instance.airline,
                              flight_instance.origin_country,
                              flight_instance.contact_counter,
                              flight_instance.total_distance,
                              flight_instance.altitude[1],
                              avg_vel,
                              heading_as_byte)
                             )

                current_flights.db_con.commit()

                # UPSERT into historical database
                db_c.execute("""
                             INSERT INTO tbl_historical_aircraft_data
                             VALUES(?,?,?,?,?,?)
                             ON CONFLICT(ICAO_id)
                             DO UPDATE SET trip_counter=trip_counter+1,
                             ping_counter=ping_counter+?,
                             total_distance_across_flights=total_distance_across_flights+?;
                             """,
                             (flight_instance.icao,
                              flight_instance.airframe,
                              flight_instance.airline,
                              1,
                              flight_instance.contact_counter,
                              flight_instance.total_distance,
                              flight_instance.contact_counter,
                              flight_instance.total_distance))

                # remove from current flights dictionary
                del current_flights.cur_flight_dict[a]

                count_flights_removed += 1

        print("[%d] flights added to historical database."
              % count_flights_removed)
