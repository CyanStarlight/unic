#!/usr/bin/env python3

"""
    UNIC Git Repository Manager
    ---------------------------
    This script is designed to help manage the UNIC Git repository by adding new course folders and converting existing folders to submodules to save space on client machines.



Please someone refactor my code and format it properly, my linter died a long time ago and nothing can save it now :(

Contributors so far:
- Maksym Dulich, lesoup-mxd


No idea as to what copyright this is. All rights reserved, I guess.
"""


"""
 Please someone test it on Win, cuz it tas those weird slashes nobody asked for
"""


import os
import subprocess
from urllib.parse import urlparse

def is_git_repo(path):
    return os.path.exists(os.path.join(path, '.git'))

def is_submodule(path):
    return os.path.exists(os.path.join(path, '.gitmodules'))

#Not sure that this will work correctly, someone gotta check it once we have the folder outside of our root TODO
def convert_to_submodule(repo_path, folder_name):
    full_path = os.path.join(repo_path, folder_name)
    
    if not is_git_repo(full_path):
        print(f"{full_path} is not a git repository")
        return
    
    if is_submodule(full_path):
        print(f"{full_path} is already a submodule")
        return
    
    subprocess.run(['git', 'submodule', 'add', '.', f'{repo_path}/{folder_name}'], cwd=repo_path)
    
    with open('.gitmodules', 'r') as f:
        lines = f.readlines()
    
    with open('.gitmodules', 'w') as f:
        for line in lines:
            if folder_name in line:
                f.write(line.replace('. ', f'{folder_name}/ '))
    
    subprocess.run(['git', 'add', '.gitmodules'], cwd=repo_path)
    subprocess.run(['git', 'commit', '-m', f"Convert {folder_name} to submodule"], cwd=repo_path)


#Messy tbh, needs a better recursive search
def search_repo(repo_path, query):
    for item in os.listdir(repo_path):
        full_path = os.path.join(repo_path, item)
        if os.path.isdir(full_path):
            if query.lower() in item.lower():
                print(f"Found matching folder: {item}")
                return full_path
    return None

#Surprisingly easy to do
def parse_id(url):
    _id_uncut = url.split('?')[1]
    _id = _id_uncut.split('=')[1]
    _course_code = url.split(' ')[0]
    return _course_code, _id

def add_folder_from_url(repo_path, url):
    course_code, course_id = parse_id(url)
    print(f"Course code: {course_code}")
    _path_course = os.path.join(repo_path, course_code)
    if not os.path.exists(_path_course):
        os.makedirs(_path_course)
        print(f"Created new folder: {course_code}")
    if not os.path.exists(os.path.join(_path_course, course_id)):
        os.makedirs(os.path.join(_path_course, course_id))
        print(f"Created new folder: {course_id}")
    
    full_path = _path_course
    #we theoretically have to move the folder outside of the root and then add it as a submodule, TODO

    if not is_git_repo(full_path):
        print(f"{full_path} is not a git repository")
        return
    
    subprocess.run(['git', 'add', course_code], cwd=repo_path)
    subprocess.run(['git', 'commit', '-m', f"Add course folder: {course_code}"], cwd=repo_path)



def main():
    repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print(f"Current repository path: {repo_path}")
    
    while True:
        action = input("Choose an action:\n1. Search for a folder\n2. Add a new folder from URL\n3. Exit\n").strip()
        
        if action == '1':
            query = input("Enter search query: ").strip()
            result = search_repo(repo_path, query)
            if result:
                choice = input(f"Found '{result}'. Do you want to convert it to a submodule? (y/n): ").strip().lower()
                if choice == 'y':
                    convert_to_submodule(os.path.dirname(result), os.path.basename(result))
            else:
                print("Folder not found.")
        
        elif action == '2':
            url = input("Enter URL (e.g., MATH-101 https://portal.unic.ac.cy/courses/355025): ").strip()
            course_code, _ = parse_id(url)

            add_folder_from_url(repo_path, url)
        
        elif action == '3':
            break
        
        else:
            print("Invalid choice. Please choose a valid option.")

if __name__ == "__main__":
    main()
