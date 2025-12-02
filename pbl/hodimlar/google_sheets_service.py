import os
import json
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from datetime import datetime

# Google Sheets API permissions
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# ============================================
# CREDENTIALS FROM ENVIRONMENT VARIABLE
# ============================================
def get_google_credentials():
    """Load Google credentials from environment variable"""
    creds_json = os.environ.get('GOOGLE_CREDENTIALS', '')
    if creds_json:
        try:
            return json.loads(creds_json)
        except json.JSONDecodeError:
            print("Warning: Invalid GOOGLE_CREDENTIALS JSON in environment")
            return None
    return None

GOOGLE_CREDENTIALS = get_google_credentials()

# Default spreadsheet ID from environment variable
DEFAULT_SPREADSHEET_ID = os.environ.get('GOOGLE_SPREADSHEET_ID', '')


class GoogleSheetsService:
    def __init__(self, credentials_json=None):
        self.service = None
        self.credentials = None
        self.credentials_json = credentials_json
        self.initialize_service()

    def initialize_service(self):
        """Initialize Google Sheets API service with credentials from environment"""
        try:
            if not GOOGLE_CREDENTIALS:
                print("❌ GOOGLE_CREDENTIALS not found in environment variables")
                self.service = None
                return

            # Use credentials from environment variable
            creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
            self.credentials = creds
            self.service = build('sheets', 'v4', credentials=creds)
            print("✅ Google Sheets API initialized with environment credentials")

        except Exception as e:
            print(f"❌ Error initializing Google Sheets service: {e}")
            self.service = None

    def create_spreadsheet(self, title="Hodimlar Ish Vaqti"):
        """Create a new Google Spreadsheet"""
        if not self.service:
            return None

        try:
            spreadsheet = {
                'properties': {
                    'title': f"{title} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                },
                'sheets': [{
                    'properties': {
                        'title': 'Bugungi Ma\'lumotlar',
                        'gridProperties': {
                            'rowCount': 1000,
                            'columnCount': 20
                        }
                    }
                }]
            }

            result = self.service.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = result.get('spreadsheetId')

            # Make spreadsheet publicly accessible (anyone with link can view)
            self._make_public(spreadsheet_id)

            print(f"✅ Created spreadsheet: {spreadsheet_id}")
            return {
                'spreadsheet_id': spreadsheet_id,
                'url': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
            }

        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return None

    def _make_public(self, spreadsheet_id):
        """Make spreadsheet accessible to anyone with link"""
        try:
            drive_service = build('drive', 'v3', credentials=self.credentials)

            permission = {
                'type': 'anyone',
                'role': 'writer'
            }

            drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission
            ).execute()

            print(f"✅ Spreadsheet made public")
            return True
        except Exception as e:
            print(f"⚠️ Could not make public: {e}")
            return False

    def write_data_to_sheet(self, spreadsheet_id, data, range_name='Sheet1!A1'):
        """Write data to Google Spreadsheet"""
        if not self.service:
            return False

        try:
            # Clear existing data first
            self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name.split('!')[0] if '!' in range_name else 'Sheet1'
            ).execute()

            # Prepare the data
            values = {
                'values': data
            }

            # Write to spreadsheet
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=values
            ).execute()

            print(f"✅ Updated {result.get('updatedCells')} cells")
            return True

        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return False

    def read_data_from_sheet(self, spreadsheet_id, range_name='Sheet1!A1:G1000'):
        """Read data from Google Spreadsheet"""
        if not self.service:
            return None

        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name).execute()

            values = result.get('values', [])
            print(f"✅ Read {len(values)} rows from spreadsheet")
            return values

        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return None

    def append_data_to_sheet(self, spreadsheet_id, data, range_name='Sheet1!A1:G1'):
        """Append new data to Google Spreadsheet"""
        if not self.service:
            return False

        try:
            values = {
                'values': data
            }

            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=values
            ).execute()

            print(f"✅ Appended {len(data)} rows")
            return True

        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return False

    def format_sheet_headers(self, spreadsheet_id, sheet_id=0):
        """Format the header row with bold text and background color"""
        if not self.service:
            return False

        try:
            requests = [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": 8
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 0.2,
                                    "green": 0.5,
                                    "blue": 0.9
                                },
                                "textFormat": {
                                    "bold": True,
                                    "foregroundColor": {
                                        "red": 1.0,
                                        "green": 1.0,
                                        "blue": 1.0
                                    }
                                }
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat)"
                    }
                },
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": 8
                        }
                    }
                }
            ]

            body = {
                'requests': requests
            }

            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body).execute()

            print("✅ Formatted header row")
            return True

        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return False

    def share_spreadsheet(self, spreadsheet_id, email_address, role='writer'):
        """Share spreadsheet with specific email"""
        if not self.service:
            return False

        try:
            drive_service = build('drive', 'v3', credentials=self.credentials)

            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email_address
            }

            drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission,
                sendNotificationEmail=True
            ).execute()

            print(f"✅ Shared spreadsheet with {email_address}")
            return True

        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return False

    def sync_worklog_data(self, today_worklogs, spreadsheet_id=None, hodimlar=None, month_worklogs=None):
        """Sync worklog data to Google Sheets with monthly report format"""
        try:
            # Use provided spreadsheet_id or default
            if not spreadsheet_id:
                spreadsheet_id = DEFAULT_SPREADSHEET_ID

            if not spreadsheet_id:
                print("❌ No spreadsheet ID provided")
                return None

            # Get all unique dates from worklogs (no limit)
            dates = sorted(set(log.check_in.date() for log in today_worklogs if log.check_in))

            # Uzbek month names
            uzbek_months = {
                1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel",
                5: "May", 6: "Iyun", 7: "Iyul", 8: "Avgust",
                9: "Sentyabr", 10: "Oktyabr", 11: "Noyabr", 12: "Dekabr"
            }

            # Build headers - Row 1: main headers + date headers
            # Row 2: sub-headers (Keldi, Ketdi, ishladi under each date)

            # First row - main column headers + dates
            header_row_1 = [
                "ID", "FIO", "Bo'lim", "Lavozim", "Oylik", "Ish xaqi 1 soat",
                "Jami ishlangan soat", "Ish xaqi"
            ]
            for date in dates:
                month_name = uzbek_months[date.month]
                date_str = f"{date.day} {month_name}"
                header_row_1.extend([date_str, "", ""])  # Date spans 3 columns

            # Second row - empty for first 8 columns, then sub-headers
            header_row_2 = ["", "", "", "", "", "", "", ""]
            for _ in dates:
                header_row_2.extend(["Keldi", "Ketdi", "Ishladi"])

            data = [header_row_1, header_row_2]

            # Group worklogs by hodim
            hodim_worklogs = {}
            for log in today_worklogs:
                hodim_id = log.hodim.id
                if hodim_id not in hodim_worklogs:
                    hodim_worklogs[hodim_id] = {'hodim': log.hodim, 'logs': {}}
                if log.check_in:
                    log_date = log.check_in.date()
                    hodim_worklogs[hodim_id]['logs'][log_date] = log

            # Hourly rate is fixed at 20,000 so'm
            hourly_rate = 20000

            row_num = 0
            for hodim_id, data_dict in hodim_worklogs.items():
                row_num += 1
                hodim = data_dict['hodim']
                logs = data_dict['logs']

                # Calculate total hours worked across all dates
                total_hours = 0
                for date in dates:
                    if date in logs:
                        log = logs[date]
                        hours_worked_str = log.hours_worked if log.hours_worked else "00:00"
                        try:
                            if ':' in str(hours_worked_str):
                                parts = str(hours_worked_str).split(':')
                                total_hours += int(parts[0]) + int(parts[1]) / 60
                        except (ValueError, IndexError):
                            pass

                # Calculate salaries
                earned_salary = hourly_rate * total_hours
                oylik = hourly_rate * 176  # Monthly salary for full month

                row = [
                    str(row_num),  # ID (row number)
                    f"{hodim.first_name} {hodim.last_name}",  # FIO
                    getattr(hodim, 'bolim', '-') or '-',  # Bo'lim
                    hodim.lavozim if hasattr(hodim, 'lavozim') else '-',  # Lavozim
                    f"{oylik:.0f}",  # Oylik
                    f"{hourly_rate}",  # Ish xaqi 1 soat
                    f"{total_hours:.2f}",  # Jami ishlangan soat
                    f"{earned_salary:.0f}",  # Ish xaqi
                ]

                # Add data for each date
                for date in dates:
                    if date in logs:
                        log = logs[date]
                        hours_worked_str = log.hours_worked if log.hours_worked else "00:00"
                        row.extend([
                            log.check_in.strftime('%H:%M') if log.check_in else '',
                            log.check_out.strftime('%H:%M') if log.check_out else '',
                            hours_worked_str
                        ])
                    else:
                        row.extend(['', '', ''])  # Empty for future/no data dates

                data.append(row)

            # Write data to Sheet1
            success = self.write_data_to_sheet(spreadsheet_id, data, "Sheet1!A1")

            if success:
                # Merge date header cells
                self._merge_date_headers(spreadsheet_id, len(dates))
                self.format_sheet_headers(spreadsheet_id)
                # Freeze first 8 columns and first 2 rows
                self._freeze_columns_and_rows(spreadsheet_id, freeze_cols=8, freeze_rows=2)
                return {
                    'spreadsheet_id': spreadsheet_id,
                    'url': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
                    'rows_updated': len(data)
                }
            else:
                return None

        except Exception as e:
            print(f"❌ Error syncing data: {e}")
            return None

    def _merge_date_headers(self, spreadsheet_id, num_dates, sheet_id=0):
        """Merge date header cells (3 columns each) in the first row with different colors"""
        if not self.service:
            return False

        try:
            requests = []

            # Different colors for each day (rotating)
            colors = [
                {"red": 0.2, "green": 0.6, "blue": 0.9},    # Blue
                {"red": 0.3, "green": 0.7, "blue": 0.4},    # Green
                {"red": 0.9, "green": 0.5, "blue": 0.2},    # Orange
                {"red": 0.6, "green": 0.3, "blue": 0.7},    # Purple
                {"red": 0.8, "green": 0.3, "blue": 0.3},    # Red
                {"red": 0.2, "green": 0.7, "blue": 0.7},    # Teal
                {"red": 0.7, "green": 0.6, "blue": 0.2},    # Gold
            ]

            # Start column for dates (after first 8 columns)
            start_col = 8

            for i in range(num_dates):
                col_start = start_col + (i * 3)
                col_end = col_start + 3
                color = colors[i % len(colors)]

                # Merge 3 cells for each date
                requests.append({
                    "mergeCells": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": col_start,
                            "endColumnIndex": col_end
                        },
                        "mergeType": "MERGE_ALL"
                    }
                })

                # Format date header cell with unique color
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": col_start,
                            "endColumnIndex": col_end
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "horizontalAlignment": "CENTER",
                                "backgroundColor": color,
                                "textFormat": {
                                    "bold": True,
                                    "foregroundColor": {
                                        "red": 1.0,
                                        "green": 1.0,
                                        "blue": 1.0
                                    }
                                }
                            }
                        },
                        "fields": "userEnteredFormat(horizontalAlignment,backgroundColor,textFormat)"
                    }
                })

                # Format sub-header row (Keldi, Ketdi, Ishladi) with same color but lighter
                lighter_color = {
                    "red": min(1.0, color["red"] + 0.3),
                    "green": min(1.0, color["green"] + 0.3),
                    "blue": min(1.0, color["blue"] + 0.3)
                }
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": 2,
                            "startColumnIndex": col_start,
                            "endColumnIndex": col_end
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "horizontalAlignment": "CENTER",
                                "backgroundColor": lighter_color,
                                "textFormat": {
                                    "bold": True
                                }
                            }
                        },
                        "fields": "userEnteredFormat(horizontalAlignment,backgroundColor,textFormat)"
                    }
                })

            if requests:
                body = {'requests': requests}
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id, body=body).execute()
                print(f"✅ Merged {num_dates} date headers with colors")

            return True

        except HttpError as error:
            print(f"❌ Error merging cells: {error}")
            return False

    def _freeze_columns_and_rows(self, spreadsheet_id, freeze_cols=8, freeze_rows=2, sheet_id=0):
        """Freeze columns and rows so they stay visible while scrolling"""
        if not self.service:
            return False

        try:
            requests = [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "gridProperties": {
                                "frozenColumnCount": freeze_cols,
                                "frozenRowCount": freeze_rows
                            }
                        },
                        "fields": "gridProperties.frozenColumnCount,gridProperties.frozenRowCount"
                    }
                }
            ]

            body = {'requests': requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body).execute()
            print(f"✅ Froze {freeze_cols} columns and {freeze_rows} rows")

            return True

        except HttpError as error:
            print(f"❌ Error freezing columns/rows: {error}")
            return False
