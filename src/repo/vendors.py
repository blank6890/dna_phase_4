"""Market place vendors and booth bookings."""
import db

CATEGORIES = {"Food", "Handicrafts", "Local specialities"}

SEARCH_SQL = """
SELECT v.Vendor_ID, v.Business_Name, v.Contact_Name, v.Phone, v.Email,
       GROUP_CONCAT(c.Category ORDER BY c.Category SEPARATOR ', ') AS Categories
FROM VENDOR v
LEFT JOIN VENDOR_PRODUCT_CATEGORY c ON c.Vendor_ID = v.Vendor_ID
WHERE (%s IS NULL OR v.Business_Name LIKE %s)
  AND (%s IS NULL OR EXISTS (SELECT 1 FROM VENDOR_PRODUCT_CATEGORY c2
                              WHERE c2.Vendor_ID = v.Vendor_ID AND c2.Category = %s))
GROUP BY v.Vendor_ID, v.Business_Name, v.Contact_Name, v.Phone, v.Email
ORDER BY v.Business_Name"""


def search(q=None, category=None):
    pattern = db.like(q) if q else None
    return db.query(SEARCH_SQL, (q, pattern, category, category)), SEARCH_SQL


BOOTHS_SQL = """
SELECT v.Vendor_ID, v.Business_Name, x.Booth_Size, x.Booth_Fee_EUR,
       x.Electricity_Required, x.Paid
FROM EXHIBITS_AT x
JOIN VENDOR v ON v.Vendor_ID = x.Vendor_ID
WHERE x.Edition_Year = %s
ORDER BY v.Business_Name"""


def booths(year):
    return db.query(BOOTHS_SQL, (year,)), BOOTHS_SQL


# ---------------------------------------------------------------- D3 remove unpaid booking
from api import ApiError  # noqa: E402

LOCK_BOOKING_SQL = """
SELECT x.Paid, e.Start_Date <= CURDATE() AS Started
FROM EXHIBITS_AT x
JOIN EDITION e ON e.Edition_Year = x.Edition_Year
WHERE x.Vendor_ID = %s AND x.Edition_Year = %s
FOR UPDATE"""
DELETE_BOOKING_SQL = "DELETE FROM EXHIBITS_AT WHERE Vendor_ID = %s AND Edition_Year = %s"
DELETE_IDLE_VENDOR_SQL = """
DELETE FROM VENDOR
WHERE Vendor_ID = %s
  AND NOT EXISTS (SELECT 1 FROM EXHIBITS_AT x WHERE x.Vendor_ID = %s)"""


def remove_booking(vendor_id, year):
    """D3: only unpaid bookings before the event; the vendor goes too when it has no other booking."""
    with db.transaction() as cur:
        cur.execute(LOCK_BOOKING_SQL, (vendor_id, year))
        row = cur.fetchone()
        if row is None:
            raise ApiError(404, "Booking not found")
        if row["Paid"]:
            raise ApiError(409, "Booking is already paid")
        if row["Started"]:
            raise ApiError(409, "Edition has already started")
        cur.execute(DELETE_BOOKING_SQL, (vendor_id, year))
        cur.execute(DELETE_IDLE_VENDOR_SQL, (vendor_id, vendor_id))
        vendor_deleted = cur.rowcount == 1
    return vendor_deleted, (LOCK_BOOKING_SQL, DELETE_BOOKING_SQL, DELETE_IDLE_VENDOR_SQL)
