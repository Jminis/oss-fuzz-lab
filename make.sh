#!/bin/bash
# git clone https://github.com/jhkim19940830/llvm-project	#llvm-dep
# git clone --depth 1 https://github.com/google/oss-fuzz.git 	#origin
git clone --depth 1 https://github.com/jhkim19940830/oss-fuzz
cd oss-fuzz
mv infra/ projects/ tools/ ../
cd ..
rm -r oss-fuzz
cp -r projects cwlab/
cd infra/base-images/base-clang
docker build . -t gcr.io/oss-fuzz-base/base-clang		#custom image build
