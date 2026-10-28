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
