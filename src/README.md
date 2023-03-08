# BC Flight Tracker [work in-progress]

This project pulls real-time flight data from ADS-B sensors via the Open Sky API (The OpenSky Network, https://opensky-network.org). This application collects flight data from aircrafts that enter BC skies, aggregating flight information such as total ground distance covered, horizontal velocity, headings, and more, which are synthesized into historical databases for each "seen" aircraft.

This project is currently written entirely in Python (3.8) with a SQLite3 (3.31) embedded database, and is a work in-progress. Many features are being added weekly with the hopes of one day offering things such as flight reports.

OpenSky Citatation:

Matthias Schäfer, Martin Strohmeier, Vincent Lenders, Ivan Martinovic and Matthias Wilhelm. "Bringing Up OpenSky: A Large-scale ADS-B Sensor Network for Research". In Proceedings of the 13th IEEE/ACM International Symposium on Information Processing in Sensor Networks (IPSN), pages 83-94, April 2014.
