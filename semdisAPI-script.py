import requests
import uuid
import csv

# Define URLs and file path
upload_url = "https://cap.ist.psu.edu/semdis"
download_url = "https://cap.ist.psu.edu/csvdownload"
csv_file_path = "ideas_pairs.csv"
processed_csv_filename = "processed_results.csv"

# Start a session to handle cookies
session = requests.Session()

# Step 1: Perform an initial GET request to fetch cookies and CSRF token
response = session.get(upload_url)
csrf_token = session.cookies.get("csrftoken")
if not csrf_token:
    print("CSRF token not found. Exiting.")
    exit()

# Step 2: Generate a unique progress_id
progress_id = uuid.uuid4().hex

# Step 3: Upload the CSV file
with open(csv_file_path, "rb") as file:
    files = {
        "csrfmiddlewaretoken": (None, csrf_token),
        "csv_file": (csv_file_path, file, "text/csv"),
        "progress_id": (None, progress_id),
    }
    headers = {
        "Referer": upload_url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    }
    upload_response = session.post(upload_url, files=files, headers=headers)

if upload_response.status_code == 200:
    print("✅ File uploaded successfully!")
else:
    print(f"❌ Error during file upload: {upload_response.status_code}")
    print("Details:", upload_response.text)
    exit()

# Step 4: Download the results
download_response = session.get(download_url)
if download_response.status_code == 200:
    with open(processed_csv_filename, "wb") as result_file:
        result_file.write(download_response.content)

    # ✅ Print first three columns (without Pandas)
    try:
        with open(processed_csv_filename, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            header = next(reader)  # Read the header row
            print("\n📊 Processed Results:")
            print(f"{header[0]:<10} {header[1]:<30} {header[2]:<15}")  # Print header with spacing
            print("-" * 60)
            
            for row in reader:
                print(f"{row[0]:<10} {row[1]:<30} {row[2]:<15}")  # Print first three columns with formatting

    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
else:
    print(f"❌ Error downloading results: {download_response.status_code}")
    print(download_response.text)
