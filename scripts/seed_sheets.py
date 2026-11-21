"""Seed the Google Sheets workbook with a header row for gig content.

Usage:
    python scripts/seed_sheets.py

Requires GOOGLE_SHEETS_CREDENTIALS_JSON and GOOGLE_SHEET_ID in the environment
(via .env). The header row is written to ``Gigs!A1:<last_col>1`` using the
service account credentials.
"""

import logging

from app.services.sheets_service import SheetsService

SHEET_NAME = "Gigs"

# Columns S, T, U, V (1-based) hold Status, Gig ID, Gig URL and Error so that
# they stay in sync with SheetsService.update_gig_status.
HEADERS = [
    "Gig Title",
    "Category",
    "Subcategory",
    "Description",
    "Requirements",
    "Tags",
    "Image URLs",
    "Extras",
    "FAQ",
    "Package Basic Price",
    "Package Basic Days",
    "Package Basic Revisions",
    "Package Basic Features",
    "Package Standard Price",
    "Package Standard Days",
    "Package Standard Revisions",
    "Package Standard Features",
    "Package Premium Price",
    "Status",
    "Gig ID",
    "Gig URL",
    "Error",
]


def _column_letter(index: int) -> str:
    """Convert a 0-based column index to a spreadsheet column letter."""
    letters = []
    while index >= 0:
        letters.insert(0, chr(ord("A") + (index % 26)))
        index = index // 26 - 1
    return "".join(letters)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sheets = SheetsService()
    service = sheets.service
    last_column = _column_letter(len(HEADERS) - 1)
    range_name = f"{SHEET_NAME}!A1:{last_column}1"

    body = {"values": [HEADERS]}
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=sheets.sheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )
    logging.info("Seeded header row into %s: %s", range_name, result)


if __name__ == "__main__":
    main()
