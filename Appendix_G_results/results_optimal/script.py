import os
import glob

def rename_files_recursively(path):
    for foldername, subfolders, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith('_'):
                new_filename = filename.rstrip('_') + '.json'
                old_path = os.path.join(foldername, filename)
                new_path = os.path.join(foldername, new_filename)
                os.rename(old_path, new_path)
                print(f"Renamed: {old_path} -> {new_path}")
        
        for subfolder in subfolders:
            rename_files_recursively(subfolder)

if __name__ == "__main__":
    root_path = '.'  # Replace this with the root directory you want to search
    rename_files_recursively(root_path)

