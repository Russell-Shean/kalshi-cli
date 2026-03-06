import os
import json
import pandas as pd
from googleapiclient.http import MediaIoBaseDownload
from utils import build_google_service, normalize_name
import io

FOLDER_ID = "1BigVWckXCrG7DM-hANjDai-SgRMld7yZ"
DATA_DIR = "data"
LOCAL_FILE = os.path.join(DATA_DIR, "nba_player_stats.xlsx")
OUTPUT_JSON = os.path.join(DATA_DIR, "player_data.json")

# Map sheet names -> stat types
STAT_MAP = {
    "Points": "points",
    "Rebounds": "rebounds",
    "Assists": "assists",
    "Three Pointers": "threes"
}


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def find_sheet_in_folder(drive_service):
    """Find the first Google Sheet inside the target folder."""
    query = f"'{FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"

    results = drive_service.files().list(
        q=query,
        fields="files(id, name)"
    ).execute()

    files = results.get("files", [])

    if not files:
        raise Exception("No Google Sheets file found in folder")

    return files[0]["id"], files[0]["name"]


def download_sheet_as_excel(drive_service, file_id):
    """Export Google Sheet to XLSX locally."""
    request = drive_service.files().export_media(
        fileId=file_id,
        mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    fh = io.FileIO(LOCAL_FILE, "wb")
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    fh.close()


def extract_threshold(column_name):
    """
    Convert column name like '10 PTS Success %'
    into '10+'
    """
    num = column_name.split()[0]
    return f"{num}+"

def parse_workbook():
    """
    Read workbook and convert success columns
    into normalized records.
    """
    sheets = pd.read_excel(LOCAL_FILE, sheet_name=None)

    records = []

    for sheet_name, df in sheets.items():

        if sheet_name not in STAT_MAP:
            continue

        stat_type = STAT_MAP[sheet_name]

        success_cols = [c for c in df.columns if "Success %" in c]

        for _, row in df.iterrows():

            player = row["Player Name"]
            team = row.get("Team")

            for col in success_cols:

                threshold = extract_threshold(col)

                record = {
                    "player_name": normalize_name(player),
                    "stat_type": stat_type,
                    "threshold": threshold,
                    "success_probability": float(row[col]),
                    "team": team
                }

                records.append(record)

    return records


def main():

    ensure_data_dir()

    drive_service = build_google_service("drive")

    print("Finding spreadsheet in Drive folder...")
    file_id, file_name = find_sheet_in_folder(drive_service)

    print(f"Downloading {file_name}...")
    download_sheet_as_excel(drive_service, file_id)

    print("Parsing workbook...")
    player_dict = parse_workbook()

    print("Writing JSON...")
    with open(OUTPUT_JSON, "w") as f:
        json.dump(player_dict, f, indent=2)

    print(f"Finished. Output written to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()