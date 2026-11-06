from bird import APIError, Bird

with Bird(api_key="bk_XXXXXXXXXXXXXXXXXXXXXXXX") as client:
    try:
        message = client.whatsapp.send(
            to="+15551234567",
            template="bird_delivery_update",
            parameters={"ref": "A1B2C3D4", "date": "10 Jul 2026"},
        )
        print(message.id, message.status)
    except APIError as err:
        print("send failed:", err)
