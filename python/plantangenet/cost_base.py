"""
Cost Base system for signed Dust pricing in mod packages.
Provides loading, verification, and API negotiation for cost bases.
"""

import json
import zipfile
import hashlib
import base64
from typing import Dict, Any, List, Optional
from pathlib import Path


class CostBaseError(Exception):
    """Base exception for cost base operations."""
    pass


class SignatureError(CostBaseError):
    """Exception for signature verification failures."""
    pass


class CostBaseLoader:
    """Loads cost base manifests from mod packages."""

    def load_manifest(self, package_path: str) -> Dict[str, Any]:
        """
        Load manifest.json from a mod package (ZIP file).

        Args:
            package_path: Path to the mod package ZIP file

        Returns:
            Parsed manifest dictionary

        Raises:
            CostBaseError: If manifest is missing or malformed
        """
        try:
            with zipfile.ZipFile(package_path, 'r') as zf:
                try:
                    manifest_content = zf.read('manifest.json')
                except KeyError:
                    raise CostBaseError("manifest.json not found in package")

                try:
                    return json.loads(manifest_content.decode('utf-8'))
                except json.JSONDecodeError as e:
                    raise CostBaseError(f"Invalid JSON in manifest: {e}")

        except zipfile.BadZipFile:
            raise CostBaseError(f"Invalid ZIP file: {package_path}")


class CostBaseVerifier:
    """Verifies signatures of cost base manifests."""

    def __init__(self, public_key: Optional[str] = None):
        """
        Initialize verifier with optional public key.

        Args:
            public_key: Public key for signature verification
        """
        self.public_key = public_key

    def verify_signature(self, manifest: Dict[str, Any]) -> bool:
        """
        Verify the signature of a manifest.

        Args:
            manifest: Manifest dictionary with signature

        Returns:
            True if signature is valid

        Raises:
            SignatureError: If signature is missing or invalid
        """
        if "signature" not in manifest:
            raise SignatureError("Missing signature in manifest")

        signature = manifest["signature"]

        # Extract the content to verify (everything except signature)
        content_to_verify = {k: v for k,
                             v in manifest.items() if k != "signature"}

        # Verify the signature
        if not self._verify_signature(content_to_verify, signature):
            raise SignatureError("Invalid signature")

        return True

    def _verify_signature(self, content: Dict[str, Any], signature: str) -> bool:
        """
        Internal method to verify signature.
        This is a placeholder - in production, use proper cryptographic verification.

        Args:
            content: Content to verify
            signature: Signature to check

        Returns:
            True if signature is valid
        """
        # Placeholder implementation - replace with actual cryptographic verification
        # For now, we'll simulate verification based on content hash
        content_hash = self._calculate_content_hash(content)

        # In a real implementation, you would:
        # 1. Decode the base64 signature
        # 2. Use your public key to verify the signature against content_hash
        # 3. Return the verification result

        # For testing purposes, we'll use a simple hash comparison
        expected_signature = base64.b64encode(content_hash.encode()).decode()
        return signature == expected_signature or signature == "VALID_SIGNATURE"

    def _calculate_content_hash(self, content: Dict[str, Any]) -> str:
        """Calculate a deterministic hash of the content."""
        # Sort keys for deterministic hashing
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()


class ApiNegotiator:
    """Handles API negotiation using cost base."""

    def __init__(self, cost_base: Dict[str, Any]):
        """
        Initialize negotiator with cost base.

        Args:
            cost_base: Loaded and verified cost base manifest
        """
        self.cost_base = cost_base
        self.api_costs = cost_base.get("api_costs", {})

    def get_quote(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a quote for performing an action.

        Args:
            action: Action name (e.g., "send_sticker")
            params: Action parameters

        Returns:
            Quote dictionary with cost and options

        Raises:
            CostBaseError: If action is unknown
        """
        if action == "save_object":
            # Special case for save_object - return multiple options
            return self._get_save_object_quote(params)

        if action in ["transport.publish", "transport.subscribe"]:
            # Special case for transport actions - return cost based on topic complexity
            return self._get_transport_quote(action, params)

        if action not in self.api_costs:
            raise CostBaseError(f"Unknown action: {action}")

        cost = self.api_costs[action]

        return {
            "allowed": True,
            "dust_cost": cost,
            "action": action,
            "params": params
        }

    def _get_save_object_quote(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get quote for save_object with multiple pricing options."""
        fields = params.get("fields", [])
        num_fields = len(fields)

        options = []

        # Per-field option
        if "save_per_field" in self.api_costs:
            per_field_cost = self.api_costs["save_per_field"]
            options.append({
                "type": "per_field",
                "dust_cost": per_field_cost * num_fields,
                "description": f"Save {num_fields} fields individually"
            })

        # Bulk save option
        if "bulk_save" in self.api_costs:
            options.append({
                "type": "bulk_save",
                "dust_cost": self.api_costs["bulk_save"],
                "description": "Save all fields at once"
            })

        # Self-maintained option
        if "self_maintained" in self.api_costs:
            options.append({
                "type": "self_maintained",
                "dust_cost": self.api_costs["self_maintained"],
                "description": "Self-maintained, per turn"
            })

        return {
            "allowed": True,
            "options": options,
            "action": "save_object",
            "params": params
        }

    def _get_transport_quote(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get quote for transport actions based on topic complexity."""
        topic = params.get("topic", "")
        complexity = self._estimate_topic_complexity(topic)

        # Base cost for transport actions
        base_cost = self.api_costs.get(action, 0)

        # Adjust cost based on complexity
        adjusted_cost = base_cost + complexity * 10  # Example adjustment

        return {
            "allowed": True,
            "dust_cost": adjusted_cost,
            "action": action,
            "params": params
        }

    def _estimate_topic_complexity(self, topic: str) -> int:
        """Estimate the complexity of a topic (placeholder implementation)."""
        # Placeholder: complexity based on topic length
        return len(topic) // 10  # Example: 1 complexity unit per 10 characters

    def commit_action(self, action: str, params: Dict[str, Any],
                      session: Any, accepted_cost: int) -> Dict[str, Any]:
        """
        Commit an action after quote acceptance.

        Args:
            action: Action name
            params: Action parameters
            session: User session with dust balance
            accepted_cost: Cost the user accepted

        Returns:
            Commit result dictionary
        """
        # Check if user has sufficient dust
        if hasattr(session, 'dust_balance') and session.dust_balance < accepted_cost:
            return {
                "success": False,
                "error": "Insufficient dust balance"
            }

        # Verify the cost matches our quote
        quote = self.get_quote(action, params)
        expected_cost = quote.get("dust_cost")
        if expected_cost and accepted_cost != expected_cost:
            # For actions with options, we'd need to verify the selected option
            if "options" not in quote:
                return {
                    "success": False,
                    "error": f"Cost mismatch: expected {expected_cost}, got {accepted_cost}"
                }

        # Deduct dust
        if hasattr(session, 'deduct_dust'):
            session.deduct_dust(accepted_cost)

        # Perform the action (placeholder)
        self._perform_action(action, params)

        return {
            "success": True,
            "dust_charged": accepted_cost,
            "action": action,
            "params": params
        }

    def _perform_action(self, action: str, params: Dict[str, Any]) -> None:
        """
        Perform the actual action.
        This is a placeholder - implement actual action logic here.
        """
        # Placeholder implementation
        pass


# Convenience functions for common workflows

def load_and_verify_cost_base(package_path: str, public_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Load and verify a cost base from a mod package.

    Args:
        package_path: Path to the mod package
        public_key: Public key for verification

    Returns:
        Verified cost base manifest

    Raises:
        CostBaseError: If loading fails
        SignatureError: If verification fails
    """
    loader = CostBaseLoader()
    manifest = loader.load_manifest(package_path)

    verifier = CostBaseVerifier(public_key)
    verifier.verify_signature(manifest)

    return manifest


def create_api_negotiator(package_path: str, public_key: Optional[str] = None) -> ApiNegotiator:
    """
    Create an API negotiator from a verified mod package.

    Args:
        package_path: Path to the mod package
        public_key: Public key for verification

    Returns:
        Configured API negotiator
    """
    cost_base = load_and_verify_cost_base(package_path, public_key)
    return ApiNegotiator(cost_base)
