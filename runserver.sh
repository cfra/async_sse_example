#!/bin/sh

exec poetry run gunicorn \
	--bind 127.0.0.1:8000 \
	-k uvicorn.workers.UvicornWorker \
	project.asgi:application
