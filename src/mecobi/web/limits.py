"""Bound request bodies before JSON decoding, including chunked uploads."""

from fastapi.responses import JSONResponse


class BodySizeLimit:
    def __init__(self, app, max_bytes):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        limit = self.max_bytes()
        headers = dict(scope.get("headers", []))
        length = headers.get(b"content-length", b"")

        async def reject():
            response = JSONResponse(
                {"detail": f"Request body too large (max {limit} bytes)."}, status_code=413)
            await response(scope, receive, send)

        if length.isdigit() and int(length) > limit:
            return await reject()
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > limit:
                return await reject()
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)
