"""Example source for the generated workspace method.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (workspace.get). Hand-written and type-checked (pyright
includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def workspace_get() -> None:
    workspace = client.workspace.get()
    print(workspace.id, workspace.name)
