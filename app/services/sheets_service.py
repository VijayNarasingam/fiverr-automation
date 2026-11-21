"""Google Sheets service for reading gig rows and updating gig status.

Consumes :class:`app.config.Settings` (``GOOGLE_SHEETS_CREDENTIALS_JSON``,
``GOOGLE_SHEET_ID``) and wraps the Google Sheets API using a service account.
"""

import json
import logging
from typing import Optional

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from app.config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Column letters for the status-related fields. These line up with columns
# S, T, U, V of the sheet so the seed header row and the status update stay
# in sync.
STATUS_COLUMN = "S"
GIG_ID_COLUMN = "T"
GIG_URL_COLUMN = "U"
ERROR_COLUMN = "V"

# Row 1 is the header row and row_index is 0-based over data rows, so the
# spreadsheet row for a given row_index is row_index + 2.
ROW_OFFSET = 2


class SheetsService:
    """Wrapper around the Google Sheets API for the Fiverr automation agent."""

    def __init__(
        self,
        credentials_json: Optional[str] = None,
        sheet_id: Optional[str] = None,
    ):
        self.credentials_json = credentials_json or settings.GOOGLE_SHEETS_CREDENTIALS_JSON
        self.sheet_id = sheet_id or settings.GOOGLE_SHEET_ID
        self._service = None

    @property
    def service(self):
        """Lazily build and cache the Google Sheets API client."""
        if self._service is None:
            credentials = self._build_credentials()
            self._service = build(
                "sheets", "v4", credentials=credentials, cache_discovery=False
            )
        return self._service

    def _build_credentials(self) -> Credentials:
        """Build service account credentials from a JSON string or file path."""
        try:
            info = json.loads(self.credentials_json)
            return Credentials.from_service_account_info(info, scopes=SCOPES)
        except (json.JSONDecodeError, ValueError):
            # Fall back to treating the value as a path to a service account file.
            return Credentials.from_service_account_file(
                self.credentials_json, scopes=SCOPES
            )

    def _sheet_name(self, range_name: str = "Gigs!A:Z") -> str:
        return range_name.split("!")[0]

    def read_gig_rows(self, range_name: str = "Gigs!A:Z") -> list[dict]:
        """Read all rows from *range_name* and map them to dicts keyed by header.

        The first row is treated as the header row. Rows shorter than the
        header row are padded with ``None`` so every returned dict has the same
        keys.
        """
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self.sheet_id, range=range_name)
            .execute()
        )
        values = result.get("values", [])
        if not values:
            return []

        headers = values[0]
        rows: list[dict] = []
        for row in values[1:]:
            # Pad rows that are shorter than the header row.
            if len(row) < len(headers):
                row = list(row) + [None] * (len(headers) - len(row))
            row_dict = {}
            for idx, header in enumerate(headers):
                row_dict[header] = row[idx] if idx < len(row) else None
            rows.append(row_dict)
        return rows

    def update_gig_status(
        self,
        row_index: int,
        status: str,
        gig_id: Optional[str] = None,
        gig_url: Optional[str] = None,
        error_message: Optional[str] = None,
        sheet_name: str = "Gigs",
    ) -> dict:
        """Update the status (and optional gig metadata) for a data row.

        Column mapping (row_index + 2 offset for the header + 0-based index):
            status  -> column S
            gig_id  -> column T
            gig_url -> column U
            error   -> column V

        Uses ``batchUpdate`` with ``valueInputOption="USER_ENTERED"`` so only
        the provided fields are written.
        """
        sheet_row = row_index + ROW_OFFSET
        updates = []

        updates.append(
            {
                "range": f"{sheet_name}!{STATUS_COLUMN}{sheet_row}",
                "values": [[status]],
            }
        )
        if gig_id is not None:
            updates.append(
                {
                    "range": f"{sheet_name}!{GIG_ID_COLUMN}{sheet_row}",
                    "values": [[gig_id]],
                }
            )
        if gig_url is not None:
            updates.append(
                {
                    "range": f"{sheet_name}!{GIG_URL_COLUMN}{sheet_row}",
                    "values": [[gig_url]],
                }
            )
        if error_message is not None:
            updates.append(
                {
                    "range": f"{sheet_name}!{ERROR_COLUMN}{sheet_row}",
                    "values": [[error_message]],
                }
            )

        body = {"valueInputOption": "USER_ENTERED", "data": updates}

        result = (
            self.service.spreadsheets()
            .values()
            .batchUpdate(spreadsheetId=self.sheet_id, body=body)
            .execute()
        )
        logger.info(
            "Updated gig status for row_index %s (sheet row %s): %s",
            row_index,
            sheet_row,
            status,
        )
        return result
