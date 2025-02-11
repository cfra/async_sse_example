# async SSE in adrf ViewSets

This repository provides a terse example how [server sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) can be sent with ASGI from django-adrf.

It started out as a reproduction repository for an issue where the events would be sent from a sync context, causing them all to be buffered and then sent all at once, instead of one by one.

The reason this was happening is the following:

DRF's `Response` inherits from Django's `SimpleTemplateResponse`. While DRF's `Response` implements its own `rendered_content` property, which then in turn calls the negotiated `Renderer`,
it keeps Django's `SimpleTemplateResponse.render` method, which is sync.

This means that although we are using adrf and Django's `_get_response_async` is used to process the viewset's view in an async context, the so called "deferred rendering" that is done
by `_get_response_async` will use the call `response = await sync_to_async(response.render, thread_sensitive=True)()` to render the response, causing the renderer to be called in a sync
context and blocking all other execution that also depends on a renderer.

We can work around this by just returning a subclass of `StreamingHttpResponse` directly, as it doesn't have a `render` method, indicating that it does not support "deferred rendering", thereby skipping this problematic step.

As a future improvement, some thought could be put into whether adrf should implement its own `Response` that provides an `async` implemention of derred rendering, so that adrf views are dispatched in a completely async fashion and are not rendered in a sync context, blocking each other waiting on a single thread.

If you want to learn more about the issue I was facing and how it was debugged, feel free to explore this repository's history.
