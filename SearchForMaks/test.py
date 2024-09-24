import py7zr
from os import walk
from os import remove
from os import path



pattern = 'J10807ES'
files_with_pattern = []

# path = r"E:\Python projects\SearchForMaks\tmp" # используйте нужный метод задания ссылки на папку

# for root, dirs, files in walk(path):
#     for file in files:
#         if pattern in file:
#             files_with_pattern.append(file)
        
# print(files_with_pattern)

with py7zr.SevenZipFile(r"E:\Python projects\SearchForMaks\Оригиналы\Delta_5.edz", 'r') as archive:
    """Getting list of all files in folder"""
    all_files = archive.getnames()

    for file in all_files:
        if pattern in file:
            folder_with_nessessary_files=r"E:\Python projects\SearchForMaks\tmp"
            archive.extractall(folder_with_nessessary_files)
            
            for root, dirs, files in walk(folder_with_nessessary_files):
                for file in files:
                    print(f"{root}\\{file}")
                    if pattern in file:
                        files_with_pattern.append(file)
            
            for root, dirs, files in walk(folder_with_nessessary_files):
                for file in files:
                    if file not in ".".join(files_with_pattern) and not file.endswith(".pdf") and not (file.endswith(".jpg") or file.endswith(".JPG")):
                        remove(f"{root}\\{file}")
            
            break
