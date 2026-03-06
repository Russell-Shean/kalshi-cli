import pandas as pd
import random
from datetime import datetime, timedelta
from googleapiclient.http import MediaFileUpload
from utils import build_google_service

# Output file
output_file = "nba_player_stats.xlsx"

# Google Drive folder ID
FOLDER_ID = "1BigVWckXCrG7DM-hANjDai-SgRMld7yZ"

# Sample players with accents/punctuation
players = [
    "Luka Dončić",
    "Nikola Jokić",
    "Giannis Antetokounmpo",
    "Shai Gilgeous-Alexander",
    "Karl-Anthony Towns",
    "Bogdan Bogdanović",
    "Tim Hardaway Jr.",
    "D'Angelo Russell",
    "José Alvarado",
    "Dennis Schröder",
    "RJ Barrett",
    "Jalen Williams"
]

teams = [
    "DAL", "DEN", "MIL", "OKC", "MIN", "ATL",
    "DAL", "LAL", "NOP", "BKN", "TOR", "OKC"
]

def random_date():
    today = datetime.today()
    return (today - timedelta(days=random.randint(1,7))).date()

def random_pct():
    return round(random.uniform(0.25, 0.95) * 100, 2)

def build_base_rows():
    rows = []
    for p, t in zip(players, teams):
        rows.append({
            "Player Name": p,
            "Team": t,
            "Current Season Games Played": random.randint(5, 75),
            "Date of Last Game Played": random_date()
        })
    return rows

points_cols = [
    "10 PTS Success %",
    "15 PTS Success %",
    "20 PTS Success %",
    "25 PTS Success %",
    "30 PTS Success %"
]

reb_cols = [
    "2 RBS Success %",
    "4 RBS Success %",
    "6 RBS Success %",
    "8 RBS Success %",
    "10 RBS Success %"
]

ast_cols = [
    "2 AST Success %",
    "4 AST Success %",
    "6 AST Success %",
    "8 AST Success %",
    "10 AST Success %"
]

three_cols = [
    "1 3s Success %",
    "2 3s Success %",
    "3 3s Success %",
    "4 3s Success %",
    "5 3s Success %"
]

def build_sheet(columns, avg_name):
    rows = build_base_rows()
    for r in rows:
        r[avg_name] = round(random.uniform(1, 30), 2)
        for c in columns:
            r[c] = random_pct()
    return pd.DataFrame(rows)

points_df = build_sheet(points_cols, "Recent Points Average")
reb_df = build_sheet(reb_cols, "Recent Rebounds Average")
ast_df = build_sheet(ast_cols, "Recent Assists Average")
three_df = build_sheet(three_cols, "Recent 3PT Average")

# Write Excel workbook
with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    points_df.to_excel(writer, sheet_name="Points", index=False)
    reb_df.to_excel(writer, sheet_name="Rebounds", index=False)
    ast_df.to_excel(writer, sheet_name="Assists", index=False)
    three_df.to_excel(writer, sheet_name="Three Pointers", index=False)

print(f"Workbook '{output_file}' created successfully.")

# -----------------------------
# Upload and convert to Sheets
# -----------------------------

drive_service = build_google_service("drive")

file_metadata = {
    "name": "NBA Player Stats",
    "parents": [FOLDER_ID],
    "mimeType": "application/vnd.google-apps.spreadsheet"
}

media = MediaFileUpload(
    output_file,
    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    resumable=True
)

uploaded_file = drive_service.files().create(
    body=file_metadata,
    media_body=media,
    fields="id, webViewLink"
).execute()

print("File uploaded and converted to Google Sheets.")
print("Spreadsheet ID:", uploaded_file["id"])
print("Open in browser:", uploaded_file["webViewLink"])