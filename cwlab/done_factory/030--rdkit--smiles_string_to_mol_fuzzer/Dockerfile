# Copyright 2020 Google Inc.
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

FROM gcr.io/oss-fuzz-base/base-builder
RUN apt-get update && apt-get install -y wget

RUN git clone https://gitlab.com/libeigen/eigen && \
    mkdir eigen_build && \
    cd eigen_build && \
    cmake ../eigen && \
    make install

RUN git clone  https://github.com/rdkit/rdkit.git $SRC/rdkit

WORKDIR $SRC/rdkit
RUN git checkout 3720c2ceaf5193e88ecd4096eac87d2653495b77
WORKDIR ../
WORKDIR $SRC/rdkit
COPY build.sh $SRC/
