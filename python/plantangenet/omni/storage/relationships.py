# Copyright (c) 2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Relationship management for omni objects.
"""

from typing import Dict, List, Set


class RelationshipManager:
    """
    Manages relationships between omni objects.
    
    Supports bidirectional relationships with different types
    (e.g., "child", "parent", "sibling", "dependency").
    """
    
    def __init__(self):
        # Forward relationships: omni_id -> {rel_type -> {child_ids}}
        self._relationships: Dict[str, Dict[str, Set[str]]] = {}
        # Reverse relationships: child_id -> {parent_ids}
        self._reverse_relationships: Dict[str, Set[str]] = {}
    
    async def add_relationship(
        self,
        parent_id: str,
        child_id: str,
        relationship_type: str = "child"
    ) -> bool:
        """
        Add relationship between omnis.
        
        Args:
            parent_id: ID of parent omni
            child_id: ID of child omni
            relationship_type: Type of relationship
            
        Returns:
            True if successful
        """
        try:
            # Forward relationship
            if parent_id not in self._relationships:
                self._relationships[parent_id] = {}
            if relationship_type not in self._relationships[parent_id]:
                self._relationships[parent_id][relationship_type] = set()
            
            self._relationships[parent_id][relationship_type].add(child_id)
            
            # Reverse relationship
            if child_id not in self._reverse_relationships:
                self._reverse_relationships[child_id] = set()
            self._reverse_relationships[child_id].add(parent_id)
            
            return True
            
        except Exception:
            return False
    
    async def remove_relationship(
        self,
        parent_id: str,
        child_id: str,
        relationship_type: str = "child"
    ) -> bool:
        """
        Remove relationship between omnis.
        
        Args:
            parent_id: ID of parent omni
            child_id: ID of child omni
            relationship_type: Type of relationship
            
        Returns:
            True if successful
        """
        try:
            # Forward relationship
            if (parent_id in self._relationships and 
                relationship_type in self._relationships[parent_id]):
                self._relationships[parent_id][relationship_type].discard(child_id)
                
                # Clean up empty sets
                if not self._relationships[parent_id][relationship_type]:
                    del self._relationships[parent_id][relationship_type]
                if not self._relationships[parent_id]:
                    del self._relationships[parent_id]
            
            # Reverse relationship
            if child_id in self._reverse_relationships:
                self._reverse_relationships[child_id].discard(parent_id)
                
                # Clean up empty sets
                if not self._reverse_relationships[child_id]:
                    del self._reverse_relationships[child_id]
            
            return True
            
        except Exception:
            return False
    
    async def get_relationships(
        self,
        omni_id: str,
        relationship_type: str = "child",
        reverse: bool = False
    ) -> List[str]:
        """
        Get relationships for an omni.
        
        Args:
            omni_id: ID of the omni
            relationship_type: Type of relationship to get
            reverse: If True, get parents instead of children
            
        Returns:
            List of related omni IDs
        """
        try:
            if reverse:
                # Get parents
                return list(self._reverse_relationships.get(omni_id, set()))
            else:
                # Get children of specified type
                relationships = self._relationships.get(omni_id, {})
                return list(relationships.get(relationship_type, set()))
                
        except Exception:
            return []
    
    def get_all_relationships(self, omni_id: str) -> Dict[str, List[str]]:
        """
        Get all relationships for an omni organized by type.
        
        Args:
            omni_id: ID of the omni
            
        Returns:
            Dictionary mapping relationship types to lists of omni IDs
        """
        result = {}
        relationships = self._relationships.get(omni_id, {})
        
        for rel_type, child_set in relationships.items():
            result[rel_type] = list(child_set)
        
        # Add reverse relationships
        parents = self._reverse_relationships.get(omni_id, set())
        if parents:
            result["parents"] = list(parents)
        
        return result
    
    def remove_all_relationships(self, omni_id: str):
        """
        Remove all relationships involving an omni.
        
        Args:
            omni_id: ID of the omni to remove relationships for
        """
        # Remove as parent
        if omni_id in self._relationships:
            for rel_type, children in self._relationships[omni_id].items():
                for child_id in children:
                    if child_id in self._reverse_relationships:
                        self._reverse_relationships[child_id].discard(omni_id)
                        if not self._reverse_relationships[child_id]:
                            del self._reverse_relationships[child_id]
            del self._relationships[omni_id]
        
        # Remove as child
        if omni_id in self._reverse_relationships:
            for parent_id in self._reverse_relationships[omni_id]:
                if parent_id in self._relationships:
                    for rel_type, children in self._relationships[parent_id].items():
                        children.discard(omni_id)
                        if not children:
                            del self._relationships[parent_id][rel_type]
                    if not self._relationships[parent_id]:
                        del self._relationships[parent_id]
            del self._reverse_relationships[omni_id]
    
    def get_stats(self) -> Dict[str, any]:
        """Get relationship statistics"""
        total_relationships = sum(
            len(children) for rel_dict in self._relationships.values() 
            for children in rel_dict.values()
        )
        
        relationship_types = set()
        for rel_dict in self._relationships.values():
            relationship_types.update(rel_dict.keys())
        
        return {
            "omnis_with_relationships": len(self._relationships),
            "total_relationships": total_relationships,
            "relationship_types": relationship_types,  # Return as set, not list
            "reverse_relationships": len(self._reverse_relationships)
        }
    
    def clear_all_relationships(self):
        """Clear all relationships"""
        self._relationships.clear()
        self._reverse_relationships.clear()
    
    def clear_relationships_for_omni(self, omni_id: str):
        """Clear all relationships for a specific omni (same as remove_all_relationships)"""
        self.remove_all_relationships(omni_id)
