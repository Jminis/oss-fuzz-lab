import os
from collections import deque
import re

base_dir = './'
workers_dir = os.path.join(base_dir, 'default-240213')
factory_dir = os.path.join(base_dir, 'factory')

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


# worker 반복
for worker in os.listdir(workers_dir):
    worker_path = os.path.join(workers_dir, worker)
    if os.path.isdir(worker_path):

        # project 반복
        for project_folder in os.listdir(worker_path):
            print(project_folder)
            log_path = os.path.join(worker_path, project_folder, 'runtime_log.txt')
            if os.path.isfile(log_path):

                # Read runtime_log.txt
                with open(log_path, 'rb') as log_file:
                    seed = None
                    for _ in range(30):
                        line = log_file.readline().decode('utf-8')
                        seed_match = re.search(r"INFO: Seed: (\d+)", line)
                        if seed_match:
                            seed = seed_match.group(1)
                            break
                

                # Parse seed 
                target_dir = os.path.join(factory_dir, project_folder)
                seed_file_path = os.path.join(target_dir, f"seed--{worker}")
                with open(seed_file_path, 'w') as seed_file:
                    seed_file.write(seed)

                # Parse executed_units
                last_lines = read_last_lines(log_path, 5)
                for line in last_lines:
                    match_executed_units = re.search(r"stat::number_of_executed_units:\s+(\d+)", line)
                    print(line)

                number_of_executed_units = -1
                if match_executed_units:
                    number_of_executed_units = int(match_executed_units.group(1)) * 2
                    target_dir = os.path.join(factory_dir, project_folder)
                    units_file_path = os.path.join(target_dir, "max_executed_units")
        
                    if os.path.exists(units_file_path):
                        with open(units_file_path, 'r') as units_file:
                            existing_units = int(units_file.read().strip())
                            if number_of_executed_units > existing_units:
                                with open(units_file_path, 'w') as units_file:
                                    units_file.write(str(number_of_executed_units))
                    else:
                        with open(units_file_path, 'w') as units_file:
                            units_file.write(str(number_of_executed_units))
