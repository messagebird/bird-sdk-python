"""Example source for the generated workspace methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (workspace.get, workspace.quotas.list). Hand-written and
type-checked (pyright includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def workspace_get() -> None:
    workspace = client.workspace.get()
    print(workspace.id, workspace.name)


def workspace_quotas_list() -> None:
    quotas = client.workspace.quotas.list()
    for quota in quotas.data:
        print(quota.key, quota.limit, quota.organization_limit)
