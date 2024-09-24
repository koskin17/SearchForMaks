import py7zr
from os import walk
from os import remove


pattern = 'J10807ES' #nessesary text
files_with_pattern = []

with py7zr.SevenZipFile(r"E:\Python projects\SearchForMaks\Оригиналы\Delta_5.edz", 'r') as archive:
    """Getting list of all files in folder"""
    all_files = archive.getnames()

    """Making list of files with nessesary text"""
    for file in all_files:
        if pattern in file:
            folder_with_nessessary_files=r"E:\Python projects\SearchForMaks\tmp"
            archive.extractall(folder_with_nessessary_files)
            
            for root, dirs, files in walk(folder_with_nessessary_files):
                for file in files:
                    print(f"{root}\\{file}")
                    if pattern in file:
                        files_with_pattern.append(file)
            
            """Deleting unnessesary files"""
            for root, dirs, files in walk(folder_with_nessessary_files):
                for file in files:
                    if file not in ".".join(files_with_pattern) and not file.endswith(".pdf") and not (file.endswith(".jpg") or file.endswith(".JPG")):
                        remove(f"{root}\\{file}")
            
            """As a result we get all folders from original archive with nessesary files"""
            break
