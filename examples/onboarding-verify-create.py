from bird import APIError, Bird

with Bird(api_key="bk_XXXXXXXXXXXXXXXXXXXXXXXX") as client:
    try:
        verification = client.verify.verifications.create(
            to={"email": "user@example.com"},
        )
        print(verification.id, verification.status)
    except APIError as err:
        print("could not start the verification:", err)
