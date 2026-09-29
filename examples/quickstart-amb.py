import os

from bird import Bird

with Bird() as client:
    conversation = client.amb.conversations.get(os.environ["AMB_CONVERSATION_ID"])
    business = client.amb.business_accounts.get(conversation.business_account_id)
    if business.status == "disconnected" or conversation.status != "open" or not business.apple_business_id or not conversation.opaque_user_id:
        raise ValueError("A configured, connected business account and an open conversation are required.")
    message = client.amb.send(
        from_=business.apple_business_id,
        to=conversation.opaque_user_id,
        content={"type": "text", "body": "Your order is ready."},
    )
    print(message.id)
    print(client.amb.list_events(message.id))
