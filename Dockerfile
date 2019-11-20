FROM python:3.7-alpine
EXPOSE 443
RUN apk --no-cache add curl sqlite openssl g++ libffi-dev nginx
RUN openssl req -new -x509 -days 365 -nodes -newkey rsa:4096 -out /cacert.pem -keyout /privkey.pem -subj '/CN=SOMETHING/O=SOMETHING /C=IN'
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
RUN mkdir -p /run/nginx
# docker run --rm -p 443:443 -v $(pwd):/guardian -w /guardian -it guardian /bin/sh
