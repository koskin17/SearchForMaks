""""Extracting the necessary files from"""

import py7zr
from zipfile import ZipFile
from os import walk
from os import remove
from os import mkdir
from os import path


text_for_search = 'J10807ES' #necessary text
files_with_pattern = []

with py7zr.SevenZipFile(r"E:\Python projects\SearchForMaks\Оригиналы\Delta_5.edz", 'r') as archive:
    
    """Getting list of all files in folder"""
    all_files = archive.getnames()

    """Making list of files with necessary text"""
    for file in all_files:
        if text_for_search in file or file.endswith('.pdf') or file.endswith('.jpg') or file.endswith('.JPG'):
            files_with_pattern.append(file)
            
"""Метод разархивирования целевых файлов"""
with py7zr.SevenZipFile(r"E:\Python projects\SearchForMaks\Оригиналы\Delta_5.edz", 'r') as archive:
    archive.extract(path='./tmp', targets=files_with_pattern)

file_for_path = files_with_pattern[0]    
print(file_for_path)
    
"""Метод с разарзивированием всего архива и удалением ненужных файлов"""
            # print(files_with_pattern)
            # archive.extract(targets=files_with_pattern)
            # mkdir("../tmp")
            # folder_with_necessary_files = "../tmp"
            # archive.extractall(folder_with_necessary_files)
            
            # for root, dirs, files in walk(folder_with_necessary_files):
            #     for file in files:
            #         if text_for_search in file:
            #             files_with_pattern.append(file)
            
            # """Deleting unnecessary files"""
            # for root, dirs, files in walk(folder_with_necessary_files):
            #     for file in files:
            #         if file not in ".".join(files_with_pattern) and not file.endswith(".pdf") and not (file.endswith(".jpg") or file.endswith(".JPG")):
            #             remove(f"{root}\\{file}")
            #             """As a result we get all folders from original archive with necessary files"""                
            
            # break
