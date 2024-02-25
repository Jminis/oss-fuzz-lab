import os
import subprocess
import re
import shutil
import tempfile
import fnmatch
import atexit
import difflib

def color_diff(diff):
    for line in diff:
        if line.startswith('+'):
            yield "\033[92m" + line + "\033[0m"  # Green for added lines
        elif line.startswith('-'):
            yield "\033[91m" + line + "\033[0m"  # Red for removed lines
        else:
            yield line


def find_files(directory, pattern):
    matched_files = []  # 조건에 맞는 파일을 저장할 리스트
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                matched_files.append(os.path.join(root, basename))
    
    matched_files.sort()
    
    for file_path in matched_files:
        yield file_path

def extract_info(file_path):
    match = re.search(r'reproduced_(.+?)--(.+?)--crash-\w+-([\d\-:]+)', os.path.basename(file_path))
    return match.groups() if match else (None, None, None)

def cleanup_repos(temp_dir):
    shutil.rmtree(temp_dir, ignore_errors=True)


def copy_repo(source,dest):
    if os.path.exists(source) and not os.path.exists(dest):
        shutil.copytree(source, dest)
    elif not os.path.exists(source):
        print(f"Source directory not found: {source}")


def parse_repo_url(source, repo_name):
    dockerfile_path = os.path.join(source, "Dockerfile")
    last_url = None
    
    try:
        with open(dockerfile_path, 'r') as file:
            for idx, line in enumerate(file):
                if 'git clone' in line and repo_name.lower() in line.lower():
                    match = re.search(r'https://(git|github|gitlab|android)\.[^\s]+', line)
                    if match:
                        last_url = match.group(0)
                        break

    except FileNotFoundError:
        print(f"Dockerfile not found for repository: {source}")
    return last_url, idx


def clone_repo(repo_url, temp_dir, repo_name):
    repo_path = os.path.join(temp_dir, repo_name)
    print(repo_url,temp_dir,repo_name)
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
    
def parse_repo_dir(line):
    parts = line.split()
    if "--recursive" in parts:
        parts.remove("--recursive")
    if len(parts) > 2 and parts[0] == 'RUN' and parts[1] == 'git' and parts[2] == 'clone':
        if len(parts) == 5:
            # Format: git clone <url> <folder>
            return parts[4]
        elif len(parts) == 4:
            # Format: git clone <url>
            pattern = r"/([^/]+?)(\.git)?$"
            data = re.search(pattern, parts[3])
            if data:
                found = data.group(1)
            return found
    return None

def process_dockerfile(dest,repo_name, commit):

    dockerfile_path = os.path.join(dest, "Dockerfile")
    dockerfile_backup_path = f"{dockerfile_path}_bak"

    if not os.path.exists(dockerfile_backup_path):
        shutil.copy(dockerfile_path, dockerfile_backup_path)

    with open(dockerfile_backup_path, 'r') as file:
        origin_data = file.readlines()

    new_data = origin_data.copy()
    git_clone_regex = re.compile(r"RUN git clone .+?")
    target_url, target_idx = parse_repo_url(dest,repo_name)

    dockerfile_changed = False
    if target_url is not None:
        
        for i, line in enumerate(origin_data):
            if i == target_idx:
                line = re.sub(r"--depth=?\s*1", "", line)
                new_data[i] = line
                repo_dir = parse_repo_dir(line)
                if repo_dir:
                    new_data.insert(i + 1, f"\nWORKDIR {repo_dir}\n")
                    new_data.insert(i + 2, f"RUN git checkout {commit}\n")
                    new_data.insert(i + 3, "WORKDIR ../\n")
                    dockerfile_changed = True
                    break

    with open(dockerfile_path, 'w') as file:
        file.writelines(new_data)

    diff = difflib.unified_diff(origin_data, new_data, fromfile='original', tofile='modified', lineterm='')
    colored_diff = color_diff(diff)
    print('\n'.join(list(colored_diff)))

    return dockerfile_changed


def main():
    asan_directory = "./crash/asan"
    data_directory = "./crash/data"
    projects_directory = "./projects"

    if not os.path.exists(asan_directory) or not os.path.exists(projects_directory):
        print("Required directories not found. Exiting.")
        return

    pattern = "reproduced_*"
    temp_dir = tempfile.mkdtemp()
    atexit.register(cleanup_repos, temp_dir)

    factory = "./factory"
    os.makedirs(factory, exist_ok=True)

    count = 0
    for file_path in find_files(asan_directory, pattern):
        count += 1
        repo_name, fuzzer_name, date = extract_info(file_path)
        
        if repo_name and fuzzer_name:
            container = f"{count:03}--{repo_name}--{fuzzer_name}"
            source =  os.path.join(projects_directory, repo_name)
            dest = os.path.join(factory, container)
            crash = os.path.basename(file_path).replace("reproduced_", "")
            copy_repo(source, dest)     # Copy project folder
            shutil.copy(file_path,dest) # Copy asan log
            shutil.copy(os.path.join(data_directory,crash),dest) # Copy crash data

            repo_url, idx = parse_repo_url(source, repo_name)
            if repo_url:
                repo_path = clone_repo(repo_url, temp_dir, repo_name)
                if repo_path:
                    commit = get_commit_before_date(date, repo_path)
                    open(os.path.join(dest,commit), 'w').close()
                    if not process_dockerfile(dest,repo_name, commit):
                        os.rename(dest,f"{dest}--HELP_dockerfile")    
                else:
                    os.rename(dest,f"{dest}--HELP_repo_path")
            else:
                os.rename(dest,f"{dest}--HELP_repo_url")

if __name__ == "__main__":
    main()
