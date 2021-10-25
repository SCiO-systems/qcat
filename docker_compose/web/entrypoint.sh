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
    python manage.py migrate --noinput
    #python manage.py load_qcat_data

    echo '###########################'
    echo "loaddata technologies approaches cca watershed cbp"
    # python manage.py loaddata technologies approaches cca watershed cbp

    # # Load technologies 2018 edition
    # #  - Must be run only first time, subsequent loads cause conflicts
    #python manage.py loaddata technologies_2018
    # # Update technologies 2018 edition
    # python manage.py runscript technologies_2018

    # create static assets
    echo '###########################'
    echo "npm install"
    npm install

    echo '###########################'
    echo "bower install"
    bower install

    echo '###########################'
    echo "grunt build:deploy --force"
    grunt build:deploy --force

    echo '###########################'
    echo "lpython manage.py collectstatic --noinput"
    python manage.py collectstatic --noinput

    # refresh elasticsearch
    #echo "Create and populate Elasticsearch indexes"
    python manage.py rebuild_es_indexes

    python manage.py runserver 0.0.0.0:8000

else
    python manage.py runserver 0.0.0.0:8000
    exec "$@"
fi