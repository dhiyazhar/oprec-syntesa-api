from googleapiclient.discovery import build

class GSheets:
    def __init__(self, credentials):
        self.service = build('sheets', 'v4', credentials=credentials)
        self.spreadsheet_id = '1cvUhePTsyv0insbnVE3bZQfGaBNYsvOYi04FEtKS0DM'

    def append_data(self, data):
        try:
            request = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='Sheet1!A:G',
                valueInputOption='USER_ENTERED',
                body={'values': data}
            )
            return request.execute()
        except Exception as e:
            print(f"Sheets append error: {e}")
            return None