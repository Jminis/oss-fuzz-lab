# Copyright 2016 Google Inc.
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
RUN apt-get update && apt-get install -y libreadline-dev libselinux1-dev \
    libxml2-dev make autoconf automake libtool pkg-config bison flex

RUN git clone  https://github.com/hercules-team/augeas

WORKDIR augeas
RUN git checkout f0a0586d5fa3cd302e6a073f6081c1626471f7dc
WORKDIR ../
WORKDIR augeas

COPY build.sh $SRC/
COPY augeas_escape_name_fuzzer.cc $SRC/
COPY augeas_fa_fuzzer.cc $SRC/
COPY augeas_api_fuzzer.cc $SRC/
