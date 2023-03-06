import sqlite3


class flight():
    cur_flight_dict = dict()
    db_con = sqlite3.connect("flight_db.db")

    def __init__(self, states):
        # iterate through each state
        for state in states:
            # assign self to flight tracking map
            flight.cur_flight_dict[state[0]] = self

            self.icao = state[0]
            self.call_sign = state[1]
            self.airline = self.getAirline()
            self.origin_country = state[2]
            self.last_contact_epoch = int(state[4])
            self.contact_counter = 0
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

    # WORKING ON ... can't test as API is currently down
    # returns "not in table" despite valid syntax
    # I think issue is with using .format instead of placeholders (?)
    def getAirline(self):
        # insert airline into id table if it isn't already
        icao_airline_code = self.call_sign[:3]
        db_c = flight.db_con.cursor()
        db_c.execute("""
                     INSERT INTO tbl_airline_id(ICAO_airline_id, full_text_airline)
                     VALUES(?, missing)
                     ON CONFLICT(ICAO_airline_id)
                     DO UPDATE SET full_text_airline=missing;
                     """, (icao_airline_code,))
        flight.db_con.commit()

        # return assoc. full airline string
        db_c.execute("""
                     SELECT full_text_airline FROM tbl_airline_id
                     WHERE ICAO_airline_id=?
                     """, (icao_airline_code,))

        # set airline attibute to assoc full airline string
        self.airline = db_c.fetchone()[0]

    @classmethod
    def updateCurrentFlights(cls, states_list):
        api_set = set()
        # add or update current flights
        for state in states_list:
            api_set.add(state[0])
            if state[0] in cls.cur_flight_dict:
                # call _updateFlights member method
                flight.updateFlight(cls.cur_flight_dict[state[0]], state)
            else:
                # create new flight
                flight(state)

        # remove any flights that are gone since last api call
        for a in cls.cur_flight_dict.keys():
            if a not in api_set:
                # get flight instance
                flight_instance = cls.cur_flight_dict[a]

                # compute average velocity
                from math import sum
                avg_vel = (sum(flight_instance.velocity)
                           /
                           len(flight_instance.velocity))

                # convert heading array into byte array for BLOB insertion
                heading_as_byte = bytearray(len(flight_instance.heading))

                for idx, head_val in flight_instance.heading:
                    heading_as_byte[idx] = head_val

                db_c = flight.db_con.cursor()
                # create table if it doesn't exist
                db_c.execute("""
                            CREATE TABLE IF NOT EXISTS {}(
                                call_sign TEXT NOT NULL,
                                airline TEXT NOT NULL,
                                origin_country TEXT NOT NULL,
                                contact_counter INTEGER.
                                ground_distance INTEGER,
                                max_altitude INTEGER,
                                avg_velocity INTEGER,
                                heading_array BLOB
                                );
                             """)
                flight.db_con.commit()

                to_insert = """({},{},{},{},{},{},{},{})""".format(
                        flight_instance.call_sign,
                        flight_instance.airline,
                        flight_instance.origin_country,
                        flight_instance.contact_counter,
                        flight_instance.total_distance,
                        flight_instance.altitude[1],
                        avg_vel,
                        heading_as_byte
                        )

                db_c.execute("""INSERT INTO {} VALUES{};"""
                             .format(flight_instance.icao, to_insert))
                flight.db_con.commit()

                # remove from current flights dictionary
                del cls.cur_flight_dict[a]

    @classmethod
    def updateFlight(cls, flight, state):
        # update last contact time
        flight.last_contact_epoch = state[4]
        # update contact counter
        flight.contact_counter += 1
        # update long and latitude
        flight.longitude = state[5]
        flight.latitude = state[6]

        # only update these if plane is airborne
        if state[8] == "false":
            flight.total_distance += haversine(
                (flight.longitude, int(state[5]),
                 flight.latitude, int(state[6])))

            # update altitude
            flight.altitude[0] = state[7]
            if flight.altitude[0] > flight.altitude[1]:
                flight.altitude[1] = flight.altitude[0]

            # append current velocity and heading to respective lists
            flight.velocity.append(state[9])
            flight.heading.append(state[10])


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

    # need to convert coord from degrees => radians!!!!!!!!!
    ground_dist = earth_radius_sq_km * asin(sqrt(lat_sin
                                                 + cos(degToRad(lat_prev))
                                                 * cos(degToRad(lat_cur))
                                                 * long_sin))
    return ground_dist
