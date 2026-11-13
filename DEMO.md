# Demo video script (≤ 10 minutes)

Two windows: **the browser** at <http://localhost:5000>, and **a terminal** with the database shell:

```bash
mysql -u phase4 -p eukonkanto_db      # password: phase4
```

Start from a fresh database (`mysql -u phase4 -p < src/schema.sql && mysql -u phase4 -p < src/populate.sql`)
so the IDs below match. The order follows the feature list in `README.md`.

## 0. Tour (≈ 45 s)

"The site is modelled on eukonkanto.fi, the Wife Carrying World Championships in Sonkajärvi." Show:

- **Front page:** 2027 dates and the 2026 winners
- **Navigation:** The Event, Competitors, Staff Desk
- **Results:** 2026 Team tab, with the bib numbers and the +15 s penalty under Team 2 SPOLK
- **Show SQL:** open the panel once and say that every page has one

## Writes (≈ 5 min): before SQL → UI action → the same SQL again

**1. Register a pair (I1)**
```sql
SELECT r.Registration_ID, r.Bib_No, n.Display_Name FROM REGISTRATION r JOIN v_entry_name n USING (Entry_ID)
WHERE r.Edition_Year = 2027 AND r.Race_No = 5 ORDER BY r.Registration_ID;
```
- **UI:** Register.
  1. Series World Championship. Carrier: new person, born 2012-01-01. Carried: new person, born 1998-05-05, 52 kg.
  2. Press Register: the trigger error "Carrier must be at least 18 …" appears.
  3. Change the carrier's birth date to 1990-01-01 and register again.
  4. Note the registration number (172).
- **After:** re-run the SQL. A new row with bib 72 appears.

**2. Cancel a registration (U2)**
```sql
SELECT Registration_ID, Bib_No, Cancelled_At, Payment_Status, Status, Refund_EUR
FROM v_registration WHERE Registration_ID = 164;
```
- **UI:** Manage my registration, number 164 (Shane Williams / Lauren Williams), Cancel registration.
  The page reports a 45 € refund.
- **After:** `Cancelled_At` is set, `Bib_No` is NULL, the payment is refunded and `Refund_EUR` is 45.00.

**3. Replace a member (U4)**
```sql
SELECT pa.Role_Code, p.First_Name, p.Last_Name, pa.Measured_Weight_kg FROM PARTICIPATES_AS pa
JOIN PERSON p USING (Person_ID) WHERE pa.Entry_ID = (SELECT Entry_ID FROM REGISTRATION WHERE Registration_ID = 172);
```
- **UI:** Manage my registration, number 172, Replace on the carried person: new person, 1997-07-07, 60 kg.
- **After:** the CARRIED row shows the new person.
- Optionally try Replace on registration 31 (a 2026 entry): no Replace button is offered, and the
  database would refuse it with "already has results".

**Staff login (before step 4)**
- **Terminal:** `curl -i -X DELETE http://localhost:5000/api/registrations/172` answers
  `401` with "Staff login required": the API itself refuses staff actions without a login.
- **UI:** open Staff Desk › Organiser: the page sends you to the login page. A wrong password shows
  "Wrong username or password". Log in as `anne` / `staff2027` (Anne Ryynänen, Timekeeper); the menu now
  shows the desk pages and "Log out (Anne Ryynänen)".

**4. Delete a registration that never ran (D1)**
```sql
SELECT Registration_ID, Bib_No FROM REGISTRATION WHERE Registration_ID IN (31, 172);
```
- **UI:** Staff Desk › Organiser, edition 2026, World Championship.
  - Delete bib 62: refused with "Registration has results".
  - Switch to 2027 and delete registration 172.
- **After:** only registration 31 remains.

**5. Delete an entry with no registrations (D2)**
```sql
SELECT e.Entry_ID, n.Display_Name, (SELECT COUNT(*) FROM PARTICIPATES_AS pa WHERE pa.Entry_ID = e.Entry_ID) AS roles
FROM ENTRY e JOIN v_entry_name n USING (Entry_ID) WHERE e.Entry_ID = 76;
SELECT COUNT(*) FROM PERSON WHERE Last_Name IN ('Korhonen', 'Nurmi');
```
- **UI:** Organiser, Entries with no registrations, Delete entry on Ville Korhonen / Emilia Nurmi.
- **After:** the entry and its roles are gone; the two people are still there.

**6. Remove an unpaid booth booking (D3)**
```sql
SELECT v.Vendor_ID, v.Business_Name, x.Edition_Year, x.Paid FROM VENDOR v
LEFT JOIN EXHIBITS_AT x USING (Vendor_ID) WHERE v.Vendor_ID IN (2, 8) ORDER BY 1, 3;
```
- **UI:** Staff Desk › Organiser, Market booth bookings, edition 2027. (The public Market Place shows
  the same table with no remove button.)
  - Remove Retkeilijän Grilli: the page says the vendor was deleted, because it had no other booking.
  - Remove Savon Käsityöpaja: the vendor is kept because of its 2026 booking.
- **After:** vendor 8 is gone; vendor 2 has only its 2026 row.

**7. Record a result (I2)**
```sql
SELECT * FROM v_result WHERE Registration_ID = 167;
```
- **UI:** Staff Desk › Jury.
  1. The toolbar shows "Recording as Anne Ryynänen". Edition 2027, Sprint, Heat 1.
  2. Record a result for bib 70: Finished, 36.12.
  3. Show a refused case: in 2026 World Championship, recording a "Heat" is not offered, and the
     database rejects it with "has no heats".
- **After:** one row, rank 1.

**8. Correct a time (U1)**
```sql
SELECT Bib_No, Raw_Time_s, Net_Time_s, Rank_In_Stage, Recorded_By_Official_ID FROM v_result
WHERE Edition_Year = 2026 AND Series_Code = 'MAIN' AND Bib_No IN (49, 62);
SELECT a.Prize_ID, r.Bib_No FROM AWARDED a JOIN REGISTRATION r USING (Registration_ID)
WHERE r.Edition_Year = 2026 AND r.Race_No = 5 AND a.Prize_ID IN (1, 3);
```
- **UI:** Jury, edition 2026, World Championship, Edit time on bib 49: 60.0, Save.
- **After:** bib 49 is rank 1 and bib 62 rank 2. The champion's prize (1) moved to bib 49, and the
  recorder is Anne, the logged-in official (`Recorded_By_Official_ID` 239).

**9. File a protest (I3)**
```sql
SELECT Protest_ID, Filed_At, Outcome, Entry_ID FROM PROTEST ORDER BY Protest_ID;
```
- **UI:** Jury, 2026 World Championship, File a protest.
  1. Entry bib 22, filed at 2026-07-04 16:50, reason "Obstruction": refused, outside the 15-minute window.
  2. Change the time to 16:35 and file again.
- **After:** protest 5 is Pending.

**10. Decide a protest (U3)**
```sql
SELECT Protest_ID, Outcome, Decided_At FROM PROTEST WHERE Protest_ID = 3;
SELECT * FROM DECIDES WHERE Protest_ID = 3;
SELECT Bib_No, Penalty_s, Net_Time_s, Rank_In_Stage FROM v_result WHERE Edition_Year = 2026 AND Bib_No = 105;
```
- **UI:** Jury, Pending protests, Protest 3 (Team 2 SPOLK): outcome Upheld, three Uphold votes,
  "Remove penalty 1 of bib 105", Record decision.
- **After:** Upheld with a decision time, 3 votes, and the penalty gone (net 139.9).

**11. Award a prize (I4)**
```sql
SELECT a.Prize_ID, p.Prize_Name, r.Bib_No FROM AWARDED a JOIN PRIZE p USING (Prize_ID)
JOIN REGISTRATION r USING (Registration_ID) WHERE r.Edition_Year = 2026 AND a.Prize_ID = 6;
```
- **UI:** Organiser, 2026, Sprint.
  1. Award "Second place product prize" to bib 78 (the winner): refused, "does not match rank".
  2. Switch to World Championship and award "Best costume" to bib 62.
- **After:** the Best costume row now includes bib 62.

## Queries (≈ 3.5 min): run each from the UI

1. **S3:** Results, 2026, Sprint, Final. The order is Tuovinen, Wasenius, Nash, Lee, the same as eukonkanto.fi.
2. **A1:** Champions and Records. 56.9, 1:24.6, 31.34, 1:13.49, 1:39.51, the same as the site's records page.
3. **Q1, Q2:** Header search "kirk", then "sonkaj" for teams and organisations. Open a person's page.
4. **Q3, P2:** Registered Competitors, 2026, World Championship, country GBR: bibs 44, 51, 63. Then the Teams tab.
5. **Q4, P3:** Market Place, search category Food, then the booth table for 2026.
6. **S1, P1, A5:** Organiser, 2026, World Championship: registrations, persons in the edition, heaviest carried.
7. **S2:** Jury, the pending protests list.
8. **A2 to AR6:** Committee reports. Click through Average times, Fees, By country (2026), Medal table,
   Backpacks, Multi-series (2026, where Andrew Lee appears in three series), Income, Protests, and
   Faster than average.
