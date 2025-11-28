from app.models.channel import Channel
from app.models.country import PaymentProvider


def test_channel_basic_fields_present():
    provider = PaymentProvider(code="eand_money", name="e& money")
    channel = Channel(
        channel_api_key="chan-key-123",
        telegram_group_id="-1001234567890",
        provider=provider,
        company_id=1,
        name="Test Channel",
    )

    assert channel.channel_api_key == "chan-key-123"
    assert channel.telegram_group_id == "-1001234567890"
    assert channel.provider is provider


def test_channel_optional_fields_can_be_none():
    channel = Channel(channel_api_key="chan-key-xyz", company_id=1, name="No Provider Channel")

    assert getattr(channel, "provider") is None
    assert hasattr(channel, "telegram_group_id")
    assert channel.telegram_group_id is None


def test_provider_has_channels_backref():
    provider = PaymentProvider(code="eand_money", name="e& money")
    c1 = Channel(provider=provider, channel_api_key="key1", company_id=1, name="C1")
    c2 = Channel(provider=provider, channel_api_key="key2", company_id=1, name="C2")

    assert len(provider.channels) == 2
    assert c1 in provider.channels and c2 in provider.channels
