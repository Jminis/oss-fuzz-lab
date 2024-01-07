#!/bin/bash
# git clone https://github.com/jhkim19940830/llvm-project	#llvm-dep
# git clone --depth 1 https://github.com/google/oss-fuzz.git 	#origin
git clone --depth 1 https://github.com/jhkim19940830/oss-fuzz
cp -r oss-fuzz/projects cwlab/
cd oss-fuzz/infra/base-images/base-clang
docker build . -t gcr.io/oss-fuzz-base/base-clang
