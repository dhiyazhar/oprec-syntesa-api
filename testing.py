from services.gsheets import GSheets
from services.gdrive import GDrive

CREDENTIALS_PATH = 'env/google-key.json'

def main(): 
    gsheets = GSheets(CREDENTIALS_PATH)
    gdrive = GDrive(CREDENTIALS_PATH)

    cv_file_path = './uploads/cv.pdf'
    transcript_file_path = './uploads/transcript.pdf'

    cv_link = gdrive.upload_file(cv_file_path, 'cv.pdf')
    transcript_link = gdrive.upload_file(transcript_file_path, 'transcript.pdf')

    data = [[
        'Muhammad Nur Azhar Dhiyaulhaq',
        'muhammadnur.23206@mhs.unesa.ac.id',
        '23051204206',
        'Teknik Informatika',
        '2023F',
        cv_link,
        transcript_link
    ]]

    gsheets.write_data(data)


if __name__ == '__main__':
    main()