FROM python:3.7-alpine
EXPOSE 443
RUN apk --no-cache add curl sqlite openssl g++ libffi-dev nginx
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
# docker run --rm -p 443:443 -v $(pwd):/guardian -w /guardian -it guardian /bin/sh
