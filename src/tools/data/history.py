"""Historic editions and champions.

Sources: https://eukonkanto.fi/en/results/champions-and-records/ (champions, world records)
and https://en.wikipedia.org/wiki/Wife-carrying (Main-series winning times 1996-2026, citing
the official results archive). Spellings follow eukonkanto.fi where the two differ.

Times marked GENERATED are not published anywhere we could find; each is slower than the
series' official world record, so the records page is reproduced exactly.
"""

# 2020 and 2021 were cancelled (COVID); 1992-1995 were Finnish Championships.
YEARS = [y for y in range(1992, 2028) if y not in (2020, 2021)]
FINNISH_YEARS = range(1992, 1996)
SERIES_FROM = {"MAIN": 1992, "TEAM": 1996, "SPR": 2006, "WOMEN": 2025, "M40": 2026}

# Edition dates published on the site: 2026 (news) and 2027 (front page / registration page).
# Every other year: GENERATED as the first Friday-Saturday of July, registration from 1 Nov of
# the previous year to the Wednesday before at 22:00.
KNOWN_DATES = {
    2026: ("2026-07-03", "2026-07-04", "2025-11-01", "2026-07-01 22:00:00"),
    2027: ("2027-07-02", "2027-07-03", "2026-11-01", "2027-06-30 22:00:00"),
}

# Main series champions: year -> (carrier, carried, ISO, time, generated?)
MAIN_CHAMPIONS = {
    1992: ("Jouni Jussila", "Tiina Kaipiainen", "FIN", "1:12.4", True),
    1993: ("Jouni Jussila", "Tiina Kaipiainen", "FIN", "1:10.9", True),
    1994: ("Jouni Jussila", "Tiina Kaipiainen", "FIN", "1:09.7", True),
    1995: ("Ilpo Rönkkö", "Anneli Rönkkö", "FIN", "1:11.3", True),
    1996: ("Jouni Jussila", "Tiina Jussila", "FIN", "1:05.8", False),
    1997: ("Jouni Jussila", "Tiina Jussila", "FIN", "1:05.0", False),
    1998: ("Imre Ambos", "Annela Ojaste", "EST", "1:09.2", False),
    1999: ("Imre Ambos", "Annela Ojaste", "EST", "1:04.5", False),
    # Wikipedia lists 55.5 and 55.6 for 2000-2001, faster than the official record (56.9, 2006);
    # the official record wins, so these two times are GENERATED.
    2000: ("Margo Uusorg", "Birgit Ulricht", "EST", "57.5", True),
    2001: ("Margo Uusorg", "Birgit Ulricht", "EST", "57.8", True),
    2002: ("Meelis Tammre", "Anna Zilbenberg", "EST", "1:03.8", False),
    2003: ("Margo Uusorg", "Egle Soll", "EST", "1:00.7", False),
    2004: ("Madis Uusorg", "Inga Klauson", "EST", "1:05.3", False),
    2005: ("Margo Uusorg", "Egle Soll", "EST", "59.1", False),
    2006: ("Margo Uusorg", "Sandra Kullas", "EST", "56.9", False),
    2007: ("Madis Uusorg", "Inga Klauson", "EST", "1:01.7", False),
    2008: ("Alar Voogla", "Kristi Viltrop", "EST", "1:01.9", False),
    2009: ("Taisto Miettinen", "Kristiina Haapanen", "FIN", "1:02.0", False),
    2010: ("Taisto Miettinen", "Kristiina Haapanen", "FIN", "1:04.9", False),
    2011: ("Taisto Miettinen", "Kristiina Haapanen", "FIN", "1:00.7", False),
    2012: ("Taisto Miettinen", "Kristiina Haapanen", "FIN", "1:12.2", False),
    2013: ("Taisto Miettinen", "Kristiina Haapanen", "FIN", "1:05.0", False),
    2014: ("Ville Parviainen", "Janette Oksman", "FIN", "1:03.7", False),
    2015: ("Ville Parviainen", "Sari Viljanen", "FIN", "1:02.8", False),
    2016: ("Dmitriy Sagal", "Anastasia Loginova", "RUS", "1:04.1", False),
    2017: ("Taisto Miettinen", "Kristiina Haapanen", "FIN", "1:08.6", False),
    2018: ("Vytautas Kirkliauskas", "Neringa Kirkliauskiene", "LTU", "1:05.1", False),
    2019: ("Vytautas Kirkliauskas", "Neringa Kirkliauskiene", "LTU", "1:06.7", False),
    2022: ("Taisto Miettinen", "Katja Kovanen", "FIN", "1:04.3", False),
    2023: ("Taisto Miettinen", "Katja Kovanen", "FIN", "1:06.2", False),
    2024: ("Vytautas Kirkliauskas", "Neringa Kirkliauskiene", "LTU", "1:03.5", False),
    2025: ("Caleb Roesler", "Justine Roesler", "USA", "1:01.1", False),
}

# Sprint champions (final). Times GENERATED except the 2012 world record (31.34).
# 2007 was a shared win; both pairs are stored with the same time (tie -> both rank 1).
SPRINT_CHAMPIONS = {
    2006: [("Renno Remmel", "Kati Elmi", "EST", "35.12", True)],
    2007: [("Ranner Kuningas", "Inga Klauson", "EST", "35.40", True),
           ("Alar Voogla", "Kristi Viltrop", "EST", "35.40", True)],
    2008: [("Joni Juntunen", "Jaana Haavikko", "FIN", "34.66", True)],
    2009: [("Renno Remmel", "Merlin Linnusaar", "EST", "35.05", True)],
    2010: [("Alar Voogla", "Kristi Viltrop", "EST", "34.90", True)],
    2011: [("Alar Voogla", "Kristi Viltrop", "EST", "34.71", True)],
    2012: [("Joni Juntunen", "Jaana Haavikko", "FIN", "31.34", False)],
    2013: [("Alar Voogla", "Kristi Viltrop", "EST", "34.98", True)],
    2014: [("Joni Juntunen", "Jaana Haavikko", "FIN", "34.52", True)],
    2015: [("Joni Juntunen", "Jaana Haavikko", "FIN", "34.47", True)],
    2016: [("Joni Juntunen", "Jaana Haavikko", "FIN", "34.81", True)],
    2017: [("Philipp Spiess", "Kim Stella Müller", "CHE", "35.66", True)],
    2018: [("Thomas Kueng", "Sandra Burch", "DEU", "35.93", True)],
    2019: [("Ilpo Haalisto", "Jenni Piippo", "FIN", "34.88", True)],
    2022: [("Joni Juntunen", "Jaana Haavikko", "FIN", "35.21", True)],
    2023: [("Ilpo Haalisto", "Jenni Piippo", "FIN", "34.75", True)],
    2024: [("Elliott Earnshaw", "Adelaide Taylor", "AUS", "34.39", True)],
    2025: [("Severi Allonen", "Karla Könönen", "FIN", "34.62", True)],
}

# Team champions: year -> (team, organisation?, [carrier1, carrier2, carrier3], carried, ISOs, time, generated?)
# The site lists four names per team without roles; the carried person is the member who is the
# carried person in other races (e.g. Jaana Haavikko, Siiri Koskinen) or, for police and company
# teams, the one woman listed. 2001 (Väike-Maarja Vald) has no archived members and is omitted;
# 2002 was shared with Äntu Farm, whose 2002 squad is not archived.
POLICE = "Ylä-Savon kihlakunnan poliisit"
PUTKI = "Iisalmen Putkiasennus Oy"
TEAM_CHAMPIONS = {
    1996: (POLICE, POLICE, ["Marko Tervo", "Reijo Kärkkäinen", "Pekka Korhonen"], "Marja Pääkkö", "FIN", "1:38.2", True),
    1997: (POLICE, POLICE, ["Tuomo Eskelinen", "Pekka Korhonen", "Marko Tervo"], "Marja Pääkkö", "FIN", "1:36.9", True),
    1998: (POLICE, POLICE, ["Jari Rytkönen", "Jorma Rannio", "Pekka Korhonen"], "Sirpa-Riitta Patronen", "FIN", "1:37.5", True),
    1999: (PUTKI, PUTKI, ["Joni Juntunen", "Jorma Ryhänen", "Arto Lappalainen"], "Katri Rask", "FIN", "1:35.8", True),
    2000: (POLICE, POLICE, ["Marko Tervo", "Tuomo Eskelinen", "Jari Rytkönen"], "Sirpa-Riitta Patronen", "FIN", "1:34.6", True),
    2002: (PUTKI, PUTKI, ["Joni Juntunen", "Jorma Ryhänen", "Petri Vinkki"], "Johanna Jauhiainen", "FIN", "1:33.0", True),
    2003: ("Äntu Farm", "Äntu Farm", ["Ants Einsalu", "Jaanus Pajula", "Janek Löömets"], "Ivi Löömets", "EST", "1:31.4", True),
    2004: ("Äntu Farm", "Äntu Farm", ["Ants Einsalu", "Margo Hussar", "Janek Löömets"], "Ivi Löömets", "EST", "1:30.2", True),
    2005: ("Sõbrad", None, ["Mauri Zahkna", "Marek Zahkna", "Renno Remmel"], "Merlin Linnusaar", "EST", "1:28.7", True),
    2006: ("Sõbrad", None, ["Mauri Zahkna", "Marek Zahkna", "Renno Remmel"], "Kati Elmi", "EST", "1:27.9", True),
    2007: ("Sõbrad", None, ["Mauri Zahkna", "Marek Zahkna", "Renno Remmel"], "Merlin Linnusaar", "EST", "1:27.6", True),
    2008: ("Sõbrad", None, ["Mauri Zahkna", "Marek Zahkna", "Renno Remmel"], "Merlin Linnusaar", "EST", "1:24.6", False),
    2009: ("Sõbrad", None, ["Mauri Zahkna", "Marek Zahkna", "Renno Remmel"], "Merlin Linnusaar", "EST", "1:28.1", True),
    2010: ("Konkurendid", None, ["Alar Voogla", "Renno Remmel", "Marek Zahkna"], "Kristi Viltrop", "EST", "1:29.4", True),
    2011: ("Sonkarun", None, ["Toni Hynynen", "Mika Suomalainen", "Joni Juntunen"], "Jaana Haavikko", "FIN", "1:30.8", True),
    2012: ("Sonkarun", None, ["Toni Hynynen", "Mika Suomalainen", "Joni Juntunen"], "Jaana Haavikko", "FIN", "1:29.9", True),
    2013: ("Sonkarun", None, ["Toni Hynynen", "Mika Suomalainen", "Joni Juntunen"], "Jaana Haavikko", "FIN", "1:31.2", True),
    2014: ("Sonkarun", None, ["Toni Hynynen", "Mika Suomalainen", "Joni Juntunen"], "Jaana Haavikko", "FIN", "1:30.5", True),
    2015: ("Sonkarun", None, ["Toni Hynynen", "Mika Suomalainen", "Joni Juntunen"], "Jaana Haavikko", "FIN", "1:31.7", True),
    2016: ("Serti", None, ["Toni Hynynen", "Timo Pudas", "Joni Juntunen"], "Jaana Haavikko", "FIN", "1:32.0", True),
    2017: ("Serti", None, ["Toni Hynynen", "Timo Pudas", "Joni Juntunen"], "Jaana Haavikko", "FIN", "1:31.3", True),
    2018: ("Serti", None, ["Sami Tervo", "Timo Pudas", "Joni Juntunen"], "Jaana Haavikko", "FIN", "1:33.4", True),
    2019: ("Serti", None, ["Toni Hynynen", "Timo Pudas", "Joni Juntunen"], "Jaana Haavikko", "FIN", "1:32.6", True),
    2022: ("Serti", None, ["Toni Hynynen", "Timo Pudas", "Joni Juntunen"], "Jaana Haavikko", "FIN", "1:34.1", True),
    2023: ("Maailmanmestaruuden metsästäjät", None, ["Joni Juntunen", "Antti Siltala", "John Lund"], "Jaana Haavikko", "FIN/USA", "1:35.0", True),
    2024: ("Team Australia", None, ["Elliott Earnshaw", "Angus Mcdonald", "Patrick Mahony"], "Adelaide Taylor", "AUS", "1:33.8", True),
    2025: ("Team Big Beef", None, ["Joni Juntunen", "John Lund", "Elliot Storey"], "Siiri Koskinen", "FIN/USA", "1:36.4", True),
}

# Women's main series 2025: the world record (records page).
WOMEN_CHAMPIONS = {2025: ("Janita Riekkinen", "Sanna Jäntti", "FIN", "1:39.51", False)}
