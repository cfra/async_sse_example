#!/bin/sh

exec poetry run gunicorn \
	--bind 127.0.0.1:8000 \
	--reload \
	-t 86400 \
	-k uvicorn.workers.UvicornWorker \
	project.asgi:application
