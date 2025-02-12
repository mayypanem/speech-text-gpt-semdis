import requests
import uuid
import csv

# Define URLs and file names
SEMDIS_UPLOAD_URL = "https://cap.ist.psu.edu/semdis"
SEMDIS_DOWNLOAD_URL = "https://cap.ist.psu.edu/csvdownload"
IDEA_PAIRS_FILENAME = "idea_pairs.csv"
RATINGS_FILENAME = "ratings.csv"

# Start a session to handle cookies
session = requests.Session()

# Step 1: Perform an initial GET request to fetch cookies and CSRF token
response = session.get(SEMDIS_UPLOAD_URL)
csrf_token = session.cookies.get("csrftoken")
if not csrf_token:
    print("CSRF token not found. Exiting.")
    exit()

# Step 2: Generate a unique progress_id
progress_id = uuid.uuid4().hex

# Step 3: Upload the CSV file
with open(IDEA_PAIRS_FILENAME, "rb") as file:
    files = {
        "csrfmiddlewaretoken": (None, csrf_token),
        "csv_file": (IDEA_PAIRS_FILENAME, file, "text/csv"),
        "progress_id": (None, progress_id),
    }
    headers = {
        "Referer": SEMDIS_UPLOAD_URL,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    }
    upload_response = session.post(SEMDIS_UPLOAD_URL, files=files, headers=headers)

if upload_response.status_code == 200:
    print("SemDis API: File uploaded successfully!")
else:
    print(f"SemDis API: Error during file upload: {upload_response.status_code}")
    print("Details:", upload_response.text)
    exit()

# Step 4: Download the results
download_response = session.get(SEMDIS_DOWNLOAD_URL)
if download_response.status_code == 200:
    with open(RATINGS_FILENAME, "wb") as result_file:
        result_file.write(download_response.content)

    # Print first three columns
    try:
        with open(RATINGS_FILENAME, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            # Read header row
            header = next(reader)
            # Print header with spacing
            print(f"{header[0]:<10} {header[1]:<30} {header[2]:<15}")
            print("-" * 60)
            
            # Print first three columns with formatting
            for row in reader:
                print(f"{row[0]:<10} {row[1]:<30} {row[2]:<15}")  

    except Exception as e:
        print(f"Error reading CSV: {e}")
else:
    print(f"SemDis API: Error downloading results: {download_response.status_code}")
    print(download_response.text)
