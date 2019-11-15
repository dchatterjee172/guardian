FROM python:3.7-alpine
RUN apk --no-cache add curl sqlite openssl
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
EXPOSE 443
# docker run --rm -p 443:443 -v $(pwd):/guardian -w /guardian -it guardian /bin/sh
