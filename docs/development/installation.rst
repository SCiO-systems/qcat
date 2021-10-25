Installation
============

This section covers the installation of QCAT for local development. For
instructions on how to deploy QCAT to a server, refer to the
`Deployment`_ section.

.. _Deployment: deployment.html


Prerequisites
-------------

The following prerequisites are needed. Make sure to have them installed
on your system.

Git
^^^

The source code of QCAT is managed in `Git`_, a free and open source
distributed version control system.

.. _Git: http://git-scm.com/


Quick Setup
^^^^^^^^^^^

Create a virtual environment and get the code::

    mkvirtualenv --python=/usr/bin/python3.6 -a . qcat
    git clone https://github.com/CDE-UNIBE/qcat.git .

Add the ``apps`` folder to your virtalenv::

    add2virtualenv apps/

Switch to the branch you would like to work on::

    git checkout develop

Set necessary env variables:

* ``envs/DJANGO_SETTINGS_MODULE``
* ``envs/DJANGO_CONFIGURATION``
* ``envs/DJANGO_SECRET_KEY``
* ``envs/DATABASE_URL``

Install requirements::
    pip install -r requirements/development.txt

Run migrations and check if server is running::

    python manage.py migrate
    python manage.py runserver

Build frontend stuff::

    grunt build:deploy

For testing purposes, also set the following env variables:

* ``envs/TESTING_CHROMEDRIVER_PATH``
* ``envs/NEXT_MAINTENANCE``
* ``envs/GOOGLE_MAPS_JAVASCRIPT_API_KEY``

Run the tests::

    pytest


Docker
^^^^^^

Use the provided docker-compose file to create the environment. `Docker`_ and docker-compose
must be installed on your system.

.. _Docker: https://docker.com/


Preparation
^^^^^^^^^^^

Create a folder for the project::

    $ mkdir qcat && cd qcat

Get the code::

    $ git clone https://github.com/CDE-UNIBE/qcat.git .


Environment variables
^^^^^^^^^^^^^^^^^^^^^

Set following environment variables:

    * DJANGO_SETTINGS_MODULE = qcat.settings
    * DJANGO_CONFIGURATION = DevDefaultSite
    * DJANGO_SECRET_KEY = random

Run
^^^

If you want to build all requirements (static assets, elasticsearch, database), pass the 'build' param.::

    $ docker-compose run web build

If a database dump is available, copy it into the folder: /docker_compose/postgis/restore. Following file formats
are supported - keep in mind all files available are executed:

    * .sh
    * .sql
    * .sql.gz

Open your browser and go to http://0.0.0.0:8000 to see the project up and running.


Hint: Docker
^^^^^^^^^^^^

Refer to `the official docs`_. Some useful commands to clean your system:

    * docker system prune
    * docker kill $(docker ps -q)
    * docker rm $(docker ps -a -q)
    * docker rmi $(docker images -q)
    * docker volume ls -qf dangling=true | xargs -r docker volume rm

.. _the official docs: https://docs.docker.com
