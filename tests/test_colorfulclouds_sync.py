#!/usr/bin/env python3
"""Regression checks for local-first Caiyun three-way YAML merges."""
import importlib.util
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
spec = importlib.util.spec_from_file_location('caiyun_sync', root / 'scripts/sync-colorfulclouds.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
merge = mod.merge_value

def check(base, local, incoming, expected):
    actual = merge(base, local, incoming)
    assert actual == expected, (actual, expected)

check({'a': 1}, {'a': 1}, {'a': 2}, {'a': 2})
check({'a': 1}, {'a': 9}, {'a': 1}, {'a': 9})
check({'a': 1, 'b': 1}, {'a': 9, 'b': 1}, {'a': 1, 'b': 2}, {'a': 9, 'b': 2})
check({'a': 1}, {'a': 9}, {'a': 2}, {'a': 9})
check({'rules': ['old']}, {'rules': ['old', 'local']},
      {'rules': ['old', 'upstream']}, {'rules': ['old', 'local', 'upstream']})
check({'rules': ['old']}, {'rules': []},
      {'rules': ['old', 'upstream']}, {'rules': ['upstream']})
base = {'scriptings': [{'http_response': {'name': 'a', 'timeout': 10, 'match': 'old'}}]}
local = {'scriptings': [{'http_response': {'name': 'a', 'timeout': 20, 'match': 'old'}}]}
upstream = {'scriptings': [{'http_response': {'name': 'a', 'timeout': 10, 'match': 'new'}},
                          {'http_response': {'name': 'b', 'timeout': 10}}]}
check(base, local, upstream,
      {'scriptings': [{'http_response': {'name': 'a', 'timeout': 20, 'match': 'new'}},
                      {'http_response': {'name': 'b', 'timeout': 10}}]})
print('Caiyun merge regression checks passed')
