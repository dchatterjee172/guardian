FROM python:3.7-alpine
RUN apk --no-cache add curl
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
# docker run --rm -v $(pwd):/guardian -w /guardian -it guardian /bin/sh
# source $HOME/.poetry/env
# poetry install
# poetry shell
