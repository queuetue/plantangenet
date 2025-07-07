"""
Banker module for Plantangenet - handles all financial operations and cost negotiation.

This module provides:
- Banker protocol for financial operations
- BankerMixin for agent functionality  
- Financial and fee policies
- Data types for transactions and identities
- NullBanker for testing and development

Main exports:
- Banker: Core protocol interface
- BankerMixin: Mixin for agents
- NullBanker: Testing implementation
- TransactionResult, FinancialIdentity: Core data types
- FinancialPolicy, FeePolicy: Policy engines
"""

# Core protocol and interfaces
from .banker import Banker

# Main implementation
from .mixin import BankerMixin

# Testing implementation
from .null_banker import NullBanker

# Data types
from .econ_types import (
    TransactionResult,
    FinancialIdentity,
    FinancialAccessRequest,
    FeeStructure,
    Distributor,
    DistributionResult
)

# Policies
from .policies import (
    FinancialPolicy,
    PermissiveFinancialPolicy,
    FeePolicy
)

# Backward compatibility - export everything that was in the old banker.py
__all__ = [
    # Core interfaces
    "Banker",

    # Implementations
    "BankerMixin",
    "NullBanker",

    # Data types
    "TransactionResult",
    "FinancialIdentity",
    "FinancialAccessRequest",
    "FeeStructure",
    "Distributor",
    "DistributionResult",

    # Policies
    "FinancialPolicy",
    "PermissiveFinancialPolicy",
    "FeePolicy"
]
