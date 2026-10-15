from bird import Bird

client = Bird()


def assets_list() -> None:
    for asset in client.assets.list(kind="image"):
        print(asset.id, asset.url)


def assets_get() -> None:
    asset = client.assets.get("ast_01krdgeqcxet5s7t44vh8rt9mg")
    print(asset.url)


def assets_update() -> None:
    asset = client.assets.update("ast_01krdgeqcxet5s7t44vh8rt9mg", name="Summer banner")
    print(asset.name)


def assets_delete() -> None:
    client.assets.delete("ast_01krdgeqcxet5s7t44vh8rt9mg")


def assets_references_list() -> None:
    references = client.assets.references.list("ast_01krdgeqcxet5s7t44vh8rt9mg")
    print(references.data, references.truncated)


def assets_folders_create() -> None:
    folder = client.assets.folders.create(name="Campaign images")
    print(folder.id)


def assets_folders_list() -> None:
    for folder in client.assets.folders.list():
        print(folder.id, folder.path)


def assets_folders_get() -> None:
    folder = client.assets.folders.get("asf_01krdgeqcxet5s7t44vh8rt9mg")
    print(folder.path)


def assets_folders_update() -> None:
    folder = client.assets.folders.update("asf_01krdgeqcxet5s7t44vh8rt9mg", name="Autumn campaign")
    print(folder.path)


def assets_folders_delete() -> None:
    client.assets.folders.delete("asf_01krdgeqcxet5s7t44vh8rt9mg")
