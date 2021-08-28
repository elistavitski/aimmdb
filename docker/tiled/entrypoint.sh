#!/usr/bin/env bash

cp /secrets/tiled-auth.yml /deploy/config/
/app/docker/check_config.py && exec gunicorn --config /app/docker/gunicorn_config.py
