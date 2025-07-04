"""
Test-driven development for signed cost base system.
Tests for loading, verifying, and using Dust pricing from mod packages.
"""

import pytest
import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the modules we'll implement
from plantangenet.cost_base import (
    CostBaseLoader,
    CostBaseVerifier,
    ApiNegotiator,
    CostBaseError,
    SignatureError
)


class TestCostBaseLoader:
    """Test loading cost base from mod packages."""

    def test_loads_cost_base_from_manifest(self):
        """Test that cost base is correctly loaded from manifest."""
        manifest_data = {
            "api_costs": {
                "send_sticker": 3,
                "bulk_save": 10,
                "self_maintained": 5
            },
            "signature": "BASE64_SIGNATURE_HERE"
        }

        # Create a temporary zip file with manifest
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w') as zf:
                zf.writestr('manifest.json', json.dumps(manifest_data))

            loader = CostBaseLoader()
            manifest = loader.load_manifest(tmp_zip.name)

            assert manifest["api_costs"]["send_sticker"] == 3
            assert manifest["api_costs"]["bulk_save"] == 10
            assert manifest["api_costs"]["self_maintained"] == 5
            assert "signature" in manifest

    def test_raises_error_on_missing_manifest(self):
        """Test that missing manifest raises appropriate error."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w') as zf:
                zf.writestr('readme.txt', 'No manifest here')

            loader = CostBaseLoader()
            with pytest.raises(CostBaseError, match="manifest.json not found"):
                loader.load_manifest(tmp_zip.name)

    def test_raises_error_on_malformed_manifest(self):
        """Test that malformed JSON raises appropriate error."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w') as zf:
                zf.writestr('manifest.json', 'invalid json {')

            loader = CostBaseLoader()
            with pytest.raises(CostBaseError, match="Invalid JSON"):
                loader.load_manifest(tmp_zip.name)


class TestCostBaseVerifier:
    """Test signature verification of cost base."""

    def test_signature_verification_passes(self):
        """Test that valid signature passes verification."""
        manifest = {
            "api_costs": {"send_sticker": 3},
            "signature": "VALID_SIGNATURE"
        }

        verifier = CostBaseVerifier()
        # Mock the actual signature verification for now
        with patch.object(verifier, '_verify_signature', return_value=True):
            assert verifier.verify_signature(manifest) is True

    def test_signature_verification_fails(self):
        """Test that invalid signature fails verification."""
        manifest = {
            "api_costs": {"send_sticker": 3},
            "signature": "INVALID_SIGNATURE"
        }

        verifier = CostBaseVerifier()
        with patch.object(verifier, '_verify_signature', return_value=False):
            with pytest.raises(SignatureError, match="Invalid signature"):
                verifier.verify_signature(manifest)

    def test_rejects_missing_signature(self):
        """Test that missing signature is rejected."""
        manifest = {
            "api_costs": {"send_sticker": 3}
            # No signature field
        }

        verifier = CostBaseVerifier()
        with pytest.raises(SignatureError, match="Missing signature"):
            verifier.verify_signature(manifest)

    def test_rejects_tampered_cost_base(self):
        """Test that tampered cost base is detected."""
        manifest = {
            "api_costs": {"send_sticker": 999},  # Tampered value
            "signature": "ORIGINAL_SIGNATURE"
        }

        verifier = CostBaseVerifier()
        with patch.object(verifier, '_verify_signature', return_value=False):
            with pytest.raises(SignatureError, match="Invalid signature"):
                verifier.verify_signature(manifest)


class TestApiNegotiator:
    """Test API negotiation using cost base."""

    def test_api_uses_cost_base_for_quote(self):
        """Test that API quotes use the loaded cost base."""
        cost_base = {
            "api_costs": {
                "send_sticker": 3,
                "bulk_save": 10
            }
        }

        negotiator = ApiNegotiator(cost_base)
        quote = negotiator.get_quote("send_sticker", {})

        assert quote["dust_cost"] == 3
        assert quote["allowed"] is True

    def test_api_supports_package_deals(self):
        """Test that API supports multiple pricing options."""
        cost_base = {
            "api_costs": {
                "save_per_field": 35,
                "bulk_save": 10,
                "self_maintained": 5
            }
        }

        negotiator = ApiNegotiator(cost_base)
        quote = negotiator.get_quote(
            "save_object", {"fields": ["name", "age", "email"]})

        # Should return multiple options
        assert "options" in quote
        options = {opt["type"]: opt["dust_cost"] for opt in quote["options"]}
        assert options["per_field"] == 35 * 3  # 3 fields
        assert options["bulk_save"] == 10
        assert options["self_maintained"] == 5

    def test_api_commit_deducts_dust(self):
        """Test that committing an action deducts the correct Dust amount."""
        cost_base = {
            "api_costs": {
                "send_sticker": 3
            }
        }

        # Mock dust balance and deduction
        mock_session = MagicMock()
        mock_session.dust_balance = 20

        negotiator = ApiNegotiator(cost_base)
        result = negotiator.commit_action("send_sticker", {}, mock_session, 3)

        assert result["success"] is True
        assert result["dust_charged"] == 3
        mock_session.deduct_dust.assert_called_once_with(3)

    def test_api_rejects_insufficient_dust(self):
        """Test that insufficient Dust balance is rejected."""
        cost_base = {
            "api_costs": {
                "send_sticker": 3
            }
        }

        mock_session = MagicMock()
        mock_session.dust_balance = 1  # Insufficient

        negotiator = ApiNegotiator(cost_base)
        result = negotiator.commit_action("send_sticker", {}, mock_session, 3)

        assert result["success"] is False
        assert "insufficient" in result["error"].lower()

    def test_api_rejects_unknown_action(self):
        """Test that unknown actions are rejected."""
        cost_base = {
            "api_costs": {
                "send_sticker": 3
            }
        }

        negotiator = ApiNegotiator(cost_base)
        with pytest.raises(CostBaseError, match="Unknown action"):
            negotiator.get_quote("unknown_action", {})


class TestIntegration:
    """Integration tests for the complete cost base system."""

    def test_complete_workflow(self):
        """Test the complete workflow from package to API call."""
        # Create a signed mod package
        manifest_data = {
            "api_costs": {
                "send_sticker": 3,
                "bulk_save": 10
            },
            "signature": "VALID_SIGNATURE"
        }

        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w') as zf:
                zf.writestr('manifest.json', json.dumps(manifest_data))

            # Load and verify the package
            loader = CostBaseLoader()
            manifest = loader.load_manifest(tmp_zip.name)

            verifier = CostBaseVerifier()
            with patch.object(verifier, '_verify_signature', return_value=True):
                verifier.verify_signature(manifest)

            # Use the cost base for API negotiation
            negotiator = ApiNegotiator(manifest)
            quote = negotiator.get_quote("send_sticker", {})

            assert quote["dust_cost"] == 3
            assert quote["allowed"] is True

    def test_rejects_tampered_package(self):
        """Test that the system rejects tampered packages end-to-end."""
        # Create a package with tampered cost base
        manifest_data = {
            "api_costs": {
                "send_sticker": 999  # Suspiciously high cost
            },
            "signature": "ORIGINAL_SIGNATURE"
        }

        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w') as zf:
                zf.writestr('manifest.json', json.dumps(manifest_data))

            loader = CostBaseLoader()
            manifest = loader.load_manifest(tmp_zip.name)

            verifier = CostBaseVerifier()
            with patch.object(verifier, '_verify_signature', return_value=False):
                with pytest.raises(SignatureError):
                    verifier.verify_signature(manifest)


if __name__ == "__main__":
    pytest.main([__file__])
