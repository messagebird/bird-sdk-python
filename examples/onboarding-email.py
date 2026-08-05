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
