import os
import datetime
TIMEOUT_SET = datetime.time(1, 0, 0)

def parse_time(time_str):
    try:
        if '.' in time_str:
            # Assuming format 'hours:minutes:seconds.microseconds'
            return datetime.datetime.strptime(time_str, '%H:%M:%S.%f').time()
        else:
            # Assuming format 'hours:minutes:seconds'
            return datetime.datetime.strptime(time_str, '%H:%M:%S').time()
    except ValueError as e:
        print(f"Time parsing error: {e}, with time string: {time_str}")
        return None

def parse_description(file_path):
    # Process the description and extract the needed information
    data = {
        "Execution Time": None,
        "Number of Files": None,
        "No Seed Corpus Available": False,
        "Crash Files Copied": False
    }
    with open(file_path, 'r') as file:
        for line in file:

            if line.startswith('Execution Time:'):
                time_str = line.split(': ')[1].strip()
                data["Execution Time"] = parse_time(time_str)
            elif line.startswith('Number of Files:'):
                data["Number of Files"] = int(line.split(':')[1].strip())
            elif 'No Seed Corpus Available' in line:
                data["No Seed Corpus Available"] = True
            elif 'Crash Files Copied' in line:
                data["Crash Files Copied"] = True
    return data

def compare_and_format_results(custom_data, default_data, fuzzer_name):
    if custom_data["Execution Time"] < default_data["Execution Time"]:
        custom_check = 'v'
        default_check = ''
    else:
        custom_check = ''
        default_check = 'v'

    if custom_data["Execution Time"] > TIMEOUT_SET:
        custom_data["Execution Time"] = '----TIMEOUT----'
        custom_check = ''
    if default_data["Execution Time"] > TIMEOUT_SET:
        default_data["Execution Time"] = '----TIMEOUT----'
        default_check = ''

    seed_default = 'o' if not default_data["No Seed Corpus Available"] else 'x'

    return [
        '{:<6}'.format(custom_data["Number of Files"]),
        '{:<15}'.format(str(custom_data["Execution Time"])),
        '{:^6}'.format(custom_check),
        '{:^40}'.format(fuzzer_name),
        '{:^6}'.format(default_check),
        '{:<15}'.format(str(default_data["Execution Time"])),
        '{:<6}'.format(default_data["Number of Files"]),
        '{:<6}'.format(seed_default)
    ]

def compare_folders_and_create_final(custom_folder, default_folder):
    final_results = []
    custom_subdir = os.listdir(custom_folder)
    default_subdir = os.listdir(default_folder)
    custom_subdir.sort()
    default_subdir.sort()
    for i in range(0,len(custom_subdir)):
        subdir_path_custom = os.path.join(custom_folder, custom_subdir[i])
        subdir_path_default = os.path.join(default_folder, default_subdir[i])
        print(subdir_path_custom,subdir_path_default)
        if os.path.isdir(subdir_path_custom) and os.path.isdir(subdir_path_default):
            desc_file_custom = os.path.join(subdir_path_custom, "description.txt")
            desc_file_default = os.path.join(subdir_path_default, "description.txt")
            if os.path.isfile(desc_file_custom) and os.path.isfile(desc_file_default):
                custom_data = parse_description(desc_file_custom)
                default_data = parse_description(desc_file_default)
                formatted_result = compare_and_format_results(custom_data, default_data, custom_subdir[i].rsplit('_',2)[0].strip())
                final_results.append(formatted_result)
   
    first_row = '{:<80}'.format("Custom") + '{:<62}'.format("Default")
    second_row = [
        '{:<6}'.format("Corpus"),
        '{:^15}'.format("Time"),
        '{:^6}'.format("Check"),
        '{:^40}'.format("Fuzzer"),
        '{:^6}'.format("Check"),
        '{:^15}'.format("Time"),
        '{:<6}'.format("Corpus"),
        '{:<6}'.format("Seed")
    ]

    final_str = first_row + "\n" + "\t".join(second_row) + "\n"
    for result in final_results:
        final_str += "\t".join(map(str, result)) + "\n"

    with open('./final.txt', 'w') as f:
        f.write(final_str)

# Provide the actual paths for your custom and default result folders
custom_folder_path = './a_result'
default_folder_path = './b_result'

compare_folders_and_create_final(custom_folder_path, default_folder_path)

# Print the path to the final.txt file
final_file_path = './final.txt'
print(f"The final.txt file has been saved to: {final_file_path}")
