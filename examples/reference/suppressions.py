from bird import Bird

client = Bird()


def suppressions_list() -> None:
    for suppression in client.suppressions.list():
        print(suppression.email, suppression.reason)


def suppressions_get() -> None:
    suppression = client.suppressions.get("sup_abc123")
    print(suppression.reason, suppression.applies_to)


def suppressions_add() -> None:
    # Adding is idempotent, so an address that already carries a manual
    # suppression returns the existing record.
    suppression = client.suppressions.add(email="blocked@example.com")
    print(suppression.id)


def suppressions_remove() -> None:
    # An API key cannot remove a `complaint` record; those come off in the dashboard.
    client.suppressions.remove("sup_abc123")
