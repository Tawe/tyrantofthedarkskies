"""Server I/O: WebSocket connection wrapper for MUD server."""


class WebSocketConnection:
    """Wrapper to make WebSocket connections work like socket connections."""

    def __init__(self, websocket, address, send_queue, loop=None):
        self.websocket = websocket
        self.address = address
        self.send_queue = send_queue
        self.loop = loop
        self._closed = False
        self._timeout = None

    def send(self, data):
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="replace")
        if not self._closed and self.send_queue is not None:
            try:
                if self.loop is not None:
                    self.loop.call_soon_threadsafe(self.send_queue.put_nowait, data)
                else:
                    self.send_queue.put_nowait(data)
            except Exception as e:
                print(f"Error queuing WebSocket message: {e}")
                self._closed = True

    def close(self):
        self._closed = True

    @property
    def closed(self):
        return self._closed
