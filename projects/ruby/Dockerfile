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

RUN apt-get update -y && \
    apt-get install -y libssl-dev libyaml-dev libreadline6-dev \
                       zlib1g-dev libncurses5-dev libffi-dev \
                       bison autoconf ruby pkg-config

RUN git clone https://github.com/ruby/ruby.git

WORKDIR ./ruby
RUN git checkout d89b15cdce8a2fa36fc2a150551f0dd8e58814d7

WORKDIR ../
WORKDIR ruby

COPY build.sh $SRC/
RUN mkdir $SRC/fuzz
COPY *.rb *.c *.options $SRC/fuzz/
