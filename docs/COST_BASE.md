# Cost Base System for Dust Pricing

## Overview

The Cost Base system enables signed, verifiable Dust pricing for mod packages in Plantangenet. It ensures that:

- All API costs are transparent and declared up front
- Mod packages cannot be tampered with to hide or change costs
- Users can negotiate API calls with full knowledge of pricing
- The system supports both simple actions and package deals

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Mod Package   │───▶│  Cost Base       │───▶│  API            │
│   (Signed ZIP)  │    │  System          │    │  Negotiator     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Signature       │
                       │  Verification    │
                       └──────────────────┘
```

### Components

1. **CostBaseLoader**: Loads manifests from mod packages (ZIP files)
2. **CostBaseVerifier**: Verifies cryptographic signatures on manifests
3. **ApiNegotiator**: Handles quote/commit negotiation using verified cost bases

## Cost Base Format

Each mod package contains a `manifest.json` file with the following structure:

```json
{
  "name": "StreamerEffects",
  "version": "1.0.0",
  "description": "Interactive effects for streamers",
  "api_costs": {
    "send_sticker": 3,
    "send_emoji": 2,
    "clear_screen": 5,
    "bulk_save": 10,
    "self_maintained": 5
  },
  "signature": "BASE64_SIGNATURE_HERE"
}
```

### API Costs

- **Simple actions**: Fixed dust cost per action (e.g., `"send_sticker": 3`)
- **Package deals**: Multiple pricing options for complex operations
- **Dynamic pricing**: Costs can be calculated based on parameters

## API Negotiation Flow

### 1. Quote Phase

```python
quote = negotiator.get_quote("send_sticker", {"sticker_id": "party_parrot"})
# Returns: {"allowed": True, "dust_cost": 3, "action": "send_sticker", ...}
```

### 2. Commit Phase

```python
result = negotiator.commit_action("send_sticker", params, session, 3)
# Returns: {"success": True, "dust_charged": 3, ...}
```

### Package Deals Example

```python
quote = negotiator.get_quote("save_object", {"fields": ["name", "age", "email"]})
# Returns multiple options:
# [
#   {"type": "per_field", "dust_cost": 105, "description": "Save 3 fields individually"},
#   {"type": "bulk_save", "dust_cost": 10, "description": "Save all fields at once"},
#   {"type": "self_maintained", "dust_cost": 5, "description": "Self-maintained, per turn"}
# ]
```

## Security Features

### Signature Verification

- All manifests must be cryptographically signed
- Tampering with costs invalidates the signature
- Unsigned or invalid packages are rejected

### Quote Expiry (Future Enhancement)

- Quotes can have expiry times to prevent stale pricing
- Clients must commit before expiry or request new quotes

## Usage Examples

### Basic Usage

```python
from plantangenet.cost_base import create_api_negotiator

# Load and verify a mod package
negotiator = create_api_negotiator("streamer_effects.zip")

# Get a quote
quote = negotiator.get_quote("send_sticker", {"sticker_id": "party"})

# Commit the action
if user_accepts_cost(quote["dust_cost"]):
    result = negotiator.commit_action("send_sticker", {"sticker_id": "party"}, 
                                    session, quote["dust_cost"])
```

### Package Deal Selection

```python
# Get multiple pricing options
quote = negotiator.get_quote("save_object", {"fields": ["name", "age"]})

# Let user choose option
selected_option = user_selects_option(quote["options"])

# Commit with selected pricing
result = negotiator.commit_action("save_object", {"fields": ["name", "age"]}, 
                                session, selected_option["dust_cost"])
```

## Integration with Streaming Platform

For the streaming platform use case:

1. **Mod developers** create packages with cost bases and sign them
2. **Streamers** install verified mod packages  
3. **Viewers** see transparent pricing for all interactions
4. **Platform** enforces costs via the negotiation API

### Streamer Benefits

- Transparent economics for viewers
- Protection against hidden or inflated costs
- Ability to offer package deals and discounts
- Auditable transaction history

### Viewer Benefits  

- No surprise charges
- Clear understanding of action costs
- Choice between different pricing options
- Protection against malicious mods

## Testing

The system includes comprehensive tests covering:

- Manifest loading and parsing
- Signature verification and tamper detection
- API negotiation with simple and package pricing
- Error handling and edge cases
- End-to-end integration workflows

Run tests with:
```bash
python -m pytest test_cost_base.py -v
```

## Future Enhancements

1. **Real Cryptographic Signatures**: Replace placeholder verification with actual crypto
2. **Quote Expiry**: Add timestamp-based quote expiration
3. **Dynamic Pricing**: Support for time-based or load-based pricing
4. **Bulk Operations**: Batch multiple actions in a single quote/commit
5. **Policy Integration**: Connect with existing RBAC policy system
6. **Audit Logging**: Enhanced logging for compliance and debugging

---

*This system provides the foundation for transparent, secure, and flexible Dust-based economics in Plantangenet mod packages.*
