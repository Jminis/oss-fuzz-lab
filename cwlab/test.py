import os
import shutil
import subprocess
import sys
import datetime
from collections import deque
import re
import time
import glob
from concurrent.futures import ProcessPoolExecutor, as_completed

# TODO: check fuzzing option
time0ut = 10
option = f"-print_final_stats=1 -detect_leaks=0 -max_total_time={time0ut} "
factory_path = "./factory"
worker_list = []

def re_container(container_path,e):
    new_container_path = f"{container_path}--{e}"
    os.rename(container_path,new_container_path)
    return new_container_path
    
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def check_build(container_path, project_name):
    projects_dockerfile_path = os.path.join('../projects', project_name, 'Dockerfile')
    container_dockerfile_path = os.path.join(container_path, 'Dockerfile')
    
    shutil.copy(container_dockerfile_path, projects_dockerfile_path)
    for i in range(0,3):
        if subprocess.run(["python", "infra/helper.py", "build_fuzzers", project_name], cwd="../").returncode == 0:
            time.sleep(3)
            return True
        re_container(container_path,"error_build_fuzzer")
        return False
    
def parse(container_dir):
    project_name = container_dir.split('--')[1]
    fuzzer_name = container_dir.split('--')[2]
    container_path = os.path.join(factory_path, container_dir) # 퍼징 수행 경로
    return project_name, fuzzer_name, container_path

def build_fuzzer(container_dir):
    global factory_path
    global worker_list
    project_name, fuzzer_name, container_path = parse(container_dir)

    # -- Clean up
    seed_corpus = True
    shutil.rmtree(f"{container_path}/{project_name}", ignore_errors=True)
    shutil.rmtree(f"../build/out/{project_name}", ignore_errors=True)

    # -- Build_fuzzer
    if not check_build(container_path,project_name):
        return

    # -- Build_fuzzer directory
    corpus_path = f"../build/out/{project_name}/{fuzzer_name}_corpus"
    if os.system(f"unzip ../build/out/{project_name}/{fuzzer_name}_seed_corpus.zip -d {corpus_path}") != 0:
        container_path = re_container(container_path,"no_seed")
        create_directory(corpus_path)
    print(f"../build/out/{project_name} to {container_path}")
    shutil.move(f"../build/out/{project_name}",container_path)

def run_fuzzer(args):
    global time0ut
    global option
    container_dir, project_name, fuzzer_name, container_path, worker = args
    timeout_flag = False

    # -- Create worker sub directory
    worker_sub_path = os.path.join(worker, container_dir)
    create_directory(worker_sub_path)

    # -- Set corpus directory
    corpus_path = f"../build/out/{project_name}/{fuzzer_name}_corpus_{worker}"
    if os.path.isdir(corpus_path):
        shutil.rmtree(corpus_path)
    shutil.copytree(f"../build/out/{project_name}/{fuzzer_name}_corpus",corpus_path)
    
    # -- Run_fuzzer
    runtime_log_path = os.path.join(worker_sub_path, 'runtime_log.txt')
    start_time = datetime.datetime.now()
    try:
        with open(runtime_log_path, 'wb') as file:
            result = subprocess.run(["python3", "infra/helper.py", "run_fuzzer", 
                                     project_name, fuzzer_name, option+f"{fuzzer_name}_corpus_{worker}/"],
                                     cwd='../', 
                                     stdout=file,
                                     timeout=time0ut)
    except subprocess.TimeoutExpired:
        timeout_flag = True
    execution_time = datetime.datetime.now() - start_time
    
    # -- Check corpus file (legacy)
    corpus_path = f"../build/out/{project_name}/{fuzzer_name}_corpus_{worker}"
    file_count = len(os.listdir(corpus_path)) if os.path.exists(corpus_path) else 0

    # -- Writing description.txt
    number_of_executed_units = 0
    new_units_added = 0
    with open(os.path.join(worker_sub_path, "description.txt"), "w") as desc_file:
        if timeout_flag:
            desc_file.write("Timeout occurred\n")
        else:
            with open(runtime_log_path, 'r') as file:
                last_lines = deque(file, 5)
            for line in last_lines:
                decoded_line = line
                match_executed_units = re.search(r"stat::number_of_executed_units:\s+(\d+)", decoded_line)
                match_new_units = re.search(r"stat::new_units_added:\s+(\d+)", decoded_line)
                if match_executed_units:
                    number_of_executed_units = int(match_executed_units.group(1))
                if match_new_units:
                    new_units_added = int(match_new_units.group(1))

        desc_file.write(f"Execution time: {execution_time}\n")
        desc_file.write(f"Number of Files: {file_count}\n")
        desc_file.write(f"Number of Executed Units: {number_of_executed_units}\n")
        desc_file.write(f"New Units Added: {new_units_added}\n")
    
    # -- Clean up corpus directory
    try:
        shutil.rmtree(corpus_path)
    except:
        pass
    #shutil.rmtree(f"../build/out/{project_name}")


def logging(message):
    with open("test_log.txt", "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] {message}\n")

def main():
    global factory_path
    global worker_list

    if os.geteuid() != 0:
        print("This script must be run as root.")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python test.py [build_fuzzer/run_fuzzer] [worker-count]")
        sys.exit(1)
    
    # Fuzzer Repo == Container
    containers = [d for d in os.listdir(factory_path)]
    containers.sort()

    # Build_fuzzer
    if sys.argv[1] == "build_fuzzer":
        for container in containers:
            build_fuzzer(container)
        print("build_fuzzer done")
    # Run_fuzzer
    elif sys.argv[1] == "run_fuzzer" and len(sys.argv) == 3 and int(sys.argv[2]):
        # build_fuzzer Worker Directory
        worker_list = [f"worker-{i}" for i in range(1,int(sys.argv[2])+1)]
        worker_count = int(sys.argv[2])
        for worker_dir in worker_list:
            create_directory(worker_dir)
        for container in containers:
            project_name, fuzzer_name, container_path = parse(container)
            # -- Setting fuzzer binary
            if os.path.isdir(container_path) and "error_build_fuzzer" not in container:
                shutil.copytree(f"{container_path}/{project_name}",f"../build/out/{project_name}",dirs_exist_ok=True)
            else:
                continue
            # -- Worker run
            with ProcessPoolExecutor(max_workers=worker_count) as executor:
                args = [(container, project_name, fuzzer_name, container_path, worker) for worker in worker_list]
                with ProcessPoolExecutor(max_workers=worker_count) as executor:
                    list(executor.map(run_fuzzer, args))
    # No option
    else:
        print("Usage: python test.py [build_fuzzer/run_fuzzer] [worker-count]")

if __name__ == "__main__":
    main()
