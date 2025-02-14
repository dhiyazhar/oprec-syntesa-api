from googleapiclient.discovery import build 
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SHEETS_SERVICE = None
SPREADSHEET_ID = '1cvUhePTsyv0insbnVE3bZQfGaBNYsvOYi04FEtKS0DM'
TOTAL_ROW = None

def google_auth():
    global SHEETS_SERVICE
    try:
        credentials = Credentials.from_service_account_file('./env/google-key.json', scopes=SCOPES) 
        SHEETS_SERVICE = build('sheets', 'v4', credentials=credentials)
        print('[200] auth successful')
    except Exception as error: 
        print (f"an error occurred {error}")
        SERVICE = None
        return {"error": {"error_details": str(error)}}

def get_data():
    global SPREADSHEET_ID
    global TOTAL_ROW
    try:
        result = (
            SHEETS_SERVICE.spreadsheets()
            .values()
            .get(
                spreadsheetId=SPREADSHEET_ID, 
                range='Sheet1'
            )
            .execute()
        )
        rows = result.get('values', [])
        TOTAL_ROW = len(rows)
        print(type(TOTAL_ROW), TOTAL_ROW)
        print(f"{TOTAL_ROW} rows retrieved")
        for row in rows:
            print(row)
    except Exception as error:
        print(f"an error occurred: {error}")    
        return error

def write_data(data):
    global SPREADSHEET_ID
    global TOTAL_ROW
    
    LATEST_WRITE_ROW = TOTAL_ROW+1
    try:
        body = {'values': data}
        result = (
            SHEETS_SERVICE.spreadsheets()
            .values()
            .update(
                spreadsheetId = SPREADSHEET_ID,
                range= f'A{LATEST_WRITE_ROW}:F{LATEST_WRITE_ROW}',
                valueInputOption='USER_ENTERED',
                body=body
            )
            .execute()
        )
        print(f'{result.get('updatedCells')} cells updated')
        return result
    except Exception as error: 
        print(f'an error occurred {error}')
        return error


if __name__ == '__main__': 
    google_auth()
    get_data()
    
    data = [
        ['Muhammad Nur Azhar Dhiyaulhaq', 'muhammadnur.23206@mhs.unesa.ac.id', '23051204206', 'Teknik Informatika', '2023F']
        ]
    write_data(data)





