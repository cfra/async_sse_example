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

## Observations

Dumping the stack from the function returning the `StreamedHttpResponse` we can see that the assumption is apparently correct:

While `/test2/` is evaluated completely async with the stack going up all the way through the ASGI until gunicorns main loop,
the stack of `/test/` paints quite a different picture. It is executed in a thread.

Stack of `/test2/` (what it should look like):

```
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/bin/gunicorn", line 8, in <module>
    sys.exit(run())
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/app/wsgiapp.py", line 66, in run
    WSGIApplication("%(prog)s [OPTIONS] [APP_MODULE]", prog=prog).run()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/app/base.py", line 235, in run
    super().run()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/app/base.py", line 71, in run
    Arbiter(self).run()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/arbiter.py", line 201, in run
    self.manage_workers()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/arbiter.py", line 570, in manage_workers
    self.spawn_workers()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/arbiter.py", line 641, in spawn_workers
    self.spawn_worker()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/arbiter.py", line 608, in spawn_worker
    worker.init_process()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/uvicorn/workers.py", line 75, in init_process
    super().init_process()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/workers/base.py", line 143, in init_process
    self.run()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/uvicorn/workers.py", line 107, in run
    return asyncio.run(self._serve())
  File "/usr/lib/python3.13/asyncio/runners.py", line 194, in run
    return runner.run(main)
  File "/usr/lib/python3.13/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
  File "/usr/lib/python3.13/asyncio/base_events.py", line 707, in run_until_complete
    self.run_forever()
  File "/usr/lib/python3.13/asyncio/base_events.py", line 678, in run_forever
    self._run_once()
  File "/usr/lib/python3.13/asyncio/base_events.py", line 2033, in _run_once
    handle._run()
  File "/usr/lib/python3.13/asyncio/events.py", line 89, in _run
    self._context.run(self._callback, *self._args)
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/django/core/handlers/asgi.py", line 185, in process_request
    response = await self.run_get_response(request)
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/django/core/handlers/asgi.py", line 244, in run_get_response
    response = await self.get_response_async(request)
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/django/core/handlers/base.py", line 162, in get_response_async
    response = await self._middleware_chain(request)
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/django/core/handlers/exception.py", line 42, in inner
    response = await get_response(request)
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/django/core/handlers/base.py", line 253, in _get_response_async
    response = await wrapped_callback(
  File "/home/user/coding/async_sse_example/test/views.py", line 40, in test_view
    return renderer.render(data)
  File "/home/user/coding/async_sse_example/test/views.py", line 17, in render
    traceback.print_stack()
```

Stack of `/test/` (what it actually looks like):

```
  File "/usr/lib/python3.13/threading.py", line 1012, in _bootstrap
    self._bootstrap_inner()
  File "/usr/lib/python3.13/threading.py", line 1041, in _bootstrap_inner
    self.run()
  File "/usr/lib/python3.13/threading.py", line 992, in run
    self._target(*self._args, **self._kwargs)
  File "/usr/lib/python3.13/concurrent/futures/thread.py", line 93, in _worker
    work_item.run()
  File "/usr/lib/python3.13/concurrent/futures/thread.py", line 59, in run
    result = self.fn(*self.args, **self.kwargs)
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/asgiref/sync.py", line 522, in thread_handler
    return func(*args, **kwargs)
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/django/template/response.py", line 114, in render
    self.content = self.rendered_content
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/rest_framework/response.py", line 74, in rendered_content
    ret = renderer.render(self.data, accepted_media_type, context)
  File "/home/user/coding/async_sse_example/test/views.py", line 17, in render
    traceback.print_stack()
```

So for some reason, part of `/test/`'s execution is dispatched into a thread, which is causing the observed issue.

Dumping the stack of all threads from `/test/`'s execution, we see, there are indeed two threads, one being the pool thread with the stack shown above, and the other thread being the main thread executing gunicorn and waiting in its event loop for the thread to finish:

```pdb
(Pdb) for th in threading.enumerate():
...     print(th)
...     traceback.print_stack(sys._current_frames()[th.ident])
...     print()
<_MainThread(MainThread, started 128623502097344)>
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/bin/gunicorn", line 8, in <module>
    sys.exit(run())
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/app/wsgiapp.py", line 66, in run
    WSGIApplication("%(prog)s [OPTIONS] [APP_MODULE]", prog=prog).run()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/app/base.py", line 235, in run
    super().run()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/app/base.py", line 71, in run
    Arbiter(self).run()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/arbiter.py", line 201, in run
    self.manage_workers()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/arbiter.py", line 570, in manage_workers
    self.spawn_workers()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/arbiter.py", line 641, in spawn_workers
    self.spawn_worker()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/arbiter.py", line 608, in spawn_worker
    worker.init_process()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/uvicorn/workers.py", line 75, in init_process
    super().init_process()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/workers/base.py", line 143, in init_process
    self.run()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/uvicorn/workers.py", line 107, in run
    return asyncio.run(self._serve())
  File "/usr/lib/python3.13/asyncio/runners.py", line 194, in run
    return runner.run(main)
  File "/usr/lib/python3.13/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
  File "/usr/lib/python3.13/asyncio/base_events.py", line 707, in run_until_complete
    self.run_forever()
  File "/usr/lib/python3.13/asyncio/base_events.py", line 678, in run_forever
    self._run_once()
  File "/usr/lib/python3.13/asyncio/base_events.py", line 1995, in _run_once
    event_list = self._selector.select(timeout)
  File "/usr/lib/python3.13/selectors.py", line 452, in select
    fd_event_list = self._selector.poll(timeout, max_ev)

<Pool thread dropped for brevity as it has been already been included above.>
```

Listing the tasks pending in the main thread event loop by "clever" introspection:

```pdb
(Pdb) import asyncio
(Pdb) import sys
(Pdb) import threading
(Pdb) main_thread = threading.enumerate()[0]
(Pdb) pending_tasks = list(asyncio.all_tasks(sys._current_frames()[main_thread.ident].f_back.f_back.f_back.f_back.f_locals['self']._loop))
(Pdb) print('\n'.join([ str(x) for x in pending_tasks]))
<Task pending name='Task-4' coro=<RequestResponseCycle.run_asgi() running at /home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/uvicorn/protocols/http/h11_impl.py:403> wait_for=<Future pending cb=[Task.task_wakeup()]> cb=[set.discard()]>
<Task pending name='Task-7' coro=<ASGIHandler.handle.<locals>.process_request() running at /home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/django/core/handlers/asgi.py:185> wait_for=<Future pending cb=[shield.<locals>._outer_done_callback() at /usr/lib/python3.13/asyncio/tasks.py:975, Task.task_wakeup()]> cb=[_wait.<locals>._on_completion() at /usr/lib/python3.13/asyncio/tasks.py:521]>
<Task pending name='Task-1' coro=<UvicornWorker._serve() running at /home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/uvicorn/workers.py:102> wait_for=<Future pending cb=[Task.task_wakeup()]> cb=[_run_until_complete_cb() at /usr/lib/python3.13/asyncio/base_events.py:181]>
<Task pending name='Task-6' coro=<ASGIHandler.listen_for_disconnect() running at /home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/django/core/handlers/asgi.py:235> wait_for=<Future pending cb=[Task.task_wakeup()]> cb=[_wait.<locals>._on_completion() at /usr/lib/python3.13/asyncio/tasks.py:521]>
b
```

The interesting task seems to be "Task-7" as this is the only task that is different in a comparison to the working case.

Dumping the stack of that task, we get:

```
(Pdb) asgi_task = [x for x in pending_tasks][1]
(Pdb) asgi_task.print_stack()
Stack for <Task pending name='Task-7' coro=<ASGIHandler.handle.<locals>.process_request() running at /home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/django/core/handlers/asgi.py:185> cb=[_wait.<locals>._on_completion() at /usr/lib/python3.13/asyncio/tasks.py:521]> (most recent call last):
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/bin/gunicorn", line 8, in <module>
    sys.exit(run())
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/app/wsgiapp.py", line 66, in run
    WSGIApplication("%(prog)s [OPTIONS] [APP_MODULE]", prog=prog).run()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/app/base.py", line 235, in run
    super().run()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/app/base.py", line 71, in run
    Arbiter(self).run()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/arbiter.py", line 201, in run
    self.manage_workers()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/arbiter.py", line 570, in manage_workers
    self.spawn_workers()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/arbiter.py", line 641, in spawn_workers
    self.spawn_worker()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/arbiter.py", line 608, in spawn_worker
    worker.init_process()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/uvicorn/workers.py", line 75, in init_process
    super().init_process()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/gunicorn/workers/base.py", line 143, in init_process
    self.run()
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/uvicorn/workers.py", line 107, in run
    return asyncio.run(self._serve())
  File "/usr/lib/python3.13/asyncio/runners.py", line 194, in run
    return runner.run(main)
  File "/usr/lib/python3.13/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
  File "/usr/lib/python3.13/asyncio/base_events.py", line 707, in run_until_complete
    self.run_forever()
  File "/usr/lib/python3.13/asyncio/base_events.py", line 678, in run_forever
    self._run_once()
  File "/usr/lib/python3.13/asyncio/base_events.py", line 2033, in _run_once
    handle._run()
  File "/usr/lib/python3.13/asyncio/events.py", line 89, in _run
    self._context.run(self._callback, *self._args)
  File "/home/user/.cache/pypoetry/virtualenvs/async-sse-example-DQzT8392-py3.13/lib/python3.13/site-packages/django/core/handlers/asgi.py", line 185, in process_request
    response = await self.run_get_response(request)
```
