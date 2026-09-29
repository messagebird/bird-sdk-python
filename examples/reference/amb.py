from bird import Bird

client = Bird()

def amb_business_accounts_delete() -> None:
    client.amb.business_accounts.delete('abz_01krdgeqcxet5s7t44vh8rt9mg')

def amb_business_accounts_reconnect() -> None:
    result = client.amb.business_accounts.reconnect('abz_01krdgeqcxet5s7t44vh8rt9mg')
    print(result)

def amb_business_accounts_events_list() -> None:
    result = client.amb.business_accounts.events.list('abz_01krdgeqcxet5s7t44vh8rt9mg', limit=20)
    print(result)

def amb_business_accounts_settings_get() -> None:
    result = client.amb.business_accounts.settings.get('abz_01krdgeqcxet5s7t44vh8rt9mg')
    print(result)

def amb_business_accounts_settings_update() -> None:
    result = client.amb.business_accounts.settings.update('abz_01krdgeqcxet5s7t44vh8rt9mg', brand_name='Acme Support', logo_asset_id=None)
    print(result)

def amb_business_accounts_submissions_list() -> None:
    result = client.amb.business_accounts.submissions.list('abz_01krdgeqcxet5s7t44vh8rt9mg', limit=2)
    print(result)

def amb_business_accounts_submissions_create() -> None:
    result = client.amb.business_accounts.submissions.create(
        'abz_01krdgeqcxet5s7t44vh8rt9mg',
        readiness_attachment_id='tca_01krdgeqcxet5s7t44vh8rt9mg',
        use_cases_attachment_id='tca_01krdgeqcxet5s7t44vh8rt9mh',
        video_attachment_id='tca_01krdgeqcxet5s7t44vh8rt9mj',
    )
    print(result)


def amb_business_accounts_get() -> None:
    result = client.amb.business_accounts.get('abz_01krdgeqcxet5s7t44vh8rt9mg')
    print(result)

def amb_business_accounts_update() -> None:
    result = client.amb.business_accounts.update('abz_01krdgeqcxet5s7t44vh8rt9mg', name='Acme Support')
    print(result)

def amb_business_accounts_list() -> None:
    result = client.amb.business_accounts.list(limit=2)
    print(result)

def amb_business_accounts_create() -> None:
    result = client.amb.business_accounts.create(name='Acme Retail', apple_business_id='b52d6267-2b62-4f8a-8842-0533d0f1dc07')
    print(result)

def amb_conversations_get() -> None:
    result = client.amb.conversations.get('acv_01krdgeqcxet5s7t44vh8rt9mg')
    print(result)

def amb_conversations_update() -> None:
    result = client.amb.conversations.update('acv_01krdgeqcxet5s7t44vh8rt9mg', assigned_to=None, labels=[], inbox_status="resolved")
    print(result)

def amb_conversations_list_messages() -> None:
    result = client.amb.conversations.list_messages('acv_01krdgeqcxet5s7t44vh8rt9mg', limit=2)
    print(result)

def amb_conversations_typing() -> None:
    result = client.amb.conversations.typing('acv_01krdgeqcxet5s7t44vh8rt9mg', event='typing_start')
    print(result)

def amb_conversations_list() -> None:
    result = client.amb.conversations.list(business_account_id='abz_01krdgeqcxet5s7t44vh8rt9mg', limit=2)
    print(result)

def amb_list_events() -> None:
    result = client.amb.list_events('amb_01krdgeqcxet5s7t44vh8rt9mg')
    print(result)

def amb_get() -> None:
    result = client.amb.get('amb_01krdgeqcxet5s7t44vh8rt9mg')
    print(result)

def amb_list() -> None:
    result = client.amb.list(business_account_id='abz_01krdgeqcxet5s7t44vh8rt9mg', limit=2)
    print(result)

def amb_send() -> None:
    result = client.amb.send(from_='b52d6267-2b62-4f8a-8842-0533d0f1dc07', to='opaque-customer', content={'type': 'text', 'body': 'Your order is ready.'})
    print(result)

def amb_routing_rules_get() -> None:
    result = client.amb.routing_rules.get('arr_01krdgeqcxet5s7t44vh8rt9mg')
    print(result)

def amb_routing_rules_update() -> None:
    result = client.amb.routing_rules.update('arr_01krdgeqcxet5s7t44vh8rt9mg', queue='sales', precedence=0, is_default=False)
    print(result)

def amb_routing_rules_delete() -> None:
    result = client.amb.routing_rules.delete('arr_01krdgeqcxet5s7t44vh8rt9mg')
    print(result)

def amb_routing_rules_list() -> None:
    result = client.amb.routing_rules.list(business_account_id='abz_01krdgeqcxet5s7t44vh8rt9mg')
    print(result)

def amb_routing_rules_create() -> None:
    result = client.amb.routing_rules.create(business_account_id='abz_01krdgeqcxet5s7t44vh8rt9mg', match_kind='intent', match_intent_id='support', queue='support', precedence=0, is_default=False, match_group_id=None)
    print(result)

def amb_stats_by_business() -> None:
    result = client.amb.stats.by_business(limit=2)
    print(result)

def amb_stats_by_category() -> None:
    result = client.amb.stats.by_category(limit=2)
    print(result)

def amb_stats_conversations_daily() -> None:
    result = client.amb.stats.conversations.daily()
    print(result)

def amb_stats_conversations_hourly() -> None:
    result = client.amb.stats.conversations.hourly()
    print(result)

def amb_stats_conversations_summary() -> None:
    result = client.amb.stats.conversations.summary()
    print(result)

def amb_stats_daily() -> None:
    result = client.amb.stats.daily(business_account_id='abz_01krdgeqcxet5s7t44vh8rt9mg')
    print(result)

def amb_stats_by_error_code() -> None:
    result = client.amb.stats.by_error_code(limit=2)
    print(result)

def amb_stats_by_group() -> None:
    result = client.amb.stats.by_group(limit=2)
    print(result)

def amb_stats_hourly() -> None:
    result = client.amb.stats.hourly(business_account_id='abz_01krdgeqcxet5s7t44vh8rt9mg')
    print(result)

def amb_stats_inbound_by_business() -> None:
    result = client.amb.stats.inbound.by_business(limit=2)
    print(result)

def amb_stats_inbound_daily() -> None:
    result = client.amb.stats.inbound.daily()
    print(result)

def amb_stats_inbound_hourly() -> None:
    result = client.amb.stats.inbound.hourly()
    print(result)

def amb_stats_inbound_by_intent() -> None:
    result = client.amb.stats.inbound.by_intent(limit=2)
    print(result)

def amb_stats_inbound_summary() -> None:
    result = client.amb.stats.inbound.summary()
    print(result)

def amb_stats_by_intent() -> None:
    result = client.amb.stats.by_intent(limit=2)
    print(result)

def amb_stats_by_message_kind() -> None:
    result = client.amb.stats.by_message_kind(limit=2)
    print(result)

def amb_stats_summary() -> None:
    result = client.amb.stats.summary(business_account_id='abz_01krdgeqcxet5s7t44vh8rt9mg')
    print(result)

def amb_stats_by_tag() -> None:
    result = client.amb.stats.by_tag(limit=2)
    print(result)

def amb_suppressions_get() -> None:
    result = client.amb.suppressions.get('asp_01krdgeqcxet5s7t44vh8rt9mg')
    print(result)

def amb_suppressions_delete() -> None:
    result = client.amb.suppressions.delete('asp_01krdgeqcxet5s7t44vh8rt9mg')
    print(result)

def amb_suppressions_list() -> None:
    result = client.amb.suppressions.list(business_account_id='abz_01krdgeqcxet5s7t44vh8rt9mg', limit=2)
    print(result)

def amb_suppressions_create() -> None:
    result = client.amb.suppressions.create(address='opaque-customer', address_type='opaque_user_id')
    print(result)
