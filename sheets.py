from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

def auth():
    try:
        credentials = service_account.Credentials.from_service_account_file(
            'env/google-key.json',
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        service = build("sheets", "v4", credentials=credentials)
        print("Auth successful")
    except HttpError as error:
        print(f"An error occured: {error}")
        return error

if __name__ == "__main__":
    auth()