from typing import List, Optional

from pyparsing import Any
from .base import OmniBase


class Omni(OmniBase):

    async def get(self, key: str, actor=None) -> Optional[str]: ...

    async def set(self, key: str, value: Any, nx: bool = False,
                  ttl: Optional[int] = None, actor=None) -> Optional[list]: ...

    async def delete(self, key: str, actor=None) -> Optional[list]: ...

    async def keys(self, pattern: str = "*", actor=None) -> List[str]: ...

    async def exists(self, key: str, actor=None) -> bool: ...

    def __init__(self, session=None, policy=None, **kwargs):
        # Initialize with enhanced Omni base
        super().__init__(session=session, policy=policy, **kwargs)

    async def initialize(self, **kwargs):
        """
        Initialize the object with the given keyword arguments.
        This method should be implemented by subclasses to perform any necessary initialization.
        """
        raise NotImplementedError(
            "Subclasses must implement initialize method")

    async def destroy(self) -> bool:
        """
        Destroy the current state of the object by removing it from storage.
        Uses Redis DEL to remove the hash and all associated data.
        """
        # Check if we have a storage backend via session
        storage = getattr(self.session, 'storage',
                          None) if self.session else None
        if not storage:
            return False

        try:
            # Get omni identifier
            omni_id = getattr(self, '_omni_id', f"omni:{id(self)}")

            # Get identity for audit
            identity_id = None
            if self.session and hasattr(self.session, 'identity') and self.session.identity:
                identity_id = getattr(
                    self.session.identity, 'identity_id', None)

            # Use Redis client directly to delete the hash
            if hasattr(storage, '_ocean__redis_client') and storage._ocean__redis_client:
                # Get the Redis key for this omni
                if hasattr(storage, '_omni_key'):
                    key = storage._omni_key(omni_id)
                else:
                    key = f"{getattr(storage, 'storage_root', 'plantangenet')}:omni:{omni_id}"

                # Delete the main hash
                deleted = await storage._ocean__redis_client.delete(key)

                # Also clean up related keys (versions, relationships, audit logs)
                cleanup_keys = [
                    f"{key}:versions",
                    f"{key}:children",
                    f"{key}:parents",
                    f"{getattr(storage, 'storage_root', 'plantangenet')}:audit:{omni_id}"
                ]
                await storage._ocean__redis_client.delete(*cleanup_keys)

                # Log the destruction
                if hasattr(storage, 'log_omni_audit'):
                    await storage.log_omni_audit(
                        omni_id=omni_id,
                        action="destroy",
                        identity_id=identity_id,
                        context={"deleted_keys": deleted}
                    )

                return deleted > 0

            return False

        except Exception as e:
            # Log error if logger is available
            print(f"Warning: Failed to destroy omni: {e}")
            return False
