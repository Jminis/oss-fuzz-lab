# Fuzzing Lab Based on Coverage Feedback
## Resource
- `crash`: ASAN logs and crash input data files obtained from OSSFuzz execution results
- `extract.py`: Parsing foundational data for fuzzing based on the information in the `crash`.
- `run.py`: python3 code for Fuzzing a single project
- `test.py`: python3 code for Fuzzing multiple projects

## Setting Environment
If you want to use the default libfuzzer code, do not build the base-clang image.
```bash
./make.sh
cd cwlab
python extract.py
```

## Run Fuzzing
```bash
# Automatically Fuzzing for all target projects
python test.py
```
```bash
# Fuzzing for target project
python run.py [project_name] [run_fuzzer/reproduce]
```

## Output data
- `descripton.txt`: Includes the time taken to discover the crash and the number of corpus creations.
- `runtime_log.txt`: Includes Fuzzing log data
- corpus file
