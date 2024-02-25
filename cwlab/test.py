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
time0ut = 60*60*24
option = f"-print_final_stats=1 -detect_leaks=0 -timeout=60 "
#option = f"-print_final_stats=1 -use_counters=0 -detect_leaks=0 -timeout=60 "
#option = f"-print_final_stats=1 -shrink=1 -detect_leaks=0 -timeout=60 "
#option = f"-print_final_stats=1 -reduce_inputs=1 -detect_leaks=0 -timeout=60 "
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


def read_last_lines(filename, num_lines):
    with open(filename, 'rb') as f:
        f.seek(0, os.SEEK_END)
        end_position = f.tell()
        buffer_size = 1024
        buffer = bytearray()
        lines = deque()

        while f.tell() > 0 and len(lines) < num_lines:
            position = max(f.tell() - buffer_size, 0)
            f.seek(position)
            buffer = bytearray(f.read(min(end_position - position, buffer_size))) + buffer
            end_position = position
            lines.extendleft(buffer.splitlines())

        # Decode and return the last num_lines lines, ignoring decoding errors
        return [line.decode('utf-8', errors='ignore') for line in list(lines)[:num_lines]]

def run_fuzzer(args):
    global time0ut
    global option
    container_dir, project_name, fuzzer_name, container_path, worker = args
    timeout_flag = False

    try:
        # -- Create worker sub directory
        worker_sub_path = os.path.join(worker, container_dir)
        create_directory(worker_sub_path)

        # -- Set corpus directory
        corpus_path = f"../build/out/{project_name}/{fuzzer_name}_corpus_{worker}"
        #if os.path.exists(corpus_path):
        #    shutil.rmtree(corpus_path)
        shutil.copytree(f"../build/out/{project_name}/{fuzzer_name}_corpus",corpus_path)
    

        # -- Set running option
        seed_file_path = os.path.join(container_path, f"seed--{worker}")
        max_executed_units_path = os.path.join(container_path, "max_executed_units")

        # Read seed value if the file exists
        seed_value = None
        custom_option = option
        if os.path.exists(seed_file_path):
            with open(seed_file_path, 'r') as seed_file:
                seed_value = seed_file.read().strip()
            if seed_value.isdigit():
                custom_option += f"-seed={seed_value} "
        
        # Read max executed units value if the file exists
        executed_units_value = None
        if os.path.exists(max_executed_units_path):
            with open(max_executed_units_path, 'r') as units_file:
                executed_units_value = units_file.read().strip()
            
            if executed_units_value.isdigit():
                custom_option += f"-runs={executed_units_value} "
    
        # -- Run_fuzzer
        runtime_log_path = os.path.join(worker_sub_path, 'runtime_log.txt')
        start_time = datetime.datetime.now()
        try:
            with open(runtime_log_path, 'wb') as file:
                result = subprocess.run(["python3", "infra/helper.py", "run_fuzzer", 
                                         project_name, fuzzer_name, custom_option+f"{fuzzer_name}_corpus_{worker}/"],
                                         cwd='../', 
                                         stdout=file)
                                         timeout=time0ut)
        except subprocess.TimeoutExpired:
            timeout_flag = True

        finally:
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
                    last_lines = read_last_lines(runtime_log_path, 5)
                    for line in last_lines:
                        decoded_line = line
                        match_executed_units = re.search(r"stat::number_of_executed_units:\s+(\d+)", decoded_line)
                        match_new_units = re.search(r"stat::new_units_added:\s+(\d+)", decoded_line)
                        if match_executed_units:
                            number_of_executed_units = int(match_executed_units.group(1))
                        if match_new_units:
                            new_units_added = int(match_new_units.group(1))
        
                if number_of_executed_units == int(executed_units_value):
                    desc_file.write("Exceed executed units \n")
                desc_file.write(f"Execution time: {execution_time}\n")
                desc_file.write(f"Number of Files: {file_count}\n")
                desc_file.write(f"Number of Executed Units: {number_of_executed_units}\n")
                desc_file.write(f"New Units Added: {new_units_added}\n")
    
            try:
                time.sleep(3)
                shutil.rmtree(corpus_path,ignore_errors=True)
            except Exception:
                pass
            
    except Exception as e:
        logging(f"[{worker}]:{e}")


def logging(message):
    with open("test_log.txt", "a") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            args = [(container, project_name, fuzzer_name, container_path, worker) for worker in worker_list]
            with ProcessPoolExecutor(max_workers=worker_count) as executor:
                list(executor.map(run_fuzzer, args))

    # No option
    else:
        print("Usage: python test.py [build_fuzzer/run_fuzzer] [worker-count]")

if __name__ == "__main__":
    main()
