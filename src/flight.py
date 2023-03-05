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
    def updateFlights(cls, states_list):
        api_set = set()
        # add or update current flights
        for state in states:
            api_set.add(state[0])
            if state[0] in cls.cur_flight_dict:
                # call _updateFlights member method
            else:
                # create new flight
                flight(state)

        # remove any flights that are gone since last api call
        for a in cls.cur_flight_dict.keys():
            if a not in api_set:
                # add information to history tbl in db

                # remove
                # del cls.cur_flight_dict[a]
