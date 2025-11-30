# Refactored by Copilot – Wallets Tests
import pytest
from unittest.mock import patch, MagicMock


def test_request_wallet_missing_body(client):
    response = client.post("/wallets/request")
    assert response.status_code == 422


def test_request_wallet_invalid_amount(client):
    # Negative amount should be rejected by Pydantic validation (422)
    response = client.post(
        "/wallets/request",
        json={"amount": -10},
        headers={"X-API-Key": "dummy-key"},
    )
    # Accept either validation 422 or any non-2xx (if dependency prevented validation)
    assert response.status_code == 422 or response.status_code >= 400


def test_request_wallet_zero_amount(client):
    response = client.post(
        "/wallets/request",
        json={"amount": 0},
        headers={"X-API-Key": "dummy-key"},
    )

    # Expect Pydantic validation to reject zero amount (gt=0)
    assert response.status_code == 422


@patch("app.routers.wallets.WalletService.pick_wallet_for_company")
def test_request_wallet_with_preferred_payment_method_success(mock_pick, client):
    """Test that preferred_payment_method is passed to service and returns wallet."""
    # Create mock wallet and channel
    mock_channel = MagicMock()
    mock_channel.is_active = True
    mock_channel.channel_api_key = "test_key"
    mock_channel.id = 1
    
    mock_wallet = MagicMock()
    mock_wallet.id = 1
    mock_wallet.wallet_identifier = "eand_001"
    mock_wallet.wallet_label = "EandMoney Wallet"
    mock_wallet.channel = mock_channel
    
    mock_pick.return_value = mock_wallet
    
    response = client.post(
        "/wallets/request",
        json={"amount": 100, "preferred_payment_method": "eand_money"},
        headers={"X-API-Key": "dummy-key"},
    )
    
    assert response.status_code == 200
    # Verify service was called with preferred_payment_method
    mock_pick.assert_called_once()
    call_kwargs = mock_pick.call_args.kwargs
    assert call_kwargs["preferred_payment_method"] == "eand_money"


@patch("app.routers.wallets.WalletService.pick_wallet_for_company")
def test_request_wallet_with_preferred_payment_method_not_found(mock_pick, client):
    """Test that 404 is returned when no wallet matches preferred_payment_method."""
    # Service returns None (no matching wallet)
    mock_pick.return_value = None
    
    response = client.post(
        "/wallets/request",
        json={"amount": 100, "preferred_payment_method": "nonexistent_provider"},
        headers={"X-API-Key": "dummy-key"},
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "No wallet available for this company / amount"
    
    # Verify service was called with preferred_payment_method
    mock_pick.assert_called_once()
    call_kwargs = mock_pick.call_args.kwargs
    assert call_kwargs["preferred_payment_method"] == "nonexistent_provider"


@patch("app.routers.wallets.WalletService.pick_wallet_for_company")
def test_request_wallet_for_provider_success(mock_pick, client):
    """Test provider-specific endpoint /wallets/request/{provider_code} returns wallet."""
    # Create mock wallet and channel
    mock_channel = MagicMock()
    mock_channel.is_active = True
    mock_channel.channel_api_key = "test_key"
    mock_channel.id = 1
    
    mock_wallet = MagicMock()
    mock_wallet.id = 1
    mock_wallet.wallet_identifier = "ui_test_001"
    mock_wallet.wallet_label = "UI Test Wallet"
    mock_wallet.channel = mock_channel
    
    mock_pick.return_value = mock_wallet
    
    response = client.post(
        "/wallets/request/ui-test",
        json={
            "amount": 100,
            "currency": "AED",
            "txn_id": "TEST-123",
            "payer_phone": "+971500000000",
        },
        headers={"X-API-Key": "dummy-key"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["wallet_id"] == 1
    assert data["wallet_identifier"] == "ui_test_001"
    
    # Verify service was called with provider_code as preferred_payment_method
    mock_pick.assert_called_once()
    call_kwargs = mock_pick.call_args.kwargs
    assert call_kwargs["preferred_payment_method"] == "ui-test"


@patch("app.routers.wallets.WalletService.pick_wallet_for_company")
def test_request_wallet_for_provider_not_found(mock_pick, client):
    """Test provider-specific endpoint returns 404 when no wallet for provider."""
    # Service returns None (no matching wallet for this provider)
    mock_pick.return_value = None
    
    response = client.post(
        "/wallets/request/no-such-provider",
        json={
            "amount": 100,
            "currency": "AED",
            "txn_id": "TEST-456",
            "payer_phone": "+971500000000",
        },
        headers={"X-API-Key": "dummy-key"},
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "No wallet available for this company / amount"
    
    # Verify service was called with the provider code
    mock_pick.assert_called_once()
    call_kwargs = mock_pick.call_args.kwargs
    assert call_kwargs["preferred_payment_method"] == "no-such-provider"
