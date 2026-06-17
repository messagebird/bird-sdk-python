from bird import APIError, Bird

with Bird() as client:
    try:
        message = client.email.send(
            from_={"email": "onboarding@messagebird.dev", "name": "Bird"},
            to=["delivered@messagebird.dev"],
            subject="Hello from Bird",
            html="<p>My first Bird email.</p>",
        )
        print(message.id, message.status)
    except APIError as err:
        print("send failed:", err)
