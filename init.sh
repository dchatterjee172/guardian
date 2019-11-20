source $HOME/.poetry/env
poetry install
poetry shell
guadian.ngnix.conf /etc/nginx/conf.d
ngnix -s reload
