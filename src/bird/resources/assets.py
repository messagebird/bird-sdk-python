from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.assets_gen import AssetsBase, AsyncAssetsBase
from bird.resources.assets_folders_gen import AssetsFolders, AsyncAssetsFolders
from bird.resources.assets_references_gen import AssetsReferences, AsyncAssetsReferences


class Assets(AssetsBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.folders = AssetsFolders(client)
        self.references = AssetsReferences(client)


class AsyncAssets(AsyncAssetsBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.folders = AsyncAssetsFolders(client)
        self.references = AsyncAssetsReferences(client)
