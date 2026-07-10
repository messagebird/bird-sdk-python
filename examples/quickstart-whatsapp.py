from bird import APIError, Bird

with Bird() as client:
    try:
        message = client.whatsapp.send(
            to="+31612345678",
            template="bird_otp",
            language="en",
            components=[{"type": "body", "parameters": [{"type": "text", "text": "123456"}]}],
        )
        print(message.id, message.status)
    except APIError as err:
        print("send failed:", err)
