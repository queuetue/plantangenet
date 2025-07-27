# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Docker Registry storage adapter implementation.

Provides Docker Registry (OCI-compatible) backend support for the managed storage system
using registry v2 API for blob storage and manifests for metadata.
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional

import aiohttp

from ..backends import StorageBackend, BackendError, BackendConnectionError


class RegistryStorageAdapter(StorageBackend):
    """
    Docker Registry backend adapter for managed storage.
    
    Features:
    - Uses registry v2 API for blob storage
    - OCI image manifests for metadata
    - JSON serialization for data
    - Automatic tag name sanitization
    - Version storage as separate manifests
    
    Example:
        adapter = RegistryStorageAdapter("http://localhost:5000", "plantangenet/omni")
        storage.add_backend("registry", adapter)
    """
    
    def __init__(self, registry_url: str, repo: str = "omni"):
        """
        Initialize Registry adapter.
        
        Args:
            registry_url: Base URL of the Docker registry
            repo: Repository name for storing data
        """
        self.registry_url = registry_url.rstrip("/")
        self.repo = repo
    
    def _tag_name(self, key: str) -> str:
        """
        Convert key to valid Docker tag name.
        
        Docker tags must be lowercase and contain only [a-z0-9_.-].
        """
        # Replace invalid characters
        tag = key.replace("/", "-").replace(":", "-").lower()
        
        # Ensure it starts with alphanumeric
        if tag and not tag[0].isalnum():
            tag = "omni-" + tag
        
        # Ensure it's not empty
        if not tag:
            tag = "unknown"
        
        return tag
    
    def _digest(self, data: bytes) -> str:
        """Calculate SHA256 digest for blob"""
        return "sha256:" + hashlib.sha256(data).hexdigest()
    
    async def store_data(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Store data as OCI blob with manifest.
        
        Process:
        1. Serialize data to JSON
        2. Upload as blob to registry
        3. Create manifest referencing the blob
        4. Push manifest with tag
        """
        try:
            # Serialize data
            blob = json.dumps(data, separators=(",", ":"), sort_keys=True).encode()
            digest = self._digest(blob)
            tag = self._tag_name(key)
            
            async with aiohttp.ClientSession() as session:
                # Start blob upload
                start_url = f"{self.registry_url}/v2/{self.repo}/blobs/uploads/"
                async with session.post(start_url) as resp:
                    if resp.status != 202:
                        raise BackendConnectionError(f"Failed to start blob upload: {resp.status}")
                    location = resp.headers.get("Location")
                
                if not location:
                    raise BackendError("No upload location returned")
                
                # Complete blob upload
                upload_url = f"{location}&digest={digest}"
                async with session.put(upload_url, data=blob) as resp:
                    if resp.status != 201:
                        raise BackendError(f"Failed to upload blob: {resp.status}")
                
                # Create and push manifest
                manifest = {
                    "schemaVersion": 2,
                    "mediaType": "application/vnd.oci.image.manifest.v1+json",
                    "config": {
                        "mediaType": "application/vnd.omni.data.v1+json",
                        "size": len(blob),
                        "digest": digest
                    },
                    "layers": []
                }
                
                manifest_url = f"{self.registry_url}/v2/{self.repo}/manifests/{tag}"
                headers = {"Content-Type": "application/vnd.oci.image.manifest.v1+json"}
                async with session.put(manifest_url, headers=headers, 
                                     data=json.dumps(manifest)) as resp:
                    if resp.status != 201:
                        raise BackendError(f"Failed to push manifest: {resp.status}")
            
            return True
            
        except aiohttp.ClientError as e:
            raise BackendConnectionError(f"Registry connection error: {e}")
        except Exception as e:
            raise BackendError(f"Failed to store data in registry: {e}")
    
    async def load_data(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load data from registry manifest and blob.
        
        Process:
        1. Get manifest for tag
        2. Extract blob digest from manifest
        3. Download blob
        4. Deserialize JSON data
        """
        try:
            tag = self._tag_name(key)
            
            async with aiohttp.ClientSession() as session:
                # Get manifest
                manifest_url = f"{self.registry_url}/v2/{self.repo}/manifests/{tag}"
                headers = {"Accept": "application/vnd.oci.image.manifest.v1+json"}
                async with session.get(manifest_url, headers=headers) as resp:
                    if resp.status == 404:
                        return None
                    if resp.status != 200:
                        raise BackendError(f"Failed to get manifest: {resp.status}")
                    manifest = await resp.json()
                
                # Get blob digest
                digest = manifest.get("config", {}).get("digest")
                if not digest:
                    raise BackendError("No blob digest in manifest")
                
                # Download blob
                blob_url = f"{self.registry_url}/v2/{self.repo}/blobs/{digest}"
                async with session.get(blob_url) as resp:
                    if resp.status != 200:
                        raise BackendError(f"Failed to download blob: {resp.status}")
                    blob = await resp.read()
                    return json.loads(blob.decode())
            
        except aiohttp.ClientError as e:
            raise BackendConnectionError(f"Registry connection error: {e}")
        except json.JSONDecodeError as e:
            raise BackendError(f"Failed to deserialize data: {e}")
        except Exception as e:
            raise BackendError(f"Failed to load data from registry: {e}")
    
    async def delete_data(self, key: str) -> bool:
        """
        Delete manifest from registry.
        
        Note: Actual blob deletion depends on registry implementation
        and garbage collection policies.
        """
        try:
            tag = self._tag_name(key)
            
            async with aiohttp.ClientSession() as session:
                manifest_url = f"{self.registry_url}/v2/{self.repo}/manifests/{tag}"
                async with session.delete(manifest_url) as resp:
                    # 200/202 = deleted, 404 = already gone
                    return resp.status in [200, 202, 404]
                    
        except aiohttp.ClientError as e:
            raise BackendConnectionError(f"Registry connection error: {e}")
        except Exception as e:
            raise BackendError(f"Failed to delete data from registry: {e}")
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """
        List tags from registry, filtering by prefix.
        
        Returns tag names that match the prefix.
        """
        try:
            async with aiohttp.ClientSession() as session:
                tags_url = f"{self.registry_url}/v2/{self.repo}/tags/list"
                async with session.get(tags_url) as resp:
                    if resp.status != 200:
                        return []
                    result = await resp.json()
                    tags = result.get("tags", [])
                    
                    # Filter by prefix if provided
                    if prefix:
                        prefix_clean = self._tag_name(prefix)
                        tags = [tag for tag in tags if tag.startswith(prefix_clean)]
                    
                    return tags
                    
        except aiohttp.ClientError as e:
            raise BackendConnectionError(f"Registry connection error: {e}")
        except Exception as e:
            raise BackendError(f"Failed to list keys from registry: {e}")
    
    async def store_version(self, key: str, version_id: str, data: Any) -> bool:
        """
        Store version as separate manifest.
        
        Versions are stored with tags like: {key}-versions-{version_id}
        """
        version_key = f"{key}/versions/{version_id}"
        version_data = {
            "data": data,
            "timestamp": time.time(),
            "version_id": version_id
        }
        return await self.store_data(version_key, version_data)
    
    async def load_version(self, key: str, version_id: Optional[str] = None) -> Optional[Any]:
        """
        Load version data.
        
        If version_id is None, loads the latest version by timestamp.
        """
        if version_id:
            version_key = f"{key}/versions/{version_id}"
            data = await self.load_data(version_key)
            return data.get("data") if data else None
        else:
            # Get latest version by listing and sorting
            versions = await self.list_versions(key)
            if not versions:
                return None
            latest = max(versions, key=lambda v: v["timestamp"])
            return await self.load_version(key, latest["version_id"])
    
    async def list_versions(self, key: str) -> List[Dict[str, Any]]:
        """
        List versions for a key.
        
        Scans for version tags and returns metadata.
        """
        try:
            version_prefix = f"{key}/versions/"
            version_tags = await self.list_keys(version_prefix)
            
            versions = []
            for tag in version_tags:
                if tag.startswith(self._tag_name(version_prefix)):
                    # Extract version_id from tag
                    version_id = tag[len(self._tag_name(version_prefix)):]
                    
                    # Load version metadata
                    data = await self.load_data(f"{key}/versions/{version_id}")
                    if data and "timestamp" in data:
                        versions.append({
                            "version_id": version_id,
                            "timestamp": data["timestamp"],
                            "datetime": time.strftime('%Y-%m-%dT%H:%M:%S', 
                                                    time.gmtime(data["timestamp"]))
                        })
            
            return sorted(versions, key=lambda v: v["timestamp"], reverse=True)
            
        except Exception as e:
            raise BackendError(f"Failed to list versions from registry: {e}")
    
    async def health_check(self) -> bool:
        """Check registry health"""
        try:
            async with aiohttp.ClientSession() as session:
                health_url = f"{self.registry_url}/v2/"
                async with session.get(health_url) as resp:
                    return resp.status == 200
        except Exception:
            return False
