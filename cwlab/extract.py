import os
import subprocess
import re
import shutil
import tempfile
import fnmatch
import atexit

def find_files(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                yield os.path.join(root, basename)

def extract_info(file_path):
    match = re.search(r'reproduced_(.+?)--.+?--crash-\w+-([\d\-]+)', os.path.basename(file_path))
    return match.groups() if match else (None, None)

def parse_dockerfile_for_repo_url(repo_name, projects_directory):
    dockerfile_path = os.path.join(projects_directory, repo_name, "Dockerfile")
    last_url = None
    try:
        with open(dockerfile_path, 'r') as file:
            for line in file:
                if 'git clone' in line:
                    match = re.search(r'https://(github|gitlab|android)\.[^\s]+', line)
                    if match:
                        last_url = match.group(0)
    except FileNotFoundError:
        print(f"Dockerfile not found for repository: {repo_name}")
    
    return last_url

def copy_repo_to_target_project(repo_name, projects_directory, target_project_directory):
    source_dir = os.path.join(projects_directory, repo_name)
    dest_dir = os.path.join(target_project_directory, repo_name)
    if os.path.exists(source_dir) and not os.path.exists(dest_dir):
        shutil.copytree(source_dir, dest_dir)
    elif not os.path.exists(source_dir):
        print(f"Source directory not found: {source_dir}")

def clone_repo(repo_url, temp_dir, repo_name):
    repo_path = os.path.join(temp_dir, repo_name)
    if not os.path.exists(repo_path):
        try:
            subprocess.check_call(['git', 'clone', repo_url, repo_path])
        except subprocess.CalledProcessError:
            print(f"Failed to clone repository: {repo_url}")
            return None
    return repo_path

def get_commit_before_date(date, repo_path):
    try:
        return subprocess.check_output(
            ['git', 'log', '--before={}'.format(date), '-1', '--format=%H'],
            cwd=repo_path
        ).decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        return "Error: " + str(e.output.decode('utf-8'))

def cleanup_repos(temp_dir):
    shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    root_directory = "./crash/asan"
    projects_directory = "./projects"

    if not os.path.exists(root_directory) or not os.path.exists(projects_directory):
        print("Required directories not found. Exiting.")
        return

    pattern = "reproduced_*"
    temp_dir = tempfile.mkdtemp()
    atexit.register(cleanup_repos, temp_dir)

    target_project_directory = "./target_projects"
    os.makedirs(target_project_directory, exist_ok=True)

    for file_path in find_files(root_directory, pattern):
        repo_name, date = extract_info(file_path)
        
        if repo_name and date:
            copy_repo_to_target_project(repo_name, projects_directory, target_project_directory)
            repo_url = parse_dockerfile_for_repo_url(repo_name, projects_directory)

            if repo_url:
                repo_path = clone_repo(repo_url, temp_dir, repo_name)

                if repo_path:
                    commit = get_commit_before_date(date, repo_path)
                    result_line = f"{file_path},{repo_name},{date},{commit}\n"

                    with open(os.path.join(target_project_directory, repo_name, "result.txt"), "a") as file:
                        file.write(result_line)
                        print(result_line, end='')
            else:
                print(f"GitHub URL not found for {repo_name}")
        else:
            print(f"Info not found in file path: {file_path}")

if __name__ == "__main__":
    main()
