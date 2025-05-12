import py7zr
from os import path

def unzip_target_arc(edz_path, search_text):
    """Function for unarchive necesssary files"""
    
    files_with_searching_model = []
    
    with py7zr.SevenZipFile(edz_path) as archive:
        all_files = archive.getnames()
        
        for file in all_files:
            if search_text in file or file.endswith('.pdf') or file.endswith('.jpg') or file.endswith('.JPG'):
                files_with_searching_model.append(file)
            
        archive.extract(targets=files_with_searching_model)
                    
    return path.realpath('item/')
    