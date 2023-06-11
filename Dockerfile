# Based on https://medium.com/@albertazzir/blazing-fast-python-docker-builds-with-poetry-a78a66f5aed0

# The image used to build
FROM python:3.11 as builder

RUN pip install poetry==1.5.1

# Don't disable virutal environment as it can mess with poetry installation. This should be default in project settings already.
# ENV POETRY_CACHE_DIR=/tmp/poetry_cache
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
# A docker container probably doesn't need a readme but poetry will complain otherwise
RUN touch README.md

# Install dependencies first without project source code to improve docker build as this layer will be cached apparently
RUN poetry install --without dev --no-root \
    # Clean package cache used for package reuse after
    && rm -rf $POETRY_CACHE_DIR
# Remove readme only used for build
# && rm README.md
# Run project without poetry dependency (use poetry only for build)
# The smaller runtime image, used to just run the code provided its virtual environment
FROM python:3.11-slim-buster as runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy source code
COPY wappstore ./wappstore

ENTRYPOINT ["uvicorn", "wappstore.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]