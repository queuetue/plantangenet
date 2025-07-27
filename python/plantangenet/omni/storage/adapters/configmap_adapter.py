# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Kubernetes ConfigMap storage adapter implementation.

Provides Kubernetes ConfigMap backend support for the managed storage system
using the Kubernetes API for CRUD operations on ConfigMaps.
"""

import json
import time
from typing import Any, Dict, List, Optional

from kubernetes_asyncio import client, config

from ..backends import StorageBackend, BackendError, BackendConnectionError


class ConfigMapStorageAdapter(StorageBackend):
    """
    Kubernetes ConfigMap backend adapter for managed storage.
    
    Features:
    - Uses ConfigMaps for data storage
    - JSON serialization for complex data
    - Automatic name sanitization for Kubernetes DNS-1123 compliance
    - Namespace isolation
    - Label-based querying
    
    Example:
        adapter = ConfigMapStorageAdapter(namespace="plantangenet")
        storage.add_backend("configmap", adapter)
    """
    
    def __init__(self, namespace: str = "default", api_client=None):
        """
        Initialize ConfigMap adapter.
        
        Args:
            namespace: Kubernetes namespace for ConfigMaps
            api_client: Optional Kubernetes API client (will auto-configure if None)
        """
        self.namespace = namespace
        self.api_client = api_client
        self._core_v1 = None
    
    async def _get_api(self):
        """Get or create Kubernetes CoreV1Api client"""
        if not self._core_v1:
            if not self.api_client:
                try:
                    # Try in-cluster config first
                    await config.load_incluster_config()
                except config.ConfigException:
                    # Fall back to local kubeconfig
                    await config.load_kube_config()
            
            self._core_v1 = client.CoreV1Api(api_client=self.api_client)
        return self._core_v1
    
    def _configmap_name(self, key: str) -> str:
        """
        Convert key to valid ConfigMap name.
        
        Must be a valid DNS-1123 subdomain:
        - lowercase alphanumeric characters or '-'
        - start and end with alphanumeric
        - max 253 characters
        """
        # Replace invalid characters
        name = key.replace("/", "-").replace(":", "-").replace("_", "-").lower()
        
        # Remove any non-alphanumeric/dash characters
        name = "".join(c for c in name if c.isalnum() or c == "-")
        
        # Ensure starts with alphanumeric
        if name and not name[0].isalnum():
            name = "omni-" + name
        
        # Ensure not empty
        if not name:
            name = "unknown"
        
        # Ensure ends with alphanumeric
        while name and not name[-1].isalnum():
            name = name[:-1]
        
        # Truncate to max length
        return name[:253]
    
    async def store_data(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Store data in ConfigMap.
        
        Data is JSON-serialized and stored in ConfigMap.data fields.
        """
        try:
            api = await self._get_api()
            configmap_name = self._configmap_name(key)
            
            # Convert data to ConfigMap format (all values must be strings)
            configmap_data = {}
            for field_name, value in data.items():
                if isinstance(value, (dict, list)):
                    configmap_data[field_name] = json.dumps(value)
                else:
                    configmap_data[field_name] = str(value)
            
            # Create ConfigMap object
            configmap = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(
                    name=configmap_name,
                    labels={
                        "app": "plantangenet",
                        "type": "omni-storage",
                        "original-key": key[:63]  # Kubernetes label value limit
                    }
                ),
                data=configmap_data
            )
            
            try:
                # Try to update existing ConfigMap
                await api.patch_namespaced_config_map(
                    name=configmap_name,
                    namespace=self.namespace,
                    body=configmap
                )
            except client.ApiException as e:
                if e.status == 404:
                    # Create new ConfigMap
                    await api.create_namespaced_config_map(
                        namespace=self.namespace,
                        body=configmap
                    )
                else:
                    raise BackendError(f"Failed to store ConfigMap: {e}")
            
            return True
            
        except client.ApiException as e:
            raise BackendConnectionError(f"Kubernetes API error: {e}")
        except Exception as e:
            raise BackendError(f"Failed to store data in ConfigMap: {e}")
    
    async def load_data(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load data from ConfigMap.
        
        Deserializes JSON data back to original types.
        """
        try:
            api = await self._get_api()
            configmap_name = self._configmap_name(key)
            
            configmap = await api.read_namespaced_config_map(
                name=configmap_name,
                namespace=self.namespace
            )
            
            if not configmap.data:
                return None
            
            # Convert ConfigMap data back to original types
            result = {}
            for field_name, value in configmap.data.items():
                try:
                    # Try JSON parsing first
                    result[field_name] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    # Fall back to string
                    result[field_name] = value
            
            return result
            
        except client.ApiException as e:
            if e.status == 404:
                return None
            raise BackendConnectionError(f"Kubernetes API error: {e}")
        except Exception as e:
            raise BackendError(f"Failed to load data from ConfigMap: {e}")
    
    async def delete_data(self, key: str) -> bool:
        """Delete ConfigMap"""
        try:
            api = await self._get_api()
            configmap_name = self._configmap_name(key)
            
            await api.delete_namespaced_config_map(
                name=configmap_name,
                namespace=self.namespace
            )
            return True
            
        except client.ApiException as e:
            if e.status == 404:
                return True  # Already deleted
            raise BackendConnectionError(f"Kubernetes API error: {e}")
        except Exception as e:
            raise BackendError(f"Failed to delete ConfigMap: {e}")
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """
        List ConfigMaps with label selector.
        
        Returns ConfigMap names that match the prefix.
        """
        try:
            api = await self._get_api()
            
            # List ConfigMaps with our label selector
            configmaps = await api.list_namespaced_config_map(
                namespace=self.namespace,
                label_selector="app=plantangenet,type=omni-storage"
            )
            
            keys = []
            prefix_clean = self._configmap_name(prefix) if prefix else ""
            
            for cm in configmaps.items:
                if not prefix or cm.metadata.name.startswith(prefix_clean):
                    # Try to get original key from label, fall back to name
                    original_key = cm.metadata.labels.get("original-key", cm.metadata.name)
                    keys.append(original_key)
            
            return keys
            
        except client.ApiException as e:
            raise BackendConnectionError(f"Kubernetes API error: {e}")
        except Exception as e:
            raise BackendError(f"Failed to list ConfigMaps: {e}")
    
    async def store_version(self, key: str, version_id: str, data: Any) -> bool:
        """
        Store version as separate ConfigMap.
        
        Version ConfigMaps have names like: {sanitized_key}-versions-{version_id}
        """
        version_key = f"{key}-versions-{version_id}"
        version_data = {
            "data": json.dumps(data) if not isinstance(data, str) else data,
            "timestamp": str(time.time()),
            "version_id": version_id,
            "original_key": key
        }
        return await self.store_data(version_key, version_data)
    
    async def load_version(self, key: str, version_id: Optional[str] = None) -> Optional[Any]:
        """
        Load version data.
        
        If version_id is None, loads the latest version by timestamp.
        """
        if version_id:
            version_key = f"{key}-versions-{version_id}"
            data = await self.load_data(version_key)
            if data and "data" in data:
                try:
                    return json.loads(data["data"])
                except (json.JSONDecodeError, TypeError):
                    return data["data"]
        else:
            # Get latest version
            versions = await self.list_versions(key)
            if not versions:
                return None
            latest = max(versions, key=lambda v: v["timestamp"])
            return await self.load_version(key, latest["version_id"])
        
        return None
    
    async def list_versions(self, key: str) -> List[Dict[str, Any]]:
        """
        List versions for a key.
        
        Scans for version ConfigMaps and returns metadata.
        """
        try:
            version_prefix = f"{key}-versions-"
            all_keys = await self.list_keys(version_prefix)
            
            versions = []
            for configmap_key in all_keys:
                if configmap_key.startswith(version_prefix):
                    data = await self.load_data(configmap_key)
                    if data and "timestamp" in data and "version_id" in data:
                        timestamp = float(data["timestamp"])
                        versions.append({
                            "version_id": data["version_id"],
                            "timestamp": timestamp,
                            "datetime": time.strftime('%Y-%m-%dT%H:%M:%S', 
                                                    time.gmtime(timestamp))
                        })
            
            return sorted(versions, key=lambda v: v["timestamp"], reverse=True)
            
        except Exception as e:
            raise BackendError(f"Failed to list versions from ConfigMaps: {e}")
    
    async def health_check(self) -> bool:
        """Check Kubernetes API health"""
        try:
            api = await self._get_api()
            # Try to list ConfigMaps as a health check
            await api.list_namespaced_config_map(
                namespace=self.namespace,
                limit=1
            )
            return True
        except Exception:
            return False
    
    async def cleanup(self):
        """Cleanup API client"""
        if self.api_client:
            try:
                await self.api_client.close()
            except Exception:
                pass
