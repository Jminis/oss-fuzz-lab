# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################

FROM gcr.io/oss-fuzz-base/base-builder-python
RUN apt-get update && apt-get install -y flex bison python3-setuptools
RUN pip3 install Cython
RUN pip3 install --upgrade Cython
RUN git clone https://github.com/alculquicondor/psqlparse && \
    cd psqlparse && \
    git checkout 72decb854590f70cbc54c549cd033df4a256b68b && \
    git submodule update --init

COPY build.sh *.py $SRC/
WORKDIR psqlparse
