import os

from bird import APIError, APIStatusError, Bird
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

bird = Bird(api_key=os.environ["BIRD_API_KEY"])
app = FastAPI()


class WelcomeRequest(BaseModel):
    email: str


@app.post("/welcome")
async def welcome(body: WelcomeRequest):
    try:
        message = bird.email.send(
            from_={"email": "onboarding@messagebird.dev", "name": "Bird"},
            to=[body.email],
            subject="Welcome to Bird",
            html="<p>You are in.</p>",
        )
        return {"sent": True, "id": message.id}
    except APIStatusError as err:
        raise HTTPException(status_code=err.status_code, detail=str(err)) from err
    except APIError as err:
        raise HTTPException(status_code=500, detail=str(err)) from err
