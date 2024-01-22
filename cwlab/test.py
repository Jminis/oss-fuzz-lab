import sys
import os
import shutil
import re
import difflib
import subprocess
import time
import glob
import zipfile
from datetime import datetime

SESSION_TIME = 10
worker_id = 0

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


def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def run_fuzzer_and_save_results(project_name, fuzzer_name, option, no_seed_corpus):
    # Initialize variables
    global workder_id
    timeout_flag = False
    crash_files_copied = False

    # Base result path
    base_result_folder = "./cwlab/result"
    create_directory(base_result_folder)
    
    base_timeout_folder = "./cwlab/result/timeout"
    create_directory(base_timeout_folder)

    current_time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_folder_name = f"{project_name}_{fuzzer_name}_{current_time_str}"
    temp_folder_path = os.path.join(base_result_folder, temp_folder_name)
    create_directory(temp_folder_path)
    runtime_log_path = os.path.join(temp_folder_path, f'runtime_log.txt')

    # Run fuzzer and Save log data
    timeout_flag = False
    start_time = datetime.now()
    try:
        with open(runtime_log_path, 'w') as file:
            subprocess.run(["python3", "infra/helper.py", "run_fuzzer", project_name, fuzzer_name, option], stdout=file, timeout=SESSION_TIME)
    except subprocess.TimeoutExpired:
        timeout_flag = True
    execution_time = datetime.now() - start_time

    # Handle timeout
    final_result_folder = os.path.join(base_timeout_folder if timeout_flag else base_result_folder, temp_folder_name)
    if timeout_flag:
        shutil.move(temp_folder_path, final_result_folder)

    # Count corpus file
    corpus_path = f"build/out/{project_name}/{fuzzer_name}_corpus"
    file_count = len(os.listdir(corpus_path)) if os.path.exists(corpus_path) else 0
    try:
        shutil.move(corpus_path, final_result_folder)
    except Exception as e:
        pass
    
    # Copy crash files if any
    crash_file_pattern = f"build/out/{project_name}/crash-*"
    for crash_file in glob.glob(crash_file_pattern):
        shutil.move(crash_file, final_result_folder)
        crash_files_copied = True

    # Save Result Description
    description_file = os.path.join(final_result_folder, "description.txt")
    with open(description_file, "w") as file:
        file.write(f"Execution Time: {execution_time}\n")
        file.write(f"Number of Files: {file_count}\n")
        if no_seed_corpus:
            file.write("No Seed Corpus Available\n")
        if crash_files_copied:
            file.write("Crash Files Copied\n")

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
    #for idx, line in enumerate(lines):
    #    print(f"{idx+1}: {line.strip()}")

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
        fuzzer_name = file_path.split('/')[-1].split('--')[1]
        seed_corpus_flag = False  # Flag to track if seed corpus is missing

        # Build Fuzzer && Set corpus dir command
        oss_fuzz_dir = "../"  # Replace with the actual path to your 'oss-fuzz' directory
        os.chdir(oss_fuzz_dir)
        subprocess.run(["cp", "-r", f"./cwlab/target_projects/{project_name}", "./projects/"])
        build_result = subprocess.run(["python", "infra/helper.py", "build_fuzzers", project_name])
        if build_result.returncode != 0:
            with open("./cwlab/errorlog.txt","a") as fp:
                fp.write(f"[Fail build_fuzzers] {project_name}\n")
            return
        
        # Remove existing corpus directory
        corpus_path = f"build/out/{project_name}/{fuzzer_name}_corpus"
        shutil.rmtree(corpus_path, ignore_errors=True)

        # Try to unzip the seed corpus
        unzip_command = f"unzip build/out/{project_name}/{fuzzer_name}_seed_corpus.zip -d {corpus_path}"
        unzip_result = os.system(unzip_command)
        
        if unzip_result != 0:  # Non-zero exit code indicates failure
            seed_corpus_flag = True
            os.makedirs(corpus_path, exist_ok=True)  # Create corpus folder if unzip fails
    
        # Run Fuzzer command
        option = f"-detect_leaks=0 -max_total_time={SESSION_TIME} {fuzzer_name}_corpus/"
        run_fuzzer_and_save_results(project_name, fuzzer_name, option, seed_corpus_flag)

    except Exception as e:
        with open("errorlog.txt","a") as fp:
            fp.write(f"[Check Run Fuzzer] {project_name} - {e}\n")


def main():
    #if len(sys.argv) != 3:
    #    print("Usage: python test.py [project_name] [run_fuzzer/reproduce]")
    #    sys.exit(1)
    #project_list = ['example','ibmswtpm2', 'perfetto','inchi','lzo'] #build fail
    project_list = ['assimp','gstreamer','augeas','libical', 'ndpi', 'p9', 'rdkit', 'unit','ffmpeg', 'netcdf', 'pandas', 'readstat', 'vlc', 'blackfriday','file', 'hiredis', 'ntopng', 'pcapplusplus', 'vulkan-loader', 'bloaty', 'fluent-bit','libyaml','ntpsec','perfetto', 's2opc','bluez', 'frr','llvm', 'php', 'samba', 'glog','open62541', 'plan9port', 'serenity', 'coturn', 'glslang', 'keystone', 'md4c','openbabel', 'psqlparse', 'simd', 'cups', 'gopsutil', 'libbpf', 'mruby', 'ossf-scorecard', 'pupnp','swift-protobuf','c-blosc2','haproxy','librdkafka','libredwg','oatpp','ruby','wabt','upx']


    global worker_id    
    if len(sys.argv) != 3:
        print("Usage: python test.py [worker_id] [total_worker]")
        sys.exit(1)

    worker_id = int(sys.argv[1])
    total_worker = int(sys.argv[2])

    projects_per_part = len(project_list) // total_worker
    start_index = projects_per_part * (worker_id - 1)
    end_index = start_index + projects_per_part if worker_id < total_worker else len(project_list)

    if worker_id == total_worker:
        end_index = len(project_list)

    for project_name in project_list[start_index:end_index]:
        #project_name = sys.argv[1]
        lines = read_result_file(project_name)
        #selected_line = handle_user_input(lines)
        for selected_line in lines:
            time.sleep(2)
            file_path = selected_line.split(',')[0]

            dockerfile_changed = process_dockerfile(project_name, selected_line.split(',')[-1])
        
            if dockerfile_changed:
                print("Dockerfile updated successfully.")
                update_dockerfile_run_fuzzer(project_name, file_path)
                os.chdir("./cwlab")
            else:
                print("No changes were made to the Dockerfile.")
                with open("errorlog.txt","a") as fp:
                    fp.write(f"[Check Dockerfile] {project_name}\n")


if __name__ == "__main__":
    main()

