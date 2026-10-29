"""Example source for the generated workspace methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (workspace.get, workspace.rateLimits.list,
workspace.quotas.list). Hand-written and type-checked (pyright includes
examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def workspace_get() -> None:
    workspace = client.workspace.get()
    print(workspace.id, workspace.name)


def workspace_rate_limits_list() -> None:
    # Workspace limits matter with several workspaces, or one that kept a limit after a deletion.
    limits = client.workspace.rate_limits.list()
    for policy in limits.data:
        # Check usage.status first: workspace_remaining is also None when the
        # workspace has no limit of its own or its usage is not measured yet.
        print(policy.key, policy.limit, policy.usage.workspace_remaining)
def workspace_quotas_list() -> None:
    quotas = client.workspace.quotas.list()
    for quota in quotas.data:
        print(quota.key, quota.limit, quota.organization_limit)
