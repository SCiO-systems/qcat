#!/bin/bash

# build image.
docker build -t locust .
# get path to file - this will be available in the docker container.
script_path=$(dirname $(realpath -s $0))
docker run -d -v $script_path:/locust -P locust --host=https://qcat-dev.wocat.net
# get the ip of the latest container.
docker_ip=$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' $(docker ps -q))
# 8089 is the exposed port of locust - open it in the browser.
url="http://$docker_ip:8089"
xdg-open $url