#!/usr/bin/env python3
"""Sync Uber Eats orders from Gmail to MySQL.

Reads the latest order date from the database, searches Gmail via IMAP
for newer Uber Eats receipt emails, parses them, and inserts new orders.

Usage:
    python scripts/sync_uber_eats_orders.py

Environment variables (or .env file in project root):
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
    GMAIL_USER        - Gmail address (e.g. you@gmail.com)
    GMAIL_APP_PASSWORD - Gmail App Password (not your regular password)

To generate a Gmail App Password:
    1. Go to https://myaccount.google.com/apppasswords
    2. Select "Mail" and your device
    3. Copy the 16-character password

Schedule with cron (every Monday at 9 AM):
    0 9 * * 1 cd /path/to/python-projects && python scripts/sync_uber_eats_orders.py >> logs/sync.log 2>&1
"""

from __future__ import annotations

import email
import imaplib
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pymysql
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GROCERY_KEYWORDS = [
    "walmart", "costco", "no frills", "freshco", "save-on-foods",
    "safeway", "fraserview meats", "t&t", "superstore",
]

SEED_FILE = PROJECT_ROOT / "schema" / "uber_eats_seed.sql"


def get_db_connection() -> pymysql.Connection:
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "healthcare"),
        charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
        autocommit=True,
    )


def get_latest_order_date(conn: pymysql.Connection) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(order_date) FROM uber_eats_orders")
        row = cur.fetchone()
        if row and row[0]:
            return row[0].strftime("%Y-%m-%d") if hasattr(row[0], "strftime") else str(row[0])
    return "2023-01-01"


def classify_order_type(restaurant: str) -> str:
    name_lower = restaurant.lower()
    for keyword in GROCERY_KEYWORDS:
        if keyword in name_lower:
            return "grocery"
    return "restaurant"


def connect_gmail() -> imaplib.IMAP4_SSL:
    user = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASSWORD")
    if not user or not password:
        print("ERROR: Set GMAIL_USER and GMAIL_APP_PASSWORD in .env")
        sys.exit(1)
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(user, password)
    return imap


def search_uber_eats_emails(imap: imaplib.IMAP4_SSL, since_date: str) -> list[bytes]:
    imap.select('"[Gmail]/All Mail"')
    since_dt = datetime.strptime(since_date, "%Y-%m-%d")
    since_imap = since_dt.strftime("%d-%b-%Y")
    criteria = f'(FROM "noreply@uber.com" SUBJECT "order with Uber Eats" SINCE {since_imap})'
    _, data = imap.search(None, criteria)
    return data[0].split() if data[0] else []


def parse_receipt_email(imap: imaplib.IMAP4_SSL, msg_id: bytes) -> dict | None:
    _, data = imap.fetch(msg_id, "(RFC822)")
    if not data or not data[0]:
        return None
    msg = email.message_from_bytes(data[0][1])
    subject = str(email.header.decode_header(msg["Subject"])[0][0])
    if isinstance(subject, bytes):
        subject = subject.decode("utf-8", errors="replace")

    date_str = msg["Date"]
    try:
        order_date = email.utils.parsedate_to_datetime(date_str).strftime("%Y-%m-%d")
    except Exception:
        return None

    restaurant_match = re.search(
        r"Your .+ order with Uber Eats",
        subject.replace("[Personal] ", ""),
    )
    if not restaurant_match:
        return None
    restaurant = subject.replace("[Personal] ", "")
    restaurant = re.sub(r"^Your ", "", restaurant)
    restaurant = re.sub(r" order with Uber Eats.*", "", restaurant)
    restaurant = restaurant.strip()

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode("utf-8", errors="replace")
                    break
            elif part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode("utf-8", errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode("utf-8", errors="replace")

    amount_match = re.search(r"(?:CA)?\$\s*([\d,]+\.\d{2})", body)
    if not amount_match:
        amount_match = re.search(r"Total\s*(?:CA)?\$\s*([\d,]+\.\d{2})", body, re.IGNORECASE)
    if not amount_match:
        return None

    amount = float(amount_match.group(1).replace(",", ""))

    return {
        "order_date": order_date,
        "restaurant": restaurant,
        "amount": amount,
        "currency": "CAD",
        "order_type": classify_order_type(restaurant),
    }


def insert_order(conn: pymysql.Connection, order: dict) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM uber_eats_orders "
            "WHERE order_date = %s AND restaurant = %s AND amount = %s",
            (order["order_date"], order["restaurant"], order["amount"]),
        )
        if cur.fetchone()[0] > 0:
            return False

        cur.execute(
            "INSERT INTO uber_eats_orders (order_date, restaurant, amount, currency, order_type) "
            "VALUES (%s, %s, %s, %s, %s)",
            (order["order_date"], order["restaurant"], order["amount"],
             order["currency"], order["order_type"]),
        )
        return True


def append_to_seed_file(orders: list[dict]) -> None:
    if not orders:
        return
    lines = []
    for o in orders:
        restaurant_escaped = o["restaurant"].replace("'", "\\'")
        lines.append(
            f"INSERT INTO uber_eats_orders (order_date, restaurant, amount, currency, order_type) "
            f"VALUES ('{o['order_date']}', '{restaurant_escaped}', {o['amount']:.2f}, "
            f"'{o['currency']}', '{o['order_type']}');"
        )
    with open(SEED_FILE, "a") as f:
        f.write("\n\n-- Synced on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
        for line in lines:
            f.write(line + "\n")


def main() -> None:
    print(f"[{datetime.now()}] Starting Uber Eats order sync...")

    conn = get_db_connection()
    latest_date = get_latest_order_date(conn)
    print(f"Latest order in DB: {latest_date}")

    imap = connect_gmail()
    msg_ids = search_uber_eats_emails(imap, latest_date)
    print(f"Found {len(msg_ids)} receipt emails since {latest_date}")

    new_orders = []
    for msg_id in msg_ids:
        order = parse_receipt_email(imap, msg_id)
        if order and order["order_date"] > latest_date:
            new_orders.append(order)

    imap.logout()

    if not new_orders:
        print("No new orders found.")
        conn.close()
        return

    new_orders.sort(key=lambda o: o["order_date"])
    inserted = 0
    for order in new_orders:
        if insert_order(conn, order):
            inserted += 1
            print(f"  Inserted: {order['order_date']} | {order['restaurant']} | ${order['amount']:.2f} ({order['order_type']})")
        else:
            print(f"  Skipped (duplicate): {order['order_date']} | {order['restaurant']}")

    conn.close()

    append_to_seed_file([o for o in new_orders if insert_order is not None])

    print(f"\nDone. Inserted {inserted} new orders out of {len(new_orders)} found.")


if __name__ == "__main__":
    main()
