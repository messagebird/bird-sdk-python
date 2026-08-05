# The first send a customer makes from the dashboard's onboarding step. Unlike
# quickstart-email.py this carries the key inline: the dashboard fills it with
# the workspace's real key, so the placeholder is what a reader sees before it
# is substituted, not advice to hardcode a secret.
from bird import APIError, Bird

with Bird(api_key="bk_XXXXXXXXXXXXXXXXXXXXXXXX") as client:
    try:
        message = client.email.send(
            from_={"email": "onboarding@messagebird.dev", "name": "Bird"},
            to=["delivered@messagebird.dev"],
            subject="Hello World",
            html="<p>You made your <strong>first email fly</strong>. Congratulations!</p>",
        )
        print(message.id, message.status)
    except APIError as err:
        print("send failed:", err)
