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
