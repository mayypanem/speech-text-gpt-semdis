import os
import pandas as pd

# Define the main data folder
data_folder = "data"

# Ensure the data folder exists
if not os.path.exists(data_folder):
    print(f"Folder '{data_folder}' not found.")
    exit()

# Iterate through all first-level folders inside 'data'
for folder_name in os.listdir(data_folder):
    folder_path = os.path.join(data_folder, folder_name)
    
    # Check if it's a directory
    if os.path.isdir(folder_path):
        csv_path = os.path.join(folder_path, "idea_pairs.csv")
        
        # Check if the file 'idea_pairs.csv' exists
        if os.path.exists(csv_path):
            # Define the new file path
            new_csv_path = os.path.join(folder_path, "idea_comparison.csv")
            
            # Read the original CSV file
            df = pd.read_csv(csv_path)
            
            # Create a new DataFrame with required columns
            if df.shape[1] >= 2:  # Ensure at least two columns exist
                new_df = pd.DataFrame()
                new_df["manually extracted ideas"] = ""
                new_df["automatically extracted ideas"] = df.iloc[:, 1]
                new_df["codes"] = ""
                
                # Save the modified DataFrame as 'idea_comparison.csv'
                new_df.to_csv(new_csv_path, index=False)
                print(f"Processed and saved: {new_csv_path}")
            else:
                print(f"Skipping '{csv_path}': Not enough columns (needs at least 2).")
                continue

print("Processing complete.")
