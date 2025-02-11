import asyncio
import traceback

from adrf.viewsets import ViewSet
from django.http import StreamingHttpResponse
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response


class ServerSentEventRenderer(BaseRenderer):
    """
    Pass through StreamingHttpResponse unchanged.
    """
    media_type = 'text/event-stream'
    format = 'txt'
    def render(self, data, accepted_media_type=None, renderer_context=None):
        traceback.print_stack()
        response = StreamingHttpResponse(data, content_type='text/event-stream')
        response['X-Accel-Buffering'] = 'no'
        response['Cache-Control'] = 'no-cache'
        return response


async def example_events():
    for i in range(5):
        yield f"data: {i}\n\n"
        await asyncio.sleep(1)


class TestViewSet(ViewSet):
    renderer_classes = [ServerSentEventRenderer]

    async def list(self, request):
        return Response(example_events())


async def test_view(request):
    renderer = ServerSentEventRenderer()
    data = example_events()
    return renderer.render(data)
