"""
Lead Tracker — Cold Outreach CRM (Local CSV)
=============================================
Tracks brands you've DMed, their response status, and deal value.
Zero dependencies. Pure CSV.

Usage:
  python lead_tracker.py add "BrandName" "tiktok" "@handle" "shoes"
  python lead_tracker.py status "BrandName" "replied"
  python lead_tracker.py list
  python lead_tracker.py stats
"""
import csv
import os
import sys
from datetime import datetime

CSV_FILE = os.path.join(os.path.dirname(__file__), "leads.csv")
HEADERS = ["brand", "platform", "handle", "niche", "status", "dm_date", "notes", "deal_value"]

VALID_STATUSES = ["prospect", "dm_sent", "replied", "negotiating", "closed", "lost"]


def _ensure_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(HEADERS)


def add_lead(brand, platform, handle, niche, notes=""):
    _ensure_csv()
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([brand, platform, handle, niche, "prospect", datetime.now().strftime("%Y-%m-%d"), notes, "0"])
    print(f"✅ Lead added: {brand} ({platform} — {handle})")


def update_status(brand, new_status, deal_value=None):
    if new_status not in VALID_STATUSES:
        print(f"❌ Invalid status. Use one of: {', '.join(VALID_STATUSES)}")
        return
    _ensure_csv()
    rows = []
    found = False
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].lower() == brand.lower() and row != HEADERS:
                row[4] = new_status
                if deal_value:
                    row[7] = deal_value
                found = True
            rows.append(row)
    if found:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        print(f"✅ {brand} updated to: {new_status}")
    else:
        print(f"❌ Brand '{brand}' not found in leads.")


def list_leads():
    _ensure_csv()
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)
    if not rows:
        print("📭 No leads yet. Start prospecting!")
        return
    print(f"\n{'Brand':<20} {'Platform':<10} {'Handle':<20} {'Niche':<12} {'Status':<14} {'DM Date':<12} {'Deal $':<8}")
    print("─" * 100)
    for r in rows:
        if len(r) >= 8:
            print(f"{r[0]:<20} {r[1]:<10} {r[2]:<20} {r[3]:<12} {r[4]:<14} {r[5]:<12} ${r[7]:<8}")


def show_stats():
    _ensure_csv()
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip headers
        rows = list(reader)
    if not rows:
        print("📭 No leads yet.")
        return
    total = len(rows)
    by_status = {}
    total_revenue = 0
    for r in rows:
        if len(r) >= 8:
            s = r[4]
            by_status[s] = by_status.get(s, 0) + 1
            try:
                total_revenue += float(r[7])
            except ValueError:
                pass
    print(f"\n📊 PIPELINE STATS")
    print(f"   Total Leads: {total}")
    for s in VALID_STATUSES:
        count = by_status.get(s, 0)
        if count:
            print(f"   {s.title()}: {count}")
    print(f"   💰 Total Deal Value: ${total_revenue:.0f}")
    if by_status.get("closed", 0) and by_status.get("dm_sent", 0):
        rate = by_status["closed"] / (by_status.get("dm_sent", 1) + by_status.get("replied", 0) + by_status.get("negotiating", 0) + by_status["closed"]) * 100
        print(f"   📈 Close Rate: {rate:.0f}%")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print('  python lead_tracker.py add "BrandName" "tiktok" "@handle" "shoes"')
        print('  python lead_tracker.py status "BrandName" "replied" [deal_value]')
        print("  python lead_tracker.py list")
        print("  python lead_tracker.py stats")
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "add" and len(sys.argv) >= 6:
        notes = sys.argv[6] if len(sys.argv) > 6 else ""
        add_lead(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], notes)
    elif cmd == "status" and len(sys.argv) >= 4:
        dv = sys.argv[4] if len(sys.argv) > 4 else None
        update_status(sys.argv[2], sys.argv[3], dv)
    elif cmd == "list":
        list_leads()
    elif cmd == "stats":
        show_stats()
    else:
        print("❌ Invalid command. Run without arguments for usage info.")
