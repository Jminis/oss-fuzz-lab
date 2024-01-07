import subprocess
import sys

def run_script_and_process_output(script, command):
    # run.py 스크립트 실행 및 출력 캡처
    process = subprocess.Popen(['python3', script] + command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, text=True)
    output, _ = process.communicate()

    # 출력된 줄 수 파악
    output_lines = output.split('\n')
    num_lines = sum(1 for line in output_lines if line.strip().isdigit())
    print(num_lines)
    sys.exit(1)

    # 각 숫자에 대해 처리
    for i in range(1, num_lines + 1):
        process.stdin.write(f'{i}\n')
        process.stdin.flush()
        # "Dockerfile updated successfully."가 나오면 "y" 전달
        if "Dockerfile updated successfully." in process.stdout.readline():
            process.stdin.write('y\n')
            process.stdin.flush()
        else:
            # 실패한 경우 error.txt 파일에 저장
            with open("error.txt", "a") as error_file:
                error_file.write(f'Failed at input {i} for command {command}\n')

    process.stdin.close()
    process.wait()

# 예제 사용
run_script_and_process_output('run.py', ['example', 'run_fuzzer'])

