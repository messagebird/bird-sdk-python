from bird import APIError, Bird

with Bird() as client:
    try:
        message = client.whatsapp.send(
            to="+15551234567",
            template="bird_otp",
            language="en",
            parameters={"code": "123456"},
        )
        print(message.id, message.status)
    except APIError as err:
        print("send failed:", err)
