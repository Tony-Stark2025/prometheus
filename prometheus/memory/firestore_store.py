
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

logger = logging.getLogger('prometheus.memory.firestore')

class TenantIntegration(BaseModel):
    service: str
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class UserProfile(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    tenant_id: str = 'default_enterprise'
    roles: List[str] = Field(default_factory=lambda: ['lead'])
    org_scopes: List[str] = Field(default_factory=lambda: ['engineering', 'platform'])
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class FirestoreStore:
    _instance = None

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID', 'gen-lang-client-0942141479')
        self._db = None
        self._memory_cache: Dict[str, Dict[str, Any]] = {
            'users': {},
            'integrations': {},
            'blockers': {},
            'drafts': {}
        }
        self._init_client()

    def _init_client(self):
        try:
            if os.getenv('ENVIRONMENT') != 'testing':
                from google.cloud import firestore
                self._db = firestore.AsyncClient(project=self.project_id)
                logger.info(f'Initialized Firestore Async Client for project: {self.project_id}')
        except Exception as e:
            logger.warning(f'Firestore initialization fallback to in-memory store: {e}')
            self._db = None

    async def save_user(self, user: UserProfile) -> UserProfile:
        self._memory_cache['users'][user.user_id] = user.model_dump()
        if self._db:
            try:
                doc_ref = self._db.collection('users').document(user.user_id)
                await doc_ref.set(user.model_dump())
            except Exception as e:
                logger.warning(f'Failed to write user to Firestore: {e}')
        return user

    async def get_user(self, user_id: str) -> Optional[UserProfile]:
        if user_id in self._memory_cache['users']:
            return UserProfile(**self._memory_cache['users'][user_id])
        if self._db:
            try:
                doc_ref = self._db.collection('users').document(user_id)
                doc = await doc_ref.get()
                if doc.exists:
                    data = doc.to_dict()
                    self._memory_cache['users'][user_id] = data
                    return UserProfile(**data)
            except Exception as e:
                logger.warning(f'Failed to read user from Firestore: {e}')
        return None

    async def save_integration(self, tenant_id: str, service: str, config: Dict[str, Any]) -> TenantIntegration:
        integration = TenantIntegration(service=service, enabled=True, config=config)
        key = f'{tenant_id}:{service}'
        self._memory_cache['integrations'][key] = integration.model_dump()

        if self._db:
            try:
                doc_ref = self._db.collection('tenants').document(tenant_id).collection('integrations').document(service)
                await doc_ref.set(integration.model_dump())
            except Exception as e:
                logger.warning(f'Failed to write integration to Firestore: {e}')
        return integration

    async def get_integration(self, tenant_id: str, service: str) -> Optional[Dict[str, Any]]:
        key = f'{tenant_id}:{service}'
        if key in self._memory_cache['integrations']:
            return self._memory_cache['integrations'][key].get('config')

        if self._db:
            try:
                doc_ref = self._db.collection('tenants').document(tenant_id).collection('integrations').document(service)
                doc = await doc_ref.get()
                if doc.exists:
                    data = doc.to_dict()
                    self._memory_cache['integrations'][key] = data
                    return data.get('config')
            except Exception as e:
                logger.warning(f'Failed to read integration from Firestore: {e}')
        return None

    async def list_integrations(self, tenant_id: str) -> Dict[str, Dict[str, Any]]:
        result = {}
        for service in ['github', 'jira', 'slack']:
            cfg = await self.get_integration(tenant_id, service)
            if cfg:
                masked = {}
                for k, v in cfg.items():
                    if 'token' in k.lower() or 'secret' in k.lower() or 'key' in k.lower():
                        masked[k] = f'••••••••{str(v)[-4:]}' if len(str(v)) > 4 else '••••'
                    else:
                        masked[k] = v
                result[service] = {'connected': True, 'config': masked}
            else:
                result[service] = {'connected': False, 'config': {}}
        return result

    async def delete_integration(self, tenant_id: str, service: str) -> bool:
        key = f'{tenant_id}:{service}'
        if key in self._memory_cache['integrations']:
            del self._memory_cache['integrations'][key]

        if self._db:
            try:
                doc_ref = self._db.collection('tenants').document(tenant_id).collection('integrations').document(service)
                await doc_ref.delete()
            except Exception as e:
                logger.warning(f'Failed to delete integration in Firestore: {e}')
        return True

firestore_store = FirestoreStore()
