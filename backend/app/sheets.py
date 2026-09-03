import re

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from app.config import settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

_SHEET_URL_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")


def is_sheets_configured() -> bool:
    return bool(settings.google_service_account_email and settings.google_service_account_private_key)


def extract_spreadsheet_id(raw: str) -> str:
    match = _SHEET_URL_RE.search(raw)
    return match.group(1) if match else raw.strip()


_FORBIDDEN_TAB_CHARS = re.compile(r"[:\\/?*\[\]]")


def make_tab_name(title: str, unique_suffix: str, max_len: int = 100) -> str:
    """Builds a Sheets tab name from a title, appending a short id so multiple
    surveys/assignments can safely share one spreadsheet without name clashes.
    """
    cleaned = _FORBIDDEN_TAB_CHARS.sub(" ", title).strip() or "제목 없음"
    suffix = f" ({unique_suffix[:6]})"
    return cleaned[: max_len - len(suffix)] + suffix


def _client():
    if not is_sheets_configured():
        raise RuntimeError(
            "Google Sheets 서비스 계정이 설정되지 않았습니다 "
            "(GOOGLE_SERVICE_ACCOUNT_EMAIL / GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY)."
        )
    private_key = settings.google_service_account_private_key.replace("\\n", "\n")
    creds = Credentials.from_service_account_info(
        {
            "client_email": settings.google_service_account_email,
            "private_key": private_key,
            "token_uri": "https://oauth2.googleapis.com/token",
        },
        scopes=SCOPES,
    )
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def ensure_tab_exists(sheet_id: str, tab_name: str) -> None:
    """Creates the tab if it doesn't already exist in the target spreadsheet."""
    service = _client()
    meta = (
        service.spreadsheets()
        .get(spreadsheetId=sheet_id, fields="sheets.properties.title")
        .execute()
    )
    titles = {s["properties"]["title"] for s in meta.get("sheets", [])}
    if tab_name in titles:
        return
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
    ).execute()


def write_header(sheet_id: str, sheet_tab: str, headers: list[str]) -> None:
    """Writes the header row (question/item labels) for a linked sheet tab."""
    ensure_tab_exists(sheet_id, sheet_tab)
    service = _client()
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{sheet_tab}!A1",
        valueInputOption="RAW",
        body={"values": [["제출 시각", "이름", "학번", *headers]]},
    ).execute()


def write_rows(sheet_id: str, sheet_tab: str, rows: list[list[str]]) -> None:
    """Overwrites the sheet tab starting at A1 with the given rows (e.g. a rubric table dump)."""
    ensure_tab_exists(sheet_id, sheet_tab)
    service = _client()
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{sheet_tab}!A1",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()


def append_row(sheet_id: str, sheet_tab: str, row: list[str]) -> None:
    ensure_tab_exists(sheet_id, sheet_tab)
    service = _client()
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f"{sheet_tab}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]},
    ).execute()
