import os

from bird import Bird

client = Bird(api_key=os.environ["BIRD_MASTER_KEY"])


def organization_workspaces_create() -> None:
    workspace = client.organization.workspaces.create(name="Staging")
    print(workspace.id)


def organization_workspaces_list() -> None:
    for workspace in client.organization.workspaces.list(name="Staging"):
        print(workspace.id, workspace.name)


def organization_workspaces_get() -> None:
    workspace = client.organization.workspaces.get("ws_01krdgeqcxet5s7t44vh8rt9mg")
    print(workspace.name)


def organization_workspaces_update() -> None:
    workspace = client.organization.workspaces.update("ws_01krdgeqcxet5s7t44vh8rt9mg", name="Production")
    print(workspace.name)


def organization_workspaces_delete() -> None:
    client.organization.workspaces.delete("ws_01krdgeqcxet5s7t44vh8rt9mg")


def organization_workspaces_whatsapp_numbers_create() -> None:
    number = client.organization.workspaces.whatsapp_numbers.create(
        "ws_01krdgeqcxet5s7t44vh8rt9mg",
        waba="102290129340398",
        meta_phone_number_id="109364591979012",
        name="Northwind Support",
    )
    print(number.id, number.status)
