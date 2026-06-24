import os

from bird import APIError, APIStatusError, Bird
from flask import Flask, jsonify, request

bird = Bird(api_key=os.environ["BIRD_API_KEY"])
app = Flask(__name__)


@app.post("/welcome")
def welcome():
    data = request.get_json()
    try:
        message = bird.email.send(
            from_={"email": "onboarding@messagebird.dev", "name": "Bird"},
            to=[data["email"]],
            subject="Welcome to Bird",
            html="<p>You are in.</p>",
        )
        return jsonify({"sent": True, "id": message.id})
    except APIStatusError as err:
        return jsonify({"error": str(err)}), err.status_code
    except APIError as err:
        return jsonify({"error": str(err)}), 500
