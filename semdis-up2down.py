from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import time
from selenium.webdriver.chrome.options import Options

# Set Chrome Options
download_dir = r"C:\Users\majas\Documents\GitHub\speech-text-gpt-semdis\downloads"
chrome_options = Options()
prefs = {
    "download.default_directory": download_dir,  # Set default download directory
    "download.prompt_for_download": False,       # Disable download prompt
    "download.directory_upgrade": True,          # Automatically overwrite existing files
    "safebrowsing.enabled": True                 # Enable safe browsing
}
chrome_options.add_experimental_option("prefs", prefs)

# Initialize the WebDriver with options
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def wait_for_new_file(directory, timeout=30):
    """
    Waits for a new file to appear in the specified directory.
    
    Args:
        directory (str): Path to the directory to monitor.
        timeout (int): Maximum time to wait in seconds.
    
    Returns:
        str: Path to the new file, or None if no new file is found.
    """
    # Get the initial set of files in the directory
    before = set(os.listdir(directory))

    # Monitor the directory for a new file
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(0.5)  # Check every second
        after = set(os.listdir(directory))
        new_files = {f for f in after - before if f.endswith('.csv')}
        if new_files:
            # Return the first new file found
            return os.path.join(directory, new_files.pop())

    # Timeout: No new file detected
    return None


try:
    # Navigate to the Website
    driver.get("http://semdis.wlu.psu.edu/")
    wait = WebDriverWait(driver, 10)

    print("Opened website!\n")

    # Go to Upload Your File Section
    upload_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '#shiny-tab-third_app')]"))
    )
    upload_button.click()

    print("Gone to Upload Your File section!\n")

    # Select Clean Type
    dropdown_element_clean = wait.until(
        EC.presence_of_element_located((By.ID, "clean_type"))
    )
    dropdown_clean = Select(dropdown_element_clean)
    dropdown_clean.select_by_value("Remove Filler and Clean")

    # Select Space Type
    dropdown_element_space = wait.until(
        EC.presence_of_element_located((By.ID, "space_type"))
    )
    dropdown_space = Select(dropdown_element_space)
    dropdown_space.select_by_value("cbowukwacsubtitle")

    # Select Model Type
    dropdown_element_model = wait.until(
        EC.presence_of_element_located((By.ID, "model_type"))
    )
    dropdown_model = Select(dropdown_element_model)
    dropdown_model.select_by_value("Multiplicative")

    print("Clean, space and model type selected!\n")

    #Locate and Record Link from Download Button
    download_button = wait.until(
        EC.element_to_be_clickable((By.ID, "downloadData3"))
    )
    initial_href = download_button.get_attribute("href")

    # Upload CSV File
    file_input = wait.until(
        EC.presence_of_element_located((By.ID, "file"))
    )
    file_path = r"C:\Users\majas\Documents\GitHub\speech-text-gpt-semdis\semdis-test-2.csv"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    file_input.send_keys(file_path)

    print("File uploaded!\n")

    # Wait for File Processing and Download
    wait.until(
        lambda driver: download_button.get_attribute("href") != initial_href
    )
    download_button.click()
    new_file = wait_for_new_file(download_dir, timeout=5)

    if new_file:
        print(f"File downloaded successfully: {new_file}")
    else:
        print("Download timed out.")

    print("Done!\n")
finally:
    driver.quit()