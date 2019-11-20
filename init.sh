cp guadian.ngnix.conf /etc/nginx/conf.d/
nginx -g 'pid /run/nginx/nginx.pid;'
nginx -s reload
source $HOME/.poetry/env
poetry install
poetry shell
