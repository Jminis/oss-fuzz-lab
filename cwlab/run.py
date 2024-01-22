import sys
import os
import shutil
import re
import difflib
import subprocess
from datetime import datetime

SESSION_TIME = 10

def color_diff(diff):
    for line in diff:
        if line.startswith('+'):
            yield "\033[92m" + line + "\033[0m"  # Green for added lines
        elif line.startswith('-'):
            yield "\033[91m" + line + "\033[0m"  # Red for removed lines
        else:
            yield line


def parse_git_clone_command(line):
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


def run_fuzzer_and_save_results(project_name, fuzzer_name, option):
    # Run Fuzzer && Calc run time
    with open('runtime_log.txt', 'w') as file:
        start_time = datetime.now()
        subprocess.run(["python", "infra/helper.py", "run_fuzzer", project_name, fuzzer_name, option],stdout=file,timeout=60)
        end_time = datetime.now()

    execution_time = end_time - start_time

    # Check result folder
    result_folder = "./cwlab/result"
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)

    # Copy corpus dir to result
    corpus_folder = f"build/out/{project_name}/{fuzzer_name}_corpus"
    current_time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_folder_name = f"{project_name}_{fuzzer_name}_{current_time_str}"
    new_corpus_folder_path = os.path.join(result_folder, new_folder_name, f"{fuzzer_name}_corpus")
    shutil.copytree(corpus_folder, new_corpus_folder_path)

    # Count corpus file
    file_count = len(os.listdir(corpus_folder))

    # Save Result Description
    description_file = os.path.join(result_folder,new_folder_name, "description.txt")
    with open(description_file, "w") as file:
        file.write(f"Execution Time: {execution_time}\n")
        file.write(f"Number of Files: {file_count}\n")

    shutil.copy('runtime_log.txt',f"{result_folder}/{new_folder_name}")


def process_dockerfile(project_name, commit_hash):
    dockerfile_path = f"./target_projects/{project_name}/Dockerfile"
    dockerfile_backup_path = f"{dockerfile_path}_bak"

    if not os.path.exists(dockerfile_backup_path):
        shutil.copy(dockerfile_path, dockerfile_backup_path)

    with open(dockerfile_backup_path, 'r') as file:
        original_dockerfile_contents = file.readlines()

    new_dockerfile_contents = []
    git_clone_regex = re.compile(r"RUN git clone .+?")
    last_git_clone_index = None
    for i, line in enumerate(original_dockerfile_contents):
        if git_clone_regex.search(line):
            last_git_clone_index = i

    dockerfile_changed = False
    if last_git_clone_index is not None:
        for i, line in enumerate(original_dockerfile_contents):
            if i == last_git_clone_index:
                line = re.sub(r"--depth 1", "", line)  # Remove --depth 1 if present
                repo_name = parse_git_clone_command(line)
                if repo_name:
                    new_dockerfile_contents.append(line)
                    new_dockerfile_contents.append(f"\nWORKDIR {repo_name}")
                    new_dockerfile_contents.append(f"\nRUN git checkout {commit_hash}")
                    new_dockerfile_contents.append("\nWORKDIR ../\n")
                    dockerfile_changed = True
            else:
                new_dockerfile_contents.append(line)

    with open(dockerfile_path, 'w') as file:
        file.writelines(new_dockerfile_contents)
    diff = difflib.unified_diff(original_dockerfile_contents, new_dockerfile_contents,
                                fromfile='original', tofile='modified', lineterm='')
    colored_diff = color_diff(diff)
    print('\n'.join(list(colored_diff)))

    return dockerfile_changed


def read_result_file(project_name):
    result_file_path = f"./target_projects/{project_name}/result.txt"

    if not os.path.exists(result_file_path):
        print(f"Result file for project {project_name} not found.")
        sys.exit(1)

    with open(result_file_path, 'r') as file:
        lines = file.readlines()

    for idx, line in enumerate(lines):
        print(f"{idx+1}: {line.strip()}")

    return lines


def handle_user_input(lines):
    selected_number = int(input("Enter the number of the entry you want to use: "))

    if selected_number < 1 or selected_number > len(lines):
        print("Invalid selection.")
        sys.exit(1)

    return lines[selected_number - 1].strip()


def display_file_content(file_path):
    try:
        with open(file_path, 'r') as f:
            print(f"Content of {file_path}:")
            print(f.read())
    except FileNotFoundError:
        print(f"File {file_path} not found.")


def update_dockerfile_run_fuzzer(project_name, file_path):
    try:
        if input("Do you want to execute 'python infra/helper.py build_fuzzers {}'? (y/n): ".format(project_name)).lower() == 'y':
            fuzzer_name = file_path.split('/')[-1].split('--')[1]
            reproduce_file_name = "".join(file_path.split('/')[5:6])
            reproduce_file_name = re.sub(r"reproduced_","",reproduce_file_name)
            reproduce_file_path = "./cwlab/crash/data/" + reproduce_file_name

            # Build Fuzzer && Set corpus dir command
            oss_fuzz_dir = "../"  # Replace with the actual path to your 'oss-fuzz' directory
            os.chdir(oss_fuzz_dir)
            subprocess.run(["cp", "-r", f"./cwlab/target_projects/{project_name}", "./projects/"])
            subprocess.run(["python", "infra/helper.py", "build_fuzzers", project_name])
            cmd = f"rm -r build/out/{project_name}/{fuzzer_name}_corpus ; "
            cmd += f"unzip build/out/{project_name}/{fuzzer_name}_seed_corpus.zip -d build/out/{project_name}/{fuzzer_name}_corpus || "
            cmd += f"mkdir build/out/{project_name}/{fuzzer_name}_corpus"
            print(cmd)
            os.system(cmd)

            # Run Fuzzer command
            option = f"-max_total_time={SESSION_TIME} {fuzzer_name}_corpus/"
            if sys.argv[2] == "run_fuzzer":
                #subprocess.run(["python", "infra/helper.py", "run_fuzzer", project_name, fuzzer_name, option])
                run_fuzzer_and_save_results(project_name, fuzzer_name, option)
            elif sys.argv[2] == "reproduce":
                subprocess.run(["python", "infra/helper.py", "reproduce", project_name, fuzzer_name, reproduce_file_path])

    except Exception as e:
        print(f"Run Fuzzer Error: {e}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python run.py [project_name] [run_fuzzer/reproduce]")
        sys.exit(1)

    project_name = sys.argv[1]
    lines = read_result_file(project_name)

    selected_line = handle_user_input(lines)
    file_path = selected_line.split(',')[0]
    display_file_content(file_path)

    dockerfile_changed = process_dockerfile(project_name, selected_line.split(',')[-1])

    if dockerfile_changed:
        print("Dockerfile updated successfully.")
        update_dockerfile_run_fuzzer(project_name, file_path)
    else:
        print("No changes were made to the Dockerfile.")


if __name__ == "__main__":
    main()

