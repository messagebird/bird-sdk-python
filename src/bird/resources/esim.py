from bird._base_client import AsyncAPIClient, SyncAPIClient
from bird.resources.esim_gen import AsyncEsimBase, EsimBase
from bird.resources.esim_assignment_gen import AsyncEsimAssignmentResource, EsimAssignmentResource
from bird.resources.esim_credentials_gen import AsyncEsimCredentialsResource, EsimCredentialsResource
from bird.resources.esim_deliveries_gen import AsyncEsimDeliveries, EsimDeliveries
from bird.resources.esim_install_links_gen import AsyncEsimInstallLinks, EsimInstallLinks
from bird.resources.esim_offers_gen import AsyncEsimOffers, EsimOffers
from bird.resources.esim_orders_gen import AsyncEsimOrders, EsimOrders
from bird.resources.esim_packages_gen import AsyncEsimPackages, EsimPackages
from bird.resources.esim_recurring_subscriptions_gen import AsyncEsimRecurringSubscriptions, EsimRecurringSubscriptions
from bird.resources.esim_settings_gen import AsyncEsimSettingsResource, EsimSettingsResource
from bird.resources.esim_subscribers_gen import AsyncEsimSubscribers, EsimSubscribers
from bird.resources.esim_zones_gen import AsyncEsimZones, EsimZones


class Esim(EsimBase):
    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.assignment = EsimAssignmentResource(client)
        self.credentials = EsimCredentialsResource(client)
        self.deliveries = EsimDeliveries(client)
        self.install_links = EsimInstallLinks(client)
        self.offers = EsimOffers(client)
        self.orders = EsimOrders(client)
        self.packages = EsimPackages(client)
        self.recurring_subscriptions = EsimRecurringSubscriptions(client)
        self.settings = EsimSettingsResource(client)
        self.subscribers = EsimSubscribers(client)
        self.zones = EsimZones(client)


class AsyncEsim(AsyncEsimBase):
    def __init__(self, client: AsyncAPIClient) -> None:
        super().__init__(client)
        self.assignment = AsyncEsimAssignmentResource(client)
        self.credentials = AsyncEsimCredentialsResource(client)
        self.deliveries = AsyncEsimDeliveries(client)
        self.install_links = AsyncEsimInstallLinks(client)
        self.offers = AsyncEsimOffers(client)
        self.orders = AsyncEsimOrders(client)
        self.packages = AsyncEsimPackages(client)
        self.recurring_subscriptions = AsyncEsimRecurringSubscriptions(client)
        self.settings = AsyncEsimSettingsResource(client)
        self.subscribers = AsyncEsimSubscribers(client)
        self.zones = AsyncEsimZones(client)
