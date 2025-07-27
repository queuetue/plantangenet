import pytest
from plantangenet.omni.storage.relationships import RelationshipManager


@pytest.mark.asyncio
async def test_relationship_manager_init():
    manager = RelationshipManager()
    assert len(manager._relationships) == 0
    assert len(manager._reverse_relationships) == 0


@pytest.mark.asyncio
async def test_add_relationship_basic():
    manager = RelationshipManager()
    
    success = await manager.add_relationship("parent1", "child1", "manages")
    assert success is True
    
    # Check forward relationship
    assert "parent1" in manager._relationships
    assert "manages" in manager._relationships["parent1"]
    assert "child1" in manager._relationships["parent1"]["manages"]
    
    # Check reverse relationship
    assert "child1" in manager._reverse_relationships
    assert "parent1" in manager._reverse_relationships["child1"]


@pytest.mark.asyncio
async def test_add_multiple_relationships():
    manager = RelationshipManager()
    
    # Add multiple children to same parent
    await manager.add_relationship("parent1", "child1", "manages")
    await manager.add_relationship("parent1", "child2", "manages")
    await manager.add_relationship("parent1", "child3", "manages")
    
    # Check all children are tracked
    children = manager._relationships["parent1"]["manages"]
    assert len(children) == 3
    assert "child1" in children
    assert "child2" in children
    assert "child3" in children
    
    # Check reverse relationships
    for child in ["child1", "child2", "child3"]:
        assert "parent1" in manager._reverse_relationships[child]


@pytest.mark.asyncio
async def test_add_different_relationship_types():
    manager = RelationshipManager()
    
    # Add different types of relationships for same parent
    await manager.add_relationship("parent1", "child1", "manages")
    await manager.add_relationship("parent1", "child2", "mentors")
    await manager.add_relationship("parent1", "child3", "collaborates_with")
    
    # Check relationships are grouped by type
    assert "manages" in manager._relationships["parent1"]
    assert "mentors" in manager._relationships["parent1"]
    assert "collaborates_with" in manager._relationships["parent1"]
    
    assert len(manager._relationships["parent1"]["manages"]) == 1
    assert len(manager._relationships["parent1"]["mentors"]) == 1
    assert len(manager._relationships["parent1"]["collaborates_with"]) == 1


@pytest.mark.asyncio
async def test_remove_relationship():
    manager = RelationshipManager()
    
    # Add relationships
    await manager.add_relationship("parent1", "child1", "manages")
    await manager.add_relationship("parent1", "child2", "manages")
    
    # Remove one relationship
    success = await manager.remove_relationship("parent1", "child1", "manages")
    assert success is True
    
    # Check forward relationship removed
    children = manager._relationships["parent1"]["manages"]
    assert "child1" not in children
    assert "child2" in children
    
    # Check reverse relationship removed
    assert "child1" not in manager._reverse_relationships or \
           "parent1" not in manager._reverse_relationships["child1"]


@pytest.mark.asyncio
async def test_remove_nonexistent_relationship():
    manager = RelationshipManager()
    
    # Try to remove relationship that doesn't exist
    success = await manager.remove_relationship("parent1", "child1", "manages")
    assert success is True  # Should succeed (idempotent)


@pytest.mark.asyncio
async def test_remove_last_relationship_cleans_up():
    manager = RelationshipManager()
    
    # Add single relationship
    await manager.add_relationship("parent1", "child1", "manages")
    
    # Remove it
    await manager.remove_relationship("parent1", "child1", "manages")
    
    # Check empty structures are cleaned up
    assert "parent1" not in manager._relationships
    assert "child1" not in manager._reverse_relationships


@pytest.mark.asyncio
async def test_get_relationships_forward():
    manager = RelationshipManager()
    
    # Add relationships
    await manager.add_relationship("parent1", "child1", "manages")
    await manager.add_relationship("parent1", "child2", "manages")
    await manager.add_relationship("parent1", "child3", "mentors")
    
    # Get children by type
    managed = await manager.get_relationships("parent1", "manages")
    assert len(managed) == 2
    assert "child1" in managed
    assert "child2" in managed
    
    mentored = await manager.get_relationships("parent1", "mentors")
    assert len(mentored) == 1
    assert "child3" in mentored


@pytest.mark.asyncio
async def test_get_relationships_reverse():
    manager = RelationshipManager()
    
    # Add relationships from multiple parents to same child
    await manager.add_relationship("parent1", "child1", "manages")
    await manager.add_relationship("parent2", "child1", "manages")
    
    # Get parents (reverse)
    parents = await manager.get_relationships("child1", reverse=True)
    assert len(parents) == 2
    assert "parent1" in parents
    assert "parent2" in parents


@pytest.mark.asyncio
async def test_get_relationships_nonexistent():
    manager = RelationshipManager()
    
    # Get relationships for non-existent omni
    relationships = await manager.get_relationships("nonexistent", "manages")
    assert relationships == []
    
    reverse_relationships = await manager.get_relationships("nonexistent", reverse=True)
    assert reverse_relationships == []


@pytest.mark.asyncio
async def test_get_relationships_empty_type():
    manager = RelationshipManager()
    
    # Add relationship of one type
    await manager.add_relationship("parent1", "child1", "manages")
    
    # Try to get different type
    relationships = await manager.get_relationships("parent1", "mentors")
    assert relationships == []


def test_get_all_relationships():
    manager = RelationshipManager()
    
    # Add various relationships
    asyncio.run(manager.add_relationship("parent1", "child1", "manages"))
    asyncio.run(manager.add_relationship("parent1", "child2", "manages"))
    asyncio.run(manager.add_relationship("parent1", "child3", "mentors"))
    asyncio.run(manager.add_relationship("parent2", "parent1", "supervises"))
    
    # Get all relationships for parent1
    all_relationships = manager.get_all_relationships("parent1")
    
    assert "manages" in all_relationships
    assert "mentors" in all_relationships
    assert "parents" in all_relationships  # Reverse relationships
    
    assert len(all_relationships["manages"]) == 2
    assert len(all_relationships["mentors"]) == 1
    assert len(all_relationships["parents"]) == 1
    assert "parent2" in all_relationships["parents"]


def test_get_all_relationships_empty():
    manager = RelationshipManager()
    
    all_relationships = manager.get_all_relationships("nonexistent")
    assert all_relationships == {}


def test_clear_all_relationships():
    manager = RelationshipManager()
    
    # Add relationships
    asyncio.run(manager.add_relationship("parent1", "child1", "manages"))
    asyncio.run(manager.add_relationship("parent2", "child2", "manages"))
    
    # Clear all
    manager.clear_all_relationships()
    
    assert len(manager._relationships) == 0
    assert len(manager._reverse_relationships) == 0


def test_clear_relationships_for_omni():
    manager = RelationshipManager()
    
    # Add relationships
    asyncio.run(manager.add_relationship("parent1", "child1", "manages"))
    asyncio.run(manager.add_relationship("parent1", "child2", "manages"))
    asyncio.run(manager.add_relationship("parent2", "child3", "manages"))
    
    # Clear relationships for parent1
    manager.clear_relationships_for_omni("parent1")
    
    # parent1 relationships should be gone
    assert "parent1" not in manager._relationships
    
    # But parent2 should remain
    assert "parent2" in manager._relationships
    
    # Reverse relationships should be updated
    assert "child1" not in manager._reverse_relationships
    assert "child2" not in manager._reverse_relationships


def test_get_stats():
    manager = RelationshipManager()
    
    # Add relationships
    asyncio.run(manager.add_relationship("parent1", "child1", "manages"))
    asyncio.run(manager.add_relationship("parent1", "child2", "manages"))
    asyncio.run(manager.add_relationship("parent2", "child3", "mentors"))
    
    stats = manager.get_stats()
    
    assert stats["total_relationships"] == 3
    assert stats["omnis_with_relationships"] == 2
    assert stats["relationship_types"] == {"manages", "mentors"}


import asyncio  # Add this import at the top
