#!/bin/bash
for j in $(seq 1 3); do
    for i in $(seq 1 6); do
        nohup python3 test.py $i 6 $j >/dev/null 2>&1 &
    done
done
