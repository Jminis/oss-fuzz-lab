# Fuzzing Lab Based on Coverage Feedback
## Resource
- `test.py`: "factory/[repo]" 들을 대상으로 build_fuzzer 또는 run_fuzzer를 수행합니다.
- `parse_iter_seed.py`: default libfuzzer 수행 결과로부터 max_executed_units 및 seed를 parsing하여 "factory/[repo]" 경로에 저장합니다. 

## Build Repo
- `factory/[repo]` 내부 퍼저 바이너리들을 빌드합니다
```bash
python test.py build_fuzzer
```

## Run Fuzzing
- `factory/[repo]` 내부 퍼저 바이너리를 5개의 worker로 수행합니다.
```bash
# Automatically Fuzzing for all target projects on background
./start.sh
```

```bash
# Passive fuzzing
python test.py run_fuzzer [worker-count]
```

## Output data
- fuzzing 수행 시 `worker-n` 폴더 내부에 repo별 퍼징 수행 결과가 저장됩니다.
- `descripton.txt`: Includes the time taken to discover the crash and the number of corpus creations.
- `runtime_log.txt`: Includes Fuzzing log data

