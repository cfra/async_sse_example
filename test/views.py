import asyncio
import traceback

from adrf.viewsets import ViewSet
from django.http import StreamingHttpResponse
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response


class ServerSentEventResponse(StreamingHttpResponse):
    """
    A streamed response configured to send Server Sent Events.
    """
    def __init__(self, *args, **kwargs):
        kwargs['content_type'] = 'text/event-stream'
        super().__init__(*args, **kwargs)
        self['X-Accel-Buffering'] = 'no'
        self['Cache-Control'] = 'no-cache'


class ServerSentEventRenderer(BaseRenderer):
    """
    A renderer for server sent events. This renderer is just used for
    content negotiation, as the ServerSentEventResponse doesn't have
    a render function the renderer will never be called.
    """
    media_type = 'text/event-stream'
    format = 'txt'
    def render(self, data, accepted_media_type=None, renderer_context=None):
        assert False


async def example_events():
    for i in range(5):
        yield f"data: {i}\n\n"
        await asyncio.sleep(1)


class TestViewSet(ViewSet):
    renderer_classes = [ServerSentEventRenderer]

    async def list(self, request):
        return ServerSentEventResponse(example_events())


async def test_view(request):
    data = example_events()
    return ServerSentEventResponse(example_events())
