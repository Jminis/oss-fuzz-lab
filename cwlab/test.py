import os
import shutil
import subprocess
import sys
import datetime
from collections import deque
import re
import time
import glob


time0ut = 10
factory_path = "./factory"
worker_path = "./worker-default"

def error(container_dir,e):
    os.rename(os.path.join(worker_path, container_dir),f"{worker_path}/{container_dir}--check_{e}")
    
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def check_build(container_path, project_name):
    projects_dockerfile_path = os.path.join('../projects', project_name, 'Dockerfile')
    container_dockerfile_path = os.path.join(container_path, 'Dockerfile')
    
    # 이전에 생성한 적이 없는 이미지라면 빌드
    result = subprocess.run(["docker", "images", "--format", "{{.Repository}}"], capture_output=True, text=True)
    image_list = result.stdout.strip().split('\n')

    if not any(project_name in image for image in image_list):
        shutil.copy(container_dockerfile_path, projects_dockerfile_path)
        for i in range(0,10):
            if subprocess.run(["python", "infra/helper.py", "build_fuzzers", project_name], cwd="../") == 0:
                return True
        error(os.path.basename(container_path),"build_fuzzers")
        return False
            
    else:        
        # 이전 도커 파일과 달라진게 있는 경우에만 빌드
        with open(projects_dockerfile_path, 'r') as file1, open(container_dockerfile_path, 'r') as file2:
            if file1.read() != file2.read():
                shutil.copy(container_dockerfile_path, projects_dockerfile_path)
                for i in range(0,10):
                    if subprocess.run(["python", "infra/helper.py", "build_fuzzers", project_name], cwd="../") == 0:
                        return True
                error(os.path.basename(container_path),"build_fuzzers")
                return False
            
    return True

    
def run_fuzzer(container_dir):
    global factory_path
    global worker_path
    global time0ut

    id = container_dir.split('--')[0]
    project_name = container_dir.split('--')[1]
    fuzzer_name = container_dir.split('--')[2]
    container_path = os.path.join(factory_path, container_dir) # 퍼징 수행 경로
    worker_dir_path = os.path.join(worker_path, container_dir) # 결과 저장 경로
    create_directory(worker_dir_path)

    # 퍼저 빌드 과정: dockerfile, build_fuzzers
    if not check_build(container_path,project_name):
        return

    # 퍼징 준비 과정: seed corpus
    no_seed_corpus = False
    corpus_path = f"../build/out/{project_name}/{fuzzer_name}_corpus_{id}"
    shutil.rmtree(corpus_path, ignore_errors=True)
    unzip_command = f"unzip build/out/{project_name}/{fuzzer_name}_seed_corpus.zip -d {corpus_path}"
    unzip_result = os.system(unzip_command)
        
    if unzip_result != 0:
        no_seed_corpus = True
        os.makedirs(corpus_path, exist_ok=True)

    # 퍼저 수행 과정: run_fuzzers
    timeout_flag = False
    runtime_log_path = os.path.join(worker_dir_path,'runtime_log.txt')
    option = f"-print_final_stats=1 -detect_leaks=0 -max_total_time={time0ut} {fuzzer_name}_corpus_{id}/"

    start_time = datetime.datetime.now()
    try:
        with open(runtime_log_path, 'w') as file:
            subprocess.run(["python3", "infra/helper.py", "run_fuzzer", project_name, fuzzer_name, option], cwd='../',stdout=file, timeout=time0ut)
    except subprocess.TimeoutExpired:
        timeout_flag = True
    execution_time = datetime.datetime.now() - start_time
    
    # 실행 결과 저장: execution time, corpus count, final stat
    corpus_path = f"../build/out/{project_name}/{fuzzer_name}_corpus_{id}"
    file_count = len(os.listdir(corpus_path)) if os.path.exists(corpus_path) else 0
    try:
        shutil.rmtree(corpus_path)
    except Exception as e:
        pass

    with open(os.path.join(worker_dir_path, "description.txt"), "w") as desc_file:
        number_of_executed_units = 0
        new_units_added = 0
        if timeout_flag:
            error(container_dir,"timeout")
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
            
            crash_file_pattern = f"../build/out/{project_name}/crash-*"
            for crash_file in glob.glob(crash_file_pattern):
                shutil.move(crash_file, worker_dir_path)

        desc_file.write(f"Execution time: {execution_time}\n")                # 실행 시간
        desc_file.write(f"Number of Files: {file_count}\n")                         # corpus 갯수
        desc_file.write(f"Number of Executed Units: {number_of_executed_units}\n")  # final stat
        desc_file.write(f"New Units Added: {new_units_added}\n")
        if no_seed_corpus:
            desc_file.write("No Seed Corpus Available\n")



def main():
    global factory_path
    global worker_path

    if os.geteuid() != 0:
        print("This script must be run as root.")
        sys.exit(1)

    if len(sys.argv) != 4:
        print("Usage: python test.py [worker_id] [n] [m]")
        sys.exit(1)

    # Setting worker dir
    worker_path = f"./worker-{sys.argv[1]}"
    create_directory(worker_path)
    
    # Run fuzzer
    containers = [d for d in os.listdir(factory_path)]
    containers.sort()

    # Distrubute
    n, m = int(sys.argv[2]), int(sys.argv[3])
    all_count = len(containers)
    div_size = all_count // m + (1 if all_count % m else 0)  # 마지막 조각에 남는 항목을 처리
    start = (n - 1) * div_size
    end = start + div_size

    # n번째 조각 선택
    containers = containers[start:end]

    # 유효성 검사 후 n번째 조각 실행
    for container in containers:
        time.sleep(1)
        run_fuzzer(container)

if __name__ == "__main__":
    main()
