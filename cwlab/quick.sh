#!/bin/bash
if [ "$(id -u)" != "0" ]; then
   echo "You must be run root previlage" 1>&2
   exit 1
fi

read -p "D0 you want clean all docker container & iamges ? " yn
if [[ "$yn" =~ ^[Yy]$ ]]
then
    docker rm -f $(docker ps -aq)
    docker rmi -f $(docker images -aq)
    echo "Docker cache clear"
fi

read -p "D0 you want clean build & projects ? " yn
if [[ "$yn" =~ ^[Yy]$ ]]
then
    rm -r ../build
    rm -r ../projects
    cp -r ./projects ../projects
    echo "Env cache clear"
fi

for i in $(seq 1 5); do
    for j in $(seq 1 4); do
        nohup python3 test.py $i $j 4 >/dev/null 2>&1 &
    done
done
