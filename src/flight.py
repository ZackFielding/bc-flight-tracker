import sqlite3


class flight():
    cur_flight_dict = dict()
    db_con = sqlite3.connect("flight_db.db")

    def __init__(self, state):
        # assign self to flight tracking map
        flight.cur_flight_dict[int_icao] = self

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
            self.altitude = int(state[7])
            self.velocity = int(state[9])
            self.heading = [int(state[10])]
        else:
            self.altitude = 0
            self.velocity = 0
            self.heading = []

    def getAirline(self):
        # 1. Check to see if ICAO code exists in table
        db_c = flight.db_con.cursor()
        db_c.execute("""SELECT * FROM tbl_airline_id
                     WHERE ICAO_airline_id={}""".format(self.call_sign[:3]))
        tup = db_c.fetchone()

        # if it does not exist => create entry && add query
        # if code in db but translation has not been added,
        # set airlie to `missing`
        if len(tup) == 0:
            db_c.execute("""INSERT INTO tbl_airline_id
                         VALUES({}, missing);"""
                         .format(self.call_sign[:3]))
        else:
            self.airline = tup[1]

    @classmethod
    def updateCurrentFlights(cls, states_list):
        api_set = set()
        # add or update current flights
        for state in states:
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
                # add information to history tbl in db

                # remove
                # del cls.cur_flight_dict[a]

    @classmethod
    def updateFlight(cls, flight, state):
        # update last contact time
        flight.last_contact_epoch = state[4]
        # update contact counter
        flight.contact_counter += 1
        # update long and latitude
        flight.longitude = state[5]
        flight.latitude = state[6]

        # compute and update distance
        flight.total_distance += haversine(
                (flight.longitude, int(state[5]),
                 flight.latitude, int(state[6])))


# haversine assums a perfect sphere => the earth is not
# but this should be accurate up to 0.5% error (good enough for this impl.)
def haversine(long_prev, long_cur, lat_prev, lat_cur):
    from math import sin, cos, sqrt, asin

    # current = 2, previous = 1
    # cur - prev
    def sin_sq(cur, prev):
        return sin((cur-prev)/2) ** 2

    earth_radius = 6356.7523142

    # need to convert coord from degrees => radians!!!!!!!!!
    a = 2 * earth_radius * asin(sqrt(sin_sq(lat_cur, lat_rev)
                                     + cos(lat_prev) * cos(lat_cur)
                                     * sin_sq(long_cur, long_prev)))
