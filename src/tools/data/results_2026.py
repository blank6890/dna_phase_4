"""2026 results transcribed from https://eukonkanto.fi/en/results/ (fetched 2026-11-13).

Row format:  bib | carrier | carried | countries | time
  * countries: ISO alpha-3 codes joined by '/'; the first is the carrier's citizenship,
    the last the carried person's (all codes become REPRESENTS rows).
  * time: m:ss.d or ss.cc as on the site, or DNS.
Team rows: bib | carrier 1 | carried | carrier 2 | carrier 3 | team name | countries | time
Names truncated on the site use the full name from its extra column.
"""

EDITION = 2026

SPRINT_ENTRIES = """
70|Jonatan Wasenius|Lotta Lindroos|FIN
71|Janno Sild|Anu Sild|EST
72|Robert Rissanen|Amelia Lintu|FIN
73|Saku Kuosmanen|Helmi-Riina Kangas|FIN
74|Khid Khairudin|Friida Turku|SGP
75|Ibrahim Asad|Emma Schellpeper|USA
76|Edward Nash|Kathryn Knight|GBR
77|Samuel Niemelä|Krista Saarinen|FIN
78|Teemu Tuovinen|Jatta Leinonen|FIN
79|Markus Ilves|Mairen Mangusson|EST
80|Andrew Lee|Devon Lee|USA
"""

SPRINT_STAGES = {  # stage -> [(bib, time)]
    "Heat 1": [(70, "34.87"), (73, "39.61"), (71, "42.71"), (72, "49.21")],
    "Heat 2": [(76, "37.07"), (74, "42.97"), (77, "47.57"), (75, "49.32")],
    "Heat 3": [(78, "35.80"), (80, "39.46"), (79, "43.11")],
    "Final":  [(78, "33.77"), (70, "34.38"), (76, "35.61"), (80, "42.37")],
}

TEAM = """
104|Andrew Lee|Devon Lee|Joshua Crafter|Vytautas Kirkliauskas|Team Beer for my Horses|USA/LTU|1:51.3
106|Jani Kumpulehto|Siiri Koskinen|John Lund|Joni Juntunen|Team Big Beef|FIN|2:09.2
105|Santeri Ilmivalta|Katy Hagstedt|Lumi Hakomäki|Jori Juntunen|Team 2 SPOLK|FIN/USA|2:19.9
101|Pekka Savolainen|Sanna Jäntti|Leevi Partanen|Tatu Heiskanen|MTK Sonkajärven maaseutunuoret|FIN|2:57.5
103|Heikki Korolainen|Annika Jokelai|Ville Kamaja|Waldo Seppä|Sonkajärven kunta|FIN|3:05.9
100|Lasse Sevon|Venla Luukkonen|Kristian Saarisalo|Nicklas Sutinen|Tulitaistelijat P121|FIN|3:07.8
102|Kari Väisänen|Sanna|Pasi Nenonen|Aki Taskinen|Sakkyn toivot|FIN|3:14.9
"""
# Bib 105: the site shows 2:34.9 including "Aikasakko +15 sek"; stored as raw 2:19.9 + 15 s PENALTY.
TEAM_PENALTIES = [(105, "Penalty", 15, "Spilled wife-carrying drink at the exchange (Aikasakko +15 sek)")]
TEAM_ORGANISATIONS = {"MTK Sonkajärven maaseutunuoret", "Sonkajärven kunta"}

WOMEN = """
1|Sini Ylönen|Jasmin Kaivola|FIN|1:47.0
2|Elina Lohi|Johanna Kupiainen|FIN|1:49.9
4|Mona Vanha|Juulia Yliheikkilä|FIN|2:13.0
3|Nea Nieminen|Susanna Valtari|FIN|2:48.0
6|Akira Ahola|Leo Tapio|FIN|5:45.4
5|Janita Riekkinen|Sanna Jäntti|FIN|DNS
"""

M40 = """
13|Tero Heikkinen|Päivi Heikkinen|FIN|73.49
19|Timo Föhr|Suvi Björk|FIN|1:17.0
10|James Forster|Jenni Forster|FIN|1:18.2
15|Andrew Lee|Devon Lee|USA|1:25.7
17|Petri Toivanen|Joida Arca|FIN|1:26.0
11|Sami Jokiniemi|Sari Pennanen|FIN|1:27.2
8|Janno Sild|Anu Sild|EST|1:33.9
12|Bob Zuver|Christina Brown|USA|1:40.2
18|Mikko Laitinen|Veepi Viinikainen|FIN|1:47.8
9|Ilkka Kojola|Niina Svenlin|FIN|1:54.2
14|Timo Jutila|Henna Rundgren|FIN|2:01.3
16|Jason Benedict|Janelle Benedict|CAN|2:16.5
7|Karl Robbins|Erin Kuosmanen|USA/FIN|3:11.0
"""
# Bib 13: results page shows 1:13.4, the records page 1.13.49; the record value is stored.

MAIN = """
62|Taisto Miettinen|Katja Kovanen|FIN|1:04.4
49|Vytautas Kirkliauskas|Neringa Kirkliauskiene|LTU|1:06.2
42|Jonatan Wasenius|Lotta Lindroos|FIN|1:07.1
47|Teemu Tuovinen|Jatta Leinonen|FIN|1:08.8
44|Edward Nash|Kathryn Knight|GBR|1:09.6
58|Ville Honkanen|Elviira Mikkonen|FIN|1:10.2
50|Perttu Saarinen|Senja Auvinen|FIN|1:11.8
32|Akseli Aninko|Helmi-Riina Kangas|FIN|1:15.5
48|Jori Mäkkeli|Pauliina Mäkkeli|FIN|1:15.5
21|Ivan Voronkov|Svetlana|RUS/FIN/UKR|1:17.0
22|Donncha O’Callaghan|Emma Doran|IRL|1:17.0
25|Jari Ruotsalainen|Aada Rissanen|FIN|1:17.1
37|Lasse Kuurila|Elina Lukkarinen|FIN|1:18.7
45|Matti Karttunen|Anette Lönnqvist|FIN|1:19.7
57|Teemu Kylämäki|Johanna Syrjämäki|FIN|1:19.8
64|Karol Bizewski|Elina Huhtanen|FIN|1:20.9
41|Joonas Sulisalo|Luara Silva|FIN/BRA|1:22.0
34|Teemu Seppä|Katja Kortström|FIN|1:22.0
40|Khid Khairudin|Friida Turku|SGP|1:22.0
30|Kalle Ujainen|Anna Vaalivirta|FIN|1:22.5
35|Robert Rissanen|Amelia Lintu|FIN|1:23.1
52|Juuso Suhonen|Aija Ylönen|FIN|1:23.5
53|Lare Lautiainen|Serinja Berg|FIN|1:25.2
46|Jens Olesen|Sonja Cerne|SWE|1:25.3
56|Markus Ilves|Mairen Mangusson|EST|1:26.2
29|Nikolaos Mach|Kristina Machova|CZE|1:27.6
54|Leo Tapio|Akira Ahola|FIN|1:29.6
60|Joshua Crafter|Anette Nilsen|USA|1:30.1
59|Mikael Rauste|Minttu-Ida Sykkö|FIN|1:32.1
61|Yusuf Riaz|Julia Silvennoinen|FIN|1:34.8
36|Pyry Pöyry|Rosie Pöyry|FIN|1:35.4
43|Timo Niinivaara|Vaimo|FIN|1:35.6
24|Joseph Ryan Casipong|Eugelynn Marie Glynn|PHL|1:36.8
51|Robert Sapsed|Paula Knevitt|GBR|1:37.1
39|Juho Luoma|Emmi Hannuksela|FIN|1:40.6
38|Teemu Tapio|Laura Hietamäki|FIN|1:49.6
20|Francois|Mathilde|FRA|1:53.5
63|Andrew Nettle|Alexa Nettle|GBR|1:56.8
28|Rei Higashida|Mao Tashiro|FIN|1:59.9
26|Tseng I Hung|Lina Reiter|SGP/DEU|2:12.3
23|David Polak|Simona Polakova|SVK|2:16.5
31|Tihomir Simin|Sanna Rautiainen|SRB/FIN|2:22.2
27|John Lund|Stefanie Weisseisen-Lund|USA/AUT|3:29.4
33|Victor Kraft|Erica Scognamiglio|ITA|DNS
55|Antti Romppanen|Janina Filenius-Romppainen|FIN|DNS
"""
