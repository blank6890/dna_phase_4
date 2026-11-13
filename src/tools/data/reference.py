"""Reference data. Sources: eukonkanto.fi/en/ (rules, programme, market place,
registration, front-page partners, news). Rows not published on the site are
marked GENERATED and are written to populate.sql with a `-- GENERATED:` comment."""

COUNTRIES = [  # (ISO 3166 alpha-3, name, continent)
    ("AUS", "Australia", "Oceania"), ("AUT", "Austria", "Europe"), ("BEL", "Belgium", "Europe"),
    ("BRA", "Brazil", "South America"), ("CAN", "Canada", "North America"), ("CHE", "Switzerland", "Europe"),
    ("CHN", "China", "Asia"), ("CZE", "Czech Republic", "Europe"), ("DEU", "Germany", "Europe"),
    ("DNK", "Denmark", "Europe"), ("EST", "Estonia", "Europe"), ("FIN", "Finland", "Europe"),
    ("FRA", "France", "Europe"), ("GBR", "United Kingdom", "Europe"), ("IRL", "Ireland", "Europe"),
    ("ITA", "Italy", "Europe"), ("JPN", "Japan", "Asia"), ("LTU", "Lithuania", "Europe"),
    ("NOR", "Norway", "Europe"), ("PHL", "Philippines", "Asia"), ("RUS", "Russia", "Europe"),
    ("SGP", "Singapore", "Asia"), ("SRB", "Serbia", "Europe"), ("SVK", "Slovakia", "Europe"),
    ("SWE", "Sweden", "Europe"), ("UKR", "Ukraine", "Europe"), ("USA", "United States", "North America"),
]

ROLES = [("CARRIER_1", "Carrier (leg 1)", 1), ("CARRIER_2", "Carrier (leg 2)", 2),
         ("CARRIER_3", "Carrier (leg 3)", 3), ("CARRIED", "Carried person ('wife')", None)]

# (code, name, track m, water, dry, min carrier age, min carried age, min kg, carriers, has heats)
SERIES = [
    ("MAIN", "World Championship, main series", 253.5, 1, 2, 18, 17, 49, 1, False),
    ("WOMEN", "Women's main series", 253.5, 1, 2, 18, 17, 49, 1, False),
    ("M40", "Senior series +40", 253.5, 1, 2, 40, 17, 49, 1, False),
    ("TEAM", "Team competition", 253.5, 1, 2, 18, 17, 49, 3, False),
    ("SPR", "Sprint", 120.0, 1, 0, 18, 17, 49, 1, True),
]

# Race number and time of day per series (programme 2027: sprint Fri 19:00, team Sat 13:00,
# World Championship Sat 15:00; women 14:00 and +40 14:20 are GENERATED from the 2026 run order).
RACE_SLOTS = {"SPR": (1, "start", "19:00"), "TEAM": (2, "end", "13:00"), "WOMEN": (3, "end", "14:00"),
              "M40": (4, "end", "14:20"), "MAIN": (5, "end", "15:00")}
# Minutes from scheduled start to the last finisher (GENERATED; the site publishes no clock times).
LAST_FINISH_MIN = {"SPR": 60, "TEAM": 45, "WOMEN": 15, "M40": 30, "MAIN": 90}
FEES_NOW = {"MAIN": 55, "WOMEN": 55, "M40": 55, "SPR": 55, "TEAM": 160}      # registration page 2027
FEES_OLD = {"MAIN": 50, "WOMEN": 50, "M40": 50, "SPR": 25, "TEAM": 150}      # Phase 1 domain study (older page)

VENUES = [  # (id, name, street, postal, city, facilities)
    (1, "Wife Carrying Arena", "Urheilutie 1", "74300", "Sonkajärvi", ["Spectator stands", "Timing booth"]),
    (2, "Sonkajärvi Sports Hall", "Urheilutie 1", "74300", "Sonkajärvi",
     ["Changing rooms", "Showers", "Lockable lockers", "Info desk"]),
    (3, "Sonkajärvi Sports Field", "Kuntotie 4", "74300", "Sonkajärvi", ["Market area"]),
]

SPONSORS = [  # "In cooperation with" partner links in the site footer
    (1, "Olvi", "http://www.olvi.fi/"), (2, "DNA", "https://www.dna.fi/"),
    (3, "Ylä-Savon Jätehuolto", "https://www.ylasavonjatehuolto.fi/"), (4, "IPA", "https://ipa.fi"),
    (5, "Rebekan hoitokoti", "https://rebekanhoitokoti.fi/"), (6, "Sonkajärven kunta", None),
]
SPONSOR_YEARS = [2025, 2026, 2027]

GRAND_PRIX = [  # (id, name, first-of-month, city, region, organiser, host ISO, generated?)
    (1, "China Wife Carrying Championship", "2024-05-01", "Shanghai", "Shanghai", "Event organiser not published", "CHN", True),
    (2, "Australian Wife Carrying Championship", "2024-09-01", "Sydney", "New South Wales", "Event organiser not published", "AUS", True),
    (3, "Dentergem Wife Carrying Championship", "2024-04-01", "Dentergem", "West Flanders", "Event organiser not published", "BEL", True),
    (4, "North American Wife Carrying Championship", "2024-10-01", "Newry", "Maine", "Sunday River Resort", "USA", True),
    (5, "UK Wife Carrying Championship", "2026-07-01", "Kirkcudbright", "Dumfries & Galloway", "Kirkcudbright Summer Festivities", "GBR", False),
]

# Prizes (rules page). (id, name, type, rank, drink, description, scope, offered by series)
ALL = ["MAIN", "WOMEN", "M40", "TEAM", "SPR"]
PRIZES = [
    (1, "World Champion prize and wife-carrying drink", "Placement", 1, True,
     "Annually changing prize plus wife-carrying drink equal to the carried person's weight", "Series", ["MAIN"]),
    (2, "Series winner product prize", "Placement", 1, False, "Product prize for the series winner", "Series",
     ["WOMEN", "M40", "TEAM", "SPR"]),
    (3, "Second place product prize", "Placement", 2, False, "Product prize; no cash value, not mailed", "Series", ALL),
    (4, "Third place product prize", "Placement", 3, False, "Product prize; no cash value, not mailed", "Series", ALL),
    (5, "Most entertaining couple", "Special", None, False, "Most entertaining couple or team of the weekend", "Weekend",
     ["MAIN", "WOMEN", "M40", "TEAM"]),
    (6, "Best costume", "Special", None, False, "Best costume of the weekend", "Weekend", ["MAIN", "WOMEN", "M40", "TEAM"]),
    (7, "Strongest carrier", "Special", None, False, "Strongest carrier of the weekend", "Weekend",
     ["MAIN", "WOMEN", "M40", "TEAM"]),
]

# GENERATED: officials are not published on the site. (first, last, dob, gender, title, since, supervisor?, duty)
OFFICIALS = [
    ("Matti", "Hyvönen", "1961-03-14", "Male", "Chief Judge", 1998, False, "Jury"),
    ("Riitta", "Kärkkäinen", "1970-08-02", "Female", "Jury Member", 2006, True, "Jury"),
    ("Juha", "Partanen", "1975-01-19", "Male", "Jury Member", 2010, True, "Jury"),
    ("Anne", "Ryynänen", "1982-05-27", "Female", "Timekeeper", 2012, True, "Timekeeper"),
    ("Pekka", "Tikkanen", "1968-11-30", "Male", "Timekeeper", 2004, True, "Timekeeper"),
    ("Jari", "Huttunen", "1979-04-08", "Male", "Starter", 2015, True, "Starter"),
    ("Sari", "Lappalainen", "1988-09-12", "Female", "Info Desk Officer", 2018, True, "Info desk"),
    ("Minna", "Rissanen", "1991-02-21", "Female", "Info Desk Officer", 2021, True, "Info desk"),
]

# GENERATED: vendor names and contacts (the site lists only booth prices and two booking contacts).
# (id, business, contact, phone, email, categories)
VENDORS = [
    (1, "Sonkajärven Leipomo", "Helena Kokkonen", "+358 40 100 2001", "myynti@leipomo.example", ["Food", "Local specialities"]),
    (2, "Savon Käsityöpaja", "Eija Mustonen", "+358 40 100 2002", "paja@kasityo.example", ["Handicrafts"]),
    (3, "Ylä-Savon Hunaja", "Tapio Pitkänen", "+358 40 100 2003", "hunaja@ylasavo.example", ["Food", "Local specialities"]),
    (4, "Kalakukko-Kioski", "Raimo Heikkinen", "+358 40 100 2004", "kioski@kalakukko.example", ["Food"]),
    (5, "Puukko & Nahka", "Ossi Kinnunen", "+358 40 100 2005", "info@puukko.example", ["Handicrafts"]),
    (6, "Marjatilan Mehut", "Leena Väänänen", "+358 40 100 2006", "mehut@marjatila.example", ["Food", "Local specialities"]),
    (7, "Villasukka Oy", "Kaarina Toivanen", "+358 40 100 2007", "villa@sukka.example", ["Handicrafts"]),
    (8, "Retkeilijän Grilli", "Markku Ruotsalainen", "+358 40 100 2008", "grilli@retki.example", ["Food"]),
    (9, "Sonka Souvenirs", "Jenni Hirvonen", "+358 40 100 2009", "shop@sonka.example", ["Handicrafts", "Local specialities"]),
]
# (vendor, year, size, fee, electricity, paid). Standard 4x4 = 70 EUR, 4x8 = 140 EUR; food and custom by contract.
BOOKINGS = [
    (1, 2026, "4x8", 160, True, True), (2, 2026, "4x4", 70, False, True), (3, 2026, "4x4", 70, False, True),
    (4, 2026, "Custom", 220, True, True), (5, 2026, "4x8", 140, False, True), (6, 2026, "4x4", 85, True, True),
    (7, 2026, "4x4", 70, False, True),
    (1, 2027, "4x8", 160, True, True), (2, 2027, "4x8", 140, False, False), (4, 2027, "Custom", 220, True, False),
    (8, 2027, "4x4", 90, True, False),
]
