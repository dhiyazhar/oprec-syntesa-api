import logging
from typing import List, Optional, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class GSheetsException(Exception):
    pass

class GSheets:
    def __init__(self, credentials: Credentials, spreadsheet_id: str = '1cvUhePTsyv0insbnVE3bZQfGaBNYsvOYi04FEtKS0DM'):
        self.service = build('sheets', 'v4', credentials=credentials)
        self.spreadsheet_id = spreadsheet_id
        logger.info('GSheets service initiated.')
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def append_data(self, values: List[List[Any]], range_name: str = 'Sheet1A:G', insert_data_option: str = 'INSERT_ROWS') -> bool:
        try:
            logger.info(f"Appending {len(values)} rows to sheets")
            
            body = {
                'values': values, 
                'majorDimension': 'ROWS'
            }
            
            result = await run_in_threadpool(
                lambda: self.service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    insertDataOption=insert_data_option,
                    body=body
                ).execute()
            )
            
            updated_rows = result.get('updates', {}).get('updatedRows', 0)
            logger.info(f"Succesfully appended {updated_rows} rows")
            
            return True
        
        except HttpError as e:
            error_msg = f"Google Sheets API error: {str(e)}"
            logger.error(error_msg)
            raise GSheetsException(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during data append: {str(e)}"
            logger.error(error_msg)
            raise GSheetsException(error_msg)
