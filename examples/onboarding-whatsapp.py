from bird import APIError, Bird

with Bird(api_key="bk_XXXXXXXXXXXXXXXXXXXXXXXX") as client:
    try:
        message = client.whatsapp.send(
            to="+15551234567",
            template="bird_delivery_update",
            components=[
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "name": "ref", "text": "A1B2C3D4"},
                        {"type": "text", "name": "date", "text": "10 Jul 2026"},
                    ],
                }
            ],
        )
        print(message.id, message.status)
    except APIError as err:
        print("send failed:", err)
