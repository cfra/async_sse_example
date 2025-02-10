# Reproduction repo for an async SSE issue in adrf

## Issue

I want to use [server sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) from django-adrf.

I am facing the problem that the events are not streamed, but buffered in the application and then sent as one batch.

Django is logging the following warning:

```
django/http/response.py:497: Warning: StreamingHttpResponse must consume asynchronous iterators in order to serve them synchronously. Use a synchronous iterator instead.
```

It seems to me like the response is evaluated in a sync context, because `StreamingHttpReponse` would not complain about an async iterator if it was running
in an async context, as can be seen when calling to the comparison URL test2.

## Installation and Setup

This example repository uses Poetry for package management and Gunicorn with Uvicorn as an ASGI server. If you have poetry installed you should be able to set up the project and run the test server using:

```console
poetry install
./runserver.sh
```

## Reproducing the issue

The issue can be observed here:

```console
curl -N http://127.0.0.1:8000/test/
```

The request will block for 5 seconds and then return 5 messages as once.

In contrast, correct operation can be observed here:

```console
curl -N http://127.0.0.1:8000/test2/
```

Here, each second a new message is showing up as expected.
