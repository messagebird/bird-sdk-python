from bird import APIError, Bird

with Bird(api_key="bk_XXXXXXXXXXXXXXXXXXXXXXXX") as client:
    try:
        message = client.sms.send(
            to="+14155550100",
            template="bird_otp_verification",
            parameters={"code": "493021"},
        )
        print(message.id, message.status)
    except APIError as err:
        print("send failed:", err)
