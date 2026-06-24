import os

from bird import APIError, APIStatusError, Bird
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

bird = Bird(api_key=os.environ["BIRD_API_KEY"])


async def welcome(request: Request):
    data = await request.json()
    try:
        message = bird.email.send(
            from_={"email": "onboarding@messagebird.dev", "name": "Bird"},
            to=[data["email"]],
            subject="Welcome to Bird",
            html="<p>You are in.</p>",
        )
        return JSONResponse({"sent": True, "id": message.id})
    except APIStatusError as err:
        return JSONResponse({"error": str(err)}, status_code=err.status_code)
    except APIError as err:
        return JSONResponse({"error": str(err)}, status_code=500)


app = Starlette(routes=[Route("/welcome", welcome, methods=["POST"])])
