"""Tests for the Google Sheets service.

All calls to ``googleapiclient`` are mocked so no real API requests are made.
"""

import json
from unittest.mock import MagicMock

import pytest

from app.services.sheets_service import SheetsService

SERVICE_ACCOUNT_JSON = json.dumps(
    {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test@test-project.iam.gserviceaccount.com",
    }
)

SHEET_ID = "test_sheet_id"


def _make_service(mocker, execute_return):
    """Patch ``build`` and ``Credentials`` and return a (SheetsService, mock_service) pair.

    Mocking ``Credentials`` avoids parsing a real service account private key;
    mocking ``build`` avoids any real Google Sheets API call.
    """
    mocker.patch("app.services.sheets_service.Credentials")
    mock_build = mocker.patch("app.services.sheets_service.build")
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = (
        execute_return
    )
    return SheetsService(credentials_json=SERVICE_ACCOUNT_JSON, sheet_id=SHEET_ID), mock_service


def test_read_gig_rows_maps_rows_to_dicts(mocker):
    execute_return = {
        "values": [
            ["Gig Title", "Category", "Status", "Price"],
            ["I will write a python script", "Programming & Tech", "draft", "25"],
            ["I will design a logo", "Graphics & Design", "pending", "50"],
        ]
    }
    service, mock_service = _make_service(mocker, execute_return)

    rows = service.read_gig_rows("Gigs!A:D")

    assert len(rows) == 2
    assert rows[0] == {
        "Gig Title": "I will write a python script",
        "Category": "Programming & Tech",
        "Status": "draft",
        "Price": "25",
    }
    assert rows[1] == {
        "Gig Title": "I will design a logo",
        "Category": "Graphics & Design",
        "Status": "pending",
        "Price": "50",
    }
    mock_service.spreadsheets.return_value.values.return_value.get.assert_called_once_with(
        spreadsheetId=SHEET_ID, range="Gigs!A:D"
    )


def test_read_gig_rows_uses_default_range(mocker):
    execute_return = {"values": [["Gig Title", "Status"], ["x", "draft"]]}
    service, mock_service = _make_service(mocker, execute_return)

    rows = service.read_gig_rows()

    assert rows == [{"Gig Title": "x", "Status": "draft"}]
    mock_service.spreadsheets.return_value.values.return_value.get.assert_called_once_with(
        spreadsheetId=SHEET_ID, range="Gigs!A:Z"
    )


def test_read_gig_rows_pads_short_rows(mocker):
    execute_return = {
        "values": [
            ["Gig Title", "Category", "Status", "Price"],
            ["I will write a python script", "Programming & Tech"],
        ]
    }
    service, _ = _make_service(mocker, execute_return)

    rows = service.read_gig_rows("Gigs!A:D")

    assert len(rows) == 1
    assert rows[0]["Gig Title"] == "I will write a python script"
    assert rows[0]["Category"] == "Programming & Tech"
    assert rows[0]["Status"] is None
    assert rows[0]["Price"] is None


def test_read_gig_rows_returns_empty_for_no_values(mocker):
    execute_return = {}
    service, _ = _make_service(mocker, execute_return)

    assert service.read_gig_rows("Gigs!A:Z") == []

    execute_return = {"values": []}
    service, _ = _make_service(mocker, execute_return)
    assert service.read_gig_rows("Gigs!A:Z") == []


def test_update_gig_status_uses_batch_update(mocker):
    mocker.patch("app.services.sheets_service.Credentials")
    mock_build = mocker.patch("app.services.sheets_service.build")
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.spreadsheets.return_value.values.return_value.batchUpdate.return_value.execute.return_value = (
        {"replies": []}
    )
    service = SheetsService(
        credentials_json=SERVICE_ACCOUNT_JSON, sheet_id=SHEET_ID
    )

    result = service.update_gig_status(
        0,
        "published",
        gig_id="gig_123",
        gig_url="https://fiverr.com/gig/123",
    )

    assert result == {"replies": []}
    _, kwargs = mock_service.spreadsheets.return_value.values.return_value.batchUpdate.call_args
    assert kwargs["spreadsheetId"] == SHEET_ID
    assert kwargs["body"]["valueInputOption"] == "USER_ENTERED"

    data = kwargs["body"]["data"]
    ranges = [entry["range"] for entry in data]
    # row_index 0 + header offset 2 => sheet row 2
    assert "Gigs!S2" in ranges
    assert "Gigs!T2" in ranges
    assert "Gigs!U2" in ranges
    # error_message not provided => column V not updated
    assert not any(entry["range"] == "Gigs!V2" for entry in data)

    status_entry = next(e for e in data if e["range"] == "Gigs!S2")
    assert status_entry["values"] == [["published"]]
    gig_id_entry = next(e for e in data if e["range"] == "Gigs!T2")
    assert gig_id_entry["values"] == [["gig_123"]]
    gig_url_entry = next(e for e in data if e["range"] == "Gigs!U2")
    assert gig_url_entry["values"] == [["https://fiverr.com/gig/123"]]
