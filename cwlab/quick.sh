#!/bin/bash
for i in $(seq 1 6); do
	nohup python3 test.py $i 6 >/dev/null 2>&1 &
done
