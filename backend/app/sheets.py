import re

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from app.config import settings

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    # Only files the service account itself creates/opens — needed to share a
    # newly auto-created spreadsheet back to a human (e.g. the admin).
    "https://www.googleapis.com/auth/drive.file",
]

_SHEET_URL_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")


def is_sheets_configured() -> bool:
    return bool(settings.google_service_account_email and settings.google_service_account_private_key)


def extract_spreadsheet_id(raw: str) -> str:
    match = _SHEET_URL_RE.search(raw)
    return match.group(1) if match else raw.strip()


_FORBIDDEN_TAB_CHARS = re.compile(r"[:\\/?*\[\]]")


def _clean_tab_title(title: str, max_len: int = 95) -> str:
    cleaned = _FORBIDDEN_TAB_CHARS.sub(" ", title).strip() or "제목 없음"
    return cleaned[:max_len]


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


def _drive_client():
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
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def create_spreadsheet(title: str, share_with_email: str | None = None) -> str:
    """Creates a new spreadsheet and (optionally) shares it with a human email
    as an editor, since a service-account-created file is otherwise invisible
    in that person's own Drive. Returns the new spreadsheet's id.
    """
    sheets_service = _client()
    result = (
        sheets_service.spreadsheets()
        .create(body={"properties": {"title": title}}, fields="spreadsheetId")
        .execute()
    )
    sheet_id = result["spreadsheetId"]

    if share_with_email:
        drive_service = _drive_client()
        drive_service.permissions().create(
            fileId=sheet_id,
            body={"type": "user", "role": "writer", "emailAddress": share_with_email},
            sendNotificationEmail=False,
        ).execute()

    return sheet_id


def _existing_tab_titles(sheet_id: str) -> set[str]:
    service = _client()
    meta = (
        service.spreadsheets()
        .get(spreadsheetId=sheet_id, fields="sheets.properties.title")
        .execute()
    )
    return {s["properties"]["title"] for s in meta.get("sheets", [])}


def unique_tab_name(sheet_id: str, desired_title: str) -> str:
    """Picks a clean tab name for a first-time link: the plain title if free,
    otherwise "제목 (2)", "제목 (3)", ... — only disambiguated when another
    survey/assignment/roster already used that exact name on this spreadsheet.
    """
    cleaned = _clean_tab_title(desired_title)
    titles = _existing_tab_titles(sheet_id)
    if cleaned not in titles:
        return cleaned
    n = 2
    while f"{cleaned} ({n})" in titles:
        n += 1
    return f"{cleaned} ({n})"


def ensure_tab_exists(sheet_id: str, tab_name: str) -> None:
    """Creates the tab if it doesn't already exist in the target spreadsheet."""
    if tab_name in _existing_tab_titles(sheet_id):
        return
    service = _client()
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
    ).execute()


def get_range_values(sheet_id: str, range_: str) -> list[list[str]]:
    """Reads raw cell values for a range (e.g. "A2:E100" or "Sheet1!A2:E100")."""
    service = _client()
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range=range_)
        .execute()
    )
    return result.get("values", [])


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
