# Copyright 2017 Google Inc.
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
RUN apt-get update && apt-get install -y cmake ninja-build g++ libz-dev
RUN git clone  https://github.com/google/bloaty.git bloaty

WORKDIR bloaty
RUN git checkout 2757d3ec0fec07f4ac7f2f96fe8f0b020c2d84fb
WORKDIR ../
WORKDIR bloaty
COPY build.sh $SRC/
