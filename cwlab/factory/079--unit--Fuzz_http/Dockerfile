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
FROM gcr.io/oss-fuzz-base/base-builder
RUN apt-get update && apt-get install -y autoconf
RUN git clone  https://github.com/nginx/unit

WORKDIR unit
RUN git checkout d9f5f1fb741109cc232cedd3574aa587626789c1
WORKDIR ../
RUN git clone https://github.com/0x34d/oss-fuzz-bloat
COPY build.sh $SRC/
COPY fuzzer/ $SRC/unit/fuzzer/
WORKDIR $SRC/unit/
