# Install stage
FROM python:3.6-slim-buster as install

COPY requirements.txt /app/
WORKDIR /app/

ENV PIPENV_SKIP_LOCK true

RUN apt-get -qq update \
    && apt-get  -qq install --assume-yes sqlite3 curl gcc python3-dev \
    && pip install pipenv \
    && pipenv install --dev --ignore-pipfile

# migrate stage
FROM install as copy_code

COPY . /app/
WORKDIR /app/

EXPOSE 3000 8000

CMD echo "\033[0;36m--------> STAGE: wait for db startup <--------" \
    && sleep 15 \
    && echo "\033[0;36m--------> STAGE: make migrations <--------" \
    && pipenv run python manage.py makemigrations wbcore \
    && echo "\033[0;36m--------> STAGE: migrate <--------" \
    && pipenv run python manage.py migrate \
    && echo "\033[0;36m--------> STAGE: rebuild index <--------" \
    && pipenv run python manage.py rebuild_index --noinput \
    && echo "\033[0;36m--------> STAGE: Starting to load the data in the database <--------" \
    && pipenv run python manage.py loaddata data/address.json \
    && echo "\033[0;36m--------> STAGE: Load: locations <--------" \
    && pipenv run python manage.py loaddata data/locations.json \
    && echo "\033[0;36m--------> STAGE: Load: hosts <--------" \
    && pipenv run python manage.py loaddata data/hosts.json \
    # && echo "\033[0;36m--------> STAGE: Load: images <--------" \
    # && pipenv run python manage.py loaddata data/images.json \
    # && echo "\033[0;36m--------> STAGE: Load: news <--------" \
    # && pipenv run python manage.py loaddata data/news.json \
    # && echo "\033[0;36m--------> STAGE: Load: blog <--------" \
    # && pipenv run python manage.py loaddata data/blog.json \
    # && echo "\033[0;36m--------> STAGE: Load: partners <--------" \
    # && pipenv run python manage.py loaddata data/partners.json \
    # && echo "\033[0;36m--------> STAGE: Load: projects <--------" \
    # && pipenv run python manage.py loaddata data/projects.json \
    && echo "\033[0;36m--------> STAGE: Creating superuser <--------" \
    && pipenv run python manage.py createsuperuser \
    && echo "\033[0;36m--------> STAGE: starting server <--------" \
    && echo "\033[0;36m Server running on: \033[0;32m  http://localhost:3000 " \
    && pipenv run python manage.py runserver 0.0.0.0:3000


HEALTHCHECK --interval=20s --timeout=5s --start-period=25s --retries=3 CMD curl -get http://localhost || exit 1