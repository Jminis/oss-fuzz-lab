# Copyright 2021 Google LLC
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
RUN apt-get update && apt-get install -y cmake ninja-build
RUN git clone  --recursive https://github.com/assimp/assimp.git

WORKDIR assimp
RUN git checkout e50233b2c1e0eccaad8ace908c66dc7425d5d500
WORKDIR ../
WORKDIR assimp
COPY build.sh $SRC/

