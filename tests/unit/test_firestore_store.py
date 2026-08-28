
import pytest
from prometheus.memory.firestore_store import FirestoreStore, UserProfile

@pytest.mark.asyncio
async def test_firestore_store_user_and_integration_lifecycle():
    store = FirestoreStore()
    
    # Save user
    user = UserProfile(
        user_id='test_user_01',
        email='test.lead@enterprise.io',
        name='Test Lead',
        tenant_id='tenant_acme',
        roles=['lead'],
        org_scopes=['engineering', 'platform']
    )
    saved_user = await store.save_user(user)
    assert saved_user.user_id == 'test_user_01'
    
    # Get user
    fetched_user = await store.get_user('test_user_01')
    assert fetched_user is not None
    assert fetched_user.email == 'test.lead@enterprise.io'
    assert fetched_user.tenant_id == 'tenant_acme'
    
    # Save integration
    saved_gh = await store.save_integration(
        tenant_id='tenant_acme',
        service='github',
        config={'token': 'ghp_secret12345', 'repos': ['acme/repo1']}
    )
    assert saved_gh.service == 'github'
    
    # List integrations with masking
    integrations = await store.list_integrations('tenant_acme')
    assert integrations['github']['connected'] is True
    assert '••••' in integrations['github']['config']['token']
    assert integrations['jira']['connected'] is False
    
    # Delete integration
    await store.delete_integration('tenant_acme', 'github')
    integrations_after = await store.list_integrations('tenant_acme')
    assert integrations_after['github']['connected'] is False
