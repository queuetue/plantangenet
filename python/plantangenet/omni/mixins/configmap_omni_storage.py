# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from .omni_storage import OmniStorageMixin


class K8sConfigMapOmniStorage(OmniStorageMixin):
    """
    In-memory implementation of OmniStorageMixin with Kubernetes ConfigMap persistence.
    Uses ConfigMaps in a specified namespace to store omni objects.
    """

    def __init__(self, k8s_api: str, namespace: str = "default"):
        self.k8s_api = k8s_api.rstrip("/")
        self.namespace = namespace
        self.memory_store: Dict[str, Dict[str, Any]] = {}
        self.version_log: Dict[str, List[Dict[str, Any]]] = {}

    def _configmap_url(self, name: str) -> str:
        return f"{self.k8s_api}/api/v1/namespaces/{self.namespace}/configmaps/{name}"

    def _configmap_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        return {k: json.dumps(v) for k, v in data.items()}

    def _digest(self, data: bytes) -> str:
        import hashlib
        return "sha256:" + hashlib.sha256(data).hexdigest()

    async def store_omni_structured(
        self,
        omni_id: str,
        fields: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        identity_id: Optional[str] = None
    ) -> bool:
        self.memory_store.setdefault(omni_id, {}).update(fields)
        return True

    async def load_omni_structured(
        self,
        omni_id: str,
        field_names: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        omni = self.memory_store.get(omni_id)
        if not omni:
            return None
        if field_names:
            return {k: omni.get(k) for k in field_names if k in omni}
        return dict(omni)

    async def update_omni_fields(
        self,
        omni_id: str,
        dirty_fields: Dict[str, Any],
        identity_id: Optional[str] = None
    ) -> bool:
        return await self.store_omni_structured(omni_id, dirty_fields, identity_id=identity_id)

    async def store_omni_version(
        self,
        omni_id: str,
        version_data: Any,
        timestamp: Optional[float] = None
    ) -> str:
        name = f"omni-{omni_id}"
        ts = timestamp or time.time()
        version_id = f"v-{int(ts * 1000)}"

        configmap_payload = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": name},
            "data": self._configmap_data({version_id: version_data})
        }

        async with aiohttp.ClientSession() as session:
            url = self._configmap_url(name)
            headers = {"Content-Type": "application/json"}
            async with session.get(url) as resp:
                if resp.status == 200:
                    existing = await resp.json()
                    configmap_payload["data"].update(existing.get("data", {}))
                    async with session.put(url, headers=headers, data=json.dumps(configmap_payload)) as r:
                        if r.status not in (200, 201):
                            raise Exception(await r.text())
                else:
                    async with session.post(
                        f"{self.k8s_api}/api/v1/namespaces/{self.namespace}/configmaps",
                        headers=headers,
                        data=json.dumps(configmap_payload)) as r:
                        if r.status not in (200, 201):
                            raise Exception(await r.text())

        self.version_log.setdefault(omni_id, []).append({
            "version_id": version_id,
            "timestamp": ts
        })

        return version_id

    async def load_omni_version(
        self,
        omni_id: str,
        version_id: Optional[str] = None
    ) -> Optional[Any]:
        name = f"omni-{omni_id}"
        async with aiohttp.ClientSession() as session:
            url = self._configmap_url(name)
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                configmap = await resp.json()
                data = configmap.get("data", {})

        if not data:
            return None

        if version_id:
            blob = data.get(version_id)
        else:
            versions = self.version_log.get(omni_id, [])
            if not versions:
                return None
            latest_id = versions[-1]["version_id"]
            blob = data.get(latest_id)

        return json.loads(blob) if blob else None

    async def list_omni_versions(
        self,
        omni_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        entries = self.version_log.get(omni_id, [])[-limit:]
        return [
            {
                "version_id": e["version_id"],
                "timestamp": e["timestamp"],
                "datetime": datetime.fromtimestamp(e["timestamp"]).isoformat()
            } for e in entries
        ]

    # Other OmniStorageMixin methods may be stubbed or left unimplemented as needed
