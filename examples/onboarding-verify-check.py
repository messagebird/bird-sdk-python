from bird import APIError, Bird

with Bird(api_key="bk_XXXXXXXXXXXXXXXXXXXXXXXX") as client:
    try:
        result = client.verify.verifications.check(
            to={"email": "user@example.com"},
            code="123456",
        )
        print(result.success)
    except APIError as err:
        print("could not check the passcode:", err)
