# Copyright 2023 Google LLC
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
RUN apt-get update && apt-get install -y make autoconf automake libtool ninja-build \
    liblzma-dev libzstd-dev pkg-config libglib2.0-dev groff libxml2-dev \
    libcurl4-openssl-dev libsqlite3-dev flex bison

# Ntopng
RUN git clone  https://github.com/ntop/ntopng.git ntopng

WORKDIR ntopng
RUN git checkout eaab912ef8ad0f0c1572c243a05d697fb07c7fac
WORKDIR ../
ENV NTOPNG_HOME=$SRC/ntopng


### Fuzzing dependencies ###

# Build libprotobuf-mutator
RUN git clone --depth 1 https://github.com/google/libprotobuf-mutator.git
RUN mkdir libprotobuf-mutator/build; cd libprotobuf-mutator/build; \
    cmake .. -GNinja -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DLIB_PROTO_MUTATOR_DOWNLOAD_PROTOBUF=ON -DLIB_PROTO_MUTATOR_TESTING=OFF -DCMAKE_BUILD_TYPE=Release; \
    ninja;

### Dependencies that need static linking ###

ADD https://www.tcpdump.org/release/libpcap-1.9.1.tar.gz libpcap-1.9.1.tar.gz
RUN tar -xvzf libpcap-1.9.1.tar.gz
ADD https://github.com/zeromq/libzmq/releases/download/v4.3.4/zeromq-4.3.4.tar.gz zeromq-4.3.4.tar.gz
RUN tar -xvzf zeromq-4.3.4.tar.gz
ADD https://github.com/json-c/json-c/archive/refs/tags/json-c-0.16-20220414.tar.gz json-c-0.16-20220414.tar.gz
RUN tar -xvzf json-c-0.16-20220414.tar.gz
ADD https://github.com/maxmind/libmaxminddb/releases/download/1.7.1/libmaxminddb-1.7.1.tar.gz libmaxminddb-1.7.1.tar.gz
RUN tar -xvzf libmaxminddb-1.7.1.tar.gz;

### ntopng dependecies ###

RUN git clone --depth 1 https://github.com/ntop/nDPI.git nDPI
ENV NDPI_HOME=$SRC/nDPI


WORKDIR ntopng

COPY build.sh $SRC/
