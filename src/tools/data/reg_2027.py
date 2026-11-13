"""2027 registrations (https://eukonkanto.fi/en/participating-competitors-and-countries/,
fetched 2026-11-13) plus GENERATED operational rows for 2026: protests, special awards and
one cancelled registration, and one entry with no registration (D2 demo).

Skipped from the 2027 list: "Name not published" rows and Team USA ("To be determined"
carriers) - a registration needs every role filled (Phase 1 rule).
"""

# series -> rows "carrier|carried|ISO"; registration timestamps and bibs are GENERATED.
REGISTRATIONS_2027 = {
    "MAIN": """
Leo Birgersson|Meja Wallering|SWE
Shane Williams|Lauren Williams|USA
Pierre Wiggström|Linda Thyselius|SWE
Sam Farber|Sarah Farber|USA
""",
    "SPR": """
Shane Williams|Lauren Williams|USA
Andrew Lee|Devon Lee|USA
""",
    "M40": """
Ian Jones|Catherine Jones|GBR
Pierre Wiggström|Linda Thyselius|SWE
Andrew Lee|Devon Lee|USA
""",
}
BIB_START_2027 = {"M40": 7, "MAIN": 20, "SPR": 70}

# Citizenship where an entry lists several countries and the order does not settle it.
CITIZENSHIP_OVERRIDES = {"John Lund": ["USA"], "Vytautas Kirkliauskas": ["LTU"], "Katy Hagstedt": ["USA"],
                         "Ivan Voronkov": ["RUS", "FIN"]}

# GENERATED: fixed carried-person weights below 49 kg so the backpack report (AR2) has rows.
LIGHT_CARRIED = {"Lotta Lindroos": 46.0, "Devon Lee": 48.0, "Mao Tashiro": 44.5, "Jatta Leinonen": 47.5}

# GENERATED: a 2026 Women's registration cancelled more than 30 days before the race (refund 45 EUR),
# and a pair that formed an entry but never registered (D2).
CANCELLED_2026 = ("WOMEN", "Oona Laitinen", "Noora Heikkinen", "FIN", "2026-01-10 18:20:00", "2026-05-20 09:00:00")
UNREGISTERED_ENTRY = ("Ville Korhonen", "Emilia Nurmi", "FIN")

# GENERATED protests (2026). (series, protesting bib, minutes after last finisher, reason, outcome,
# minutes to decision, votes chief/jury1/jury2)
PROTESTS_2026 = [
    ("MAIN", 22, 5, "Pair 21 obstructed our line at the water obstacle.", "Rejected", 30, ["Reject", "Reject", "Reject"]),
    ("M40", 12, 8, "Finish time recorded late; video shows 1:40.2. Corrected before publication.", "Upheld", 25,
     ["Uphold", "Uphold", "Uphold"]),
    ("TEAM", 105, 5, "Contest the +15 s penalty: the drink was not spilled at the exchange.", "Pending", None, None),
    ("MAIN", 59, 10, "Footwear of pair 64 was not inspected before the start.", "Pending", None, None),
]

# GENERATED special prizes 2026: prize id -> (series, bib)
SPECIAL_AWARDS_2026 = {5: ("WOMEN", 6), 6: ("TEAM", 102), 7: ("MAIN", 49)}
