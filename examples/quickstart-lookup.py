from bird import APIError, Bird

with Bird() as client:
    try:
        # What is this number? The base lookup always answers the country, the
        # serving network and a coarse line type, and it always bills once.
        number = client.lookup.phone_number(
            phone_number="+31612345678", type=["porting", "score"]
        )
        print(number.country_code, number.line_type)

        # Each requested property is billed only when it is delivered, so read
        # the status before the value. Anything but "ok" means "not answered".
        if number.score is not None and number.score.status == "ok":
            print("credibility", number.score.value)
        if number.porting is not None and number.porting.status == "ok":
            print("ported", number.porting.ported, number.porting.last_ported_at)

        # Is this address worth sending to? `result` is the field to decide on;
        # `delivery_confidence` is always present and comparable, which is what
        # makes it safe to fall back on when a new verdict is added.
        address = client.lookup.email(email="aisha.khan@example.com")
        print(address.result, address.delivery_confidence)

        if address.result == "typo":
            print("did you mean", address.did_you_mean)
    except APIError as err:
        print("lookup failed:", err)
