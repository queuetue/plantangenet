# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

import aiohttp
import hashlib
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from .omni_storage import OmniStorageMixin


class InMemoryRegistryOmniStorage(OmniStorageMixin):
    """
    In-memory implementation of OmniStorageMixin with Registry v2 persistence layer.
    Pushes infrequently to a remote Docker registry (OCI-compatible).
    """

    def __init__(self, registry_url: str, repo: str = "omni"):
        self.registry_url = registry_url.rstrip("/")
        self.repo = repo
        self.memory_store: Dict[str, Dict[str, Any]] = {}
        self.version_log: Dict[str, List[Dict[str, Any]]] = {}

    def _digest(self, data: bytes) -> str:
        return "sha256:" + hashlib.sha256(data).hexdigest()

    async def store_omni_structured(
        self,
        omni_id: str,
        fields: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        identity_id: Optional[str] = None
    ) -> bool:
        if omni_id not in self.memory_store:
            self.memory_store[omni_id] = {}
        self.memory_store[omni_id].update(fields)
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
        blob = json.dumps(version_data, separators=(",", ":"), sort_keys=True).encode()
        digest = self._digest(blob)
        ts = timestamp or time.time()
        tag = f"{omni_id}-{int(ts)}"

        async with aiohttp.ClientSession() as session:
            start_url = f"{self.registry_url}/v2/{self.repo}/blobs/uploads/"
            async with session.post(start_url) as resp:
                loc = resp.headers.get("Location")

            if not loc:
                raise Exception("Failed to initiate blob upload")

            upload_url = f"{loc}&digest={digest}"
            async with session.put(upload_url, data=blob) as resp:
                if resp.status != 201:
                    raise Exception(f"Blob upload failed: {await resp.text()}")

            manifest = {
                "schemaVersion": 2,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "config": {
                    "mediaType": "application/vnd.omni.version.v1+json",
                    "size": len(blob),
                    "digest": digest
                },
                "layers": []
            }

            m_url = f"{self.registry_url}/v2/{self.repo}/manifests/{tag}"
            headers = {"Content-Type": "application/vnd.oci.image.manifest.v1+json"}
            async with session.put(m_url, headers=headers, data=json.dumps(manifest)) as resp:
                if resp.status != 201:
                    raise Exception(f"Manifest push failed: {await resp.text()}")

        if omni_id not in self.version_log:
            self.version_log[omni_id] = []

        self.version_log[omni_id].append({
            "version_id": tag,
            "timestamp": ts,
            "digest": digest
        })

        return tag

    async def load_omni_version(
        self,
        omni_id: str,
        version_id: Optional[str] = None
    ) -> Optional[Any]:
        tag = version_id
        if not tag:
            versions = self.version_log.get(omni_id, [])
            if not versions:
                return None
            tag = versions[-1]["version_id"]

        async with aiohttp.ClientSession() as session:
            m_url = f"{self.registry_url}/v2/{self.repo}/manifests/{tag}"
            headers = {"Accept": "application/vnd.oci.image.manifest.v1+json"}
            async with session.get(m_url, headers=headers) as resp:
                if resp.status != 200:
                    return None
                manifest = await resp.json()

            digest = manifest.get("config", {}).get("digest")
            if not digest:
                return None

            b_url = f"{self.registry_url}/v2/{self.repo}/blobs/{digest}"
            async with session.get(b_url) as resp:
                if resp.status != 200:
                    return None
                blob = await resp.read()
                return json.loads(blob.decode())

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

    # All other methods from OmniStorageMixin can be no-ops or raise NotImplementedError
    # or delegate to Redis-backed variant if combined in a hybrid class
