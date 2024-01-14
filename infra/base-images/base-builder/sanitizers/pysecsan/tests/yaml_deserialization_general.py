#!/usr/bin/python3
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
"""Fuzzer for insecure yaml deserialization."""

import sys
import yaml
import atheris
import pysecsan


def serialize_with_tainted_data(param):
  """Hit insecure yaml function."""
  try:
    yaml.load(param, yaml.Loader)
  except yaml.YAMLError:
    pass


def test_one_input(data):
  """Fuzzer routine."""
  fdp = atheris.FuzzedDataProvider(data)
  serialize_with_tainted_data(fdp.ConsumeUnicodeNoSurrogates(32))


def main():
  """Set up and start fuzzing."""
  pysecsan.add_hooks()

  atheris.instrument_all()
  atheris.Setup(sys.argv, test_one_input, enable_python_coverage=True)
  atheris.Fuzz()


if __name__ == '__main__':
  main()
