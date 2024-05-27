import os
import shutil

def move_txt_files(source_dir):
    raw_files_dir = os.path.join(source_dir, 'raw_files')
    if not os.path.exists(raw_files_dir):
        print(f"Error: '{raw_files_dir}' does not exist.")
        return
    
    for filename in os.listdir(raw_files_dir):
        if filename.endswith(".txt"):
            base_name = os.path.splitext(filename)[0]
            suffix = base_name[-3:]  # Get the last three characters
            
            if suffix == "ECG":
                target_folder = os.path.join(source_dir, 'polar_ECG')
            elif suffix == "_RR" or suffix == " RR":
                target_folder = os.path.join(source_dir, 'polar_RR')
            elif suffix == "PPG":
                target_folder = os.path.join(source_dir, 'polar_PPG')
            else:
                target_folder = os.path.join(source_dir, 'polar_HR')
            
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)  # Create the target folder if it doesn't exist
            
            source_path = os.path.join(raw_files_dir, filename)
            target_path = os.path.join(target_folder, filename)
            
            try:
                shutil.move(source_path, target_path)
                print(f"Moved '{filename}' to '{target_folder}'.")
            except Exception as e:
                print(f"Error moving '{filename}': {e}")

# Usage example:
source_directory = 'polar_data'
move_txt_files(source_directory)
