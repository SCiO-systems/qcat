FROM camptocamp/postgres:9.5

ENV POSTGRES_USER qcat
ENV POSTGRES_DB qcat

COPY ./docker_compose/postgis/restore/* /docker-entrypoint-initdb.d/
