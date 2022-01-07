#!/bin/bash

# Wait for all services.
waitfor camptocamp/postgres:5432 -- python manage.py check
waitfor redis:6379 -- python manage.py check
waitfor elasticsearch:9200 -- python manage.py check

# Set env-files according to docker-compose containers
mv /code/envs/DATABASE_URL /code/envs/DATABASE_URL.bak
mv /code/envs/ES_HOST /code/envs/ES_HOST.bak
mv /code/envs/CACHES /code/envs/CACHES.bak

echo "postgis://qcat:qcat@postgres:5432/qcat?sslmode=disable" > /code/envs/DATABASE_URL
echo "elasticsearch" > /code/envs/ES_HOST
#echo "{'default': {'BACKEND': 'django_redis.cache.RedisCache','LOCATION': 'redis:6379','OPTIONS': {'PARSER_CLASS': 'redis.connection.HiredisParser'}}}" > /code/envs/CACHES

# Create static assets, and prepare all data for the application.
if [ "$1" = 'build' ]; then

    # prepare database and data
    echo "prepare database and data"
    #python manage.py migrate --noinput
    #python manage.py load_qcat_data

    echo '###########################'
    echo "loaddata technologies approaches cca watershed cbp"
    # python manage.py loaddata technologies approaches cca watershed cbp

    # # Load technologies 2018 edition
    # #  - Must be run only first time, subsequent loads cause conflicts
    #python manage.py loaddata technologies_2018
    # # Update technologies 2018 edition
    # python manage.py runscript technologies_2018

    # Generating static files

    mkdir /root/.nvm
    curl -o- https://raw.githubusercontent.com/creationix/nvm/master/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
    nvm install 8
    nvm use 8
    apt-get install python2.7 -y
    npm config set python python2.7

    npm rebuild jpegtran-bin

    npm install bower
    npm install grunt-cli
    npm install

    npm run bower
    npm run grunt

    echo '###########################'
    echo "python3 manage.py collectstatic"
    python3 manage.py collectstatic
    python3 manage.py compress

    echo "LOAD TEST DATA"
    python3 manage.py loaddata apps/sample/fixtures/sample_global_key_values.json
    python3 manage.py loaddata apps/sample/fixtures/sample.json
    echo '###########################'
    echo "END RUN python3 manage.py compress --force"

    # refresh elasticsearch
    #echo "Create and populate Elasticsearch indexes"
    python manage.py rebuild_es_indexes

    python manage.py runserver 0.0.0.0:8000
else
    if [[ "'$*'" == *"manage.py test"* ]]  # only add if 'manage.py test' in the args
    then
      # get the container id
      THIS_CONTAINER_ID_LONG=`cat /proc/self/cgroup | grep 'docker' | sed 's/^.*\///' | tail -n1`
      # take the first 12 characters - that is the format used in /etc/hosts
      THIS_CONTAINER_ID_SHORT=${THIS_CONTAINER_ID_LONG:0:12}
      # search /etc/hosts for the line with the ip address which will look like this:
      #     172.18.0.4    8886629d38e6
      THIS_DOCKER_CONTAINER_IP_LINE=`cat /etc/hosts | grep $THIS_CONTAINER_ID_SHORT`
      # take the ip address from this
      THIS_DOCKER_CONTAINER_IP=`(echo $THIS_DOCKER_CONTAINER_IP_LINE | grep -o '[0-9]\+[.][0-9]\+[.][0-9]\+[.][0-9]\+')`
      # add the port you want on the end
      # Issues here include: django changing port if in use (I think)
      # and parallel tests needing multiple ports etc.
      THIS_DOCKER_CONTAINER_TEST_SERVER="$THIS_DOCKER_CONTAINER_IP:8081"
      echo "this docker container test server = $THIS_DOCKER_CONTAINER_TEST_SERVER"
      export DJANGO_LIVE_TEST_SERVER_ADDRESS=$THIS_DOCKER_CONTAINER_TEST_SERVER
    fi
    exec "$@"
fi
