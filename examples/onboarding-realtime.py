import os

from bird import APIError, Bird

with Bird(
    api_key=os.environ["BIRD_API_KEY"],
    realtime_key="your-app-key",
    realtime_secret="your-app-secret",
) as client:
    try:
        client.realtime.publish(
            "rap_01krdgeqcxet5s7t44vh8rt9mg",
            event="order-updated",
            channels=["orders"],
            data={"id": 42, "status": "shipped"},
        )
        print("published to orders")
    except APIError as err:
        print("publish failed:", err)
