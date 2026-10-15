from bird import Bird

client = Bird()
folder = client.assets.folders.create(name="Campaign images")
print(folder.id)
for asset in client.assets.list(kind="image"):
    print(asset.id, asset.url)
