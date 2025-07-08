"""
Base component system for registrable components in Plantangenet.

This module provides a common base class and utilities for components that need to be
registered with parents (sessions, compositors, agents, etc.) and managed uniformly.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Set, Dict, List
from collections import defaultdict


class RegistrableComponent(ABC):
    """
    Base class for components that can be registered with parent objects.

    This provides a common interface for comdecs, observables, mixins, agents,
    and other components that need lifecycle management and registration.
    """

    def __init__(self, name: Optional[str] = None):
        self._name = name or self.__class__.__name__
        self._registered_with: Optional[Any] = None
        self._metadata: Dict[str, Any] = {}
        self._errors: List[str] = []

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    def register_with(self, parent: Any) -> 'RegistrableComponent':
        """
        Register this component with a parent object.

        Args:
            parent: The parent object to register with

        Returns:
            self for method chaining
        """
        if self._registered_with is not None:
            self.unregister()

        self._registered_with = parent

        # If parent has a component registry, register there
        if hasattr(parent, '_component_registry'):
            parent._component_registry.register(self)
        elif hasattr(parent, 'add_component'):
            parent.add_component(self)

        self._on_register(parent)
        return self

    def unregister(self) -> 'RegistrableComponent':
        """
        Unregister this component from its parent.

        Returns:
            self for method chaining
        """
        if self._registered_with is None:
            return self

        parent = self._registered_with

        # If parent has a component registry, unregister there
        if hasattr(parent, '_component_registry'):
            parent._component_registry.unregister(self)
        elif hasattr(parent, 'remove_component'):
            parent.remove_component(self)

        self._on_unregister(parent)
        self._registered_with = None
        return self

    def _on_register(self, parent: Any):
        """Hook called when component is registered. Override in subclasses."""
        pass

    def _on_unregister(self, parent: Any):
        """Hook called when component is unregistered. Override in subclasses."""
        pass

    @property
    def registered_with(self) -> Optional[Any]:
        """Get the parent this component is registered with."""
        return self._registered_with

    @property
    def is_registered(self) -> bool:
        """Check if this component is currently registered."""
        return self._registered_with is not None

    def set_metadata(self, key: str, value: Any) -> 'RegistrableComponent':
        """Set metadata for this component."""
        self._metadata[key] = value
        return self

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata for this component."""
        return self._metadata.get(key, default)

    def add_error(self, error: str):
        """Add an error message to this component."""
        self._errors.append(error)

    @property
    def errors(self) -> List[str]:
        """Get all errors for this component."""
        return self._errors.copy()

    def clear_errors(self):
        """Clear all errors for this component."""
        self._errors.clear()


class ComponentRegistry:
    """
    Registry for managing collections of RegistrableComponents.

    This can be used by parent objects (sessions, compositors, etc.) to
    manage their registered components uniformly.
    """

    def __init__(self):
        self._components: Set[RegistrableComponent] = set()
        self._components_by_type: Dict[type,
                                       Set[RegistrableComponent]] = defaultdict(set)
        self._components_by_name: Dict[str, RegistrableComponent] = {}

    def register(self, component: RegistrableComponent):
        """Register a component."""
        if component in self._components:
            return

        self._components.add(component)
        self._components_by_type[type(component)].add(component)

        if component.name:
            if component.name in self._components_by_name:
                existing = self._components_by_name[component.name]
                component.add_error(f"Name conflict with {existing}")
            self._components_by_name[component.name] = component

    def unregister(self, component: RegistrableComponent):
        """Unregister a component."""
        self._components.discard(component)
        self._components_by_type[type(component)].discard(component)

        if component.name in self._components_by_name:
            if self._components_by_name[component.name] is component:
                del self._components_by_name[component.name]

    def get_by_name(self, name: str) -> Optional[RegistrableComponent]:
        """Get a component by name."""
        return self._components_by_name.get(name)

    def get_by_type(self, component_type: type) -> Set[RegistrableComponent]:
        """Get all components of a specific type."""
        return self._components_by_type[component_type].copy()

    def all_components(self) -> Set[RegistrableComponent]:
        """Get all registered components."""
        return self._components.copy()

    def clear(self):
        """Clear all registered components."""
        # Unregister all components
        for component in list(self._components):
            component.unregister()

        self._components.clear()
        self._components_by_type.clear()
        self._components_by_name.clear()


class ComponentRegistryMixin:
    """
    Mixin for objects that need to manage RegistrableComponents using a ComponentRegistry.

    This can be used by sessions, compositors, agents, etc. to provide
    standard component registration capabilities.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._component_registry = ComponentRegistry()

    def add_component(self, component: RegistrableComponent) -> 'ComponentRegistryMixin':
        """Add a component to this manager."""
        component.register_with(self)
        return self

    def remove_component(self, component: RegistrableComponent) -> 'ComponentRegistryMixin':
        """Remove a component from this manager."""
        component.unregister()
        return self

    def get_component(self, name: str) -> Optional[RegistrableComponent]:
        """Get a component by name."""
        return self._component_registry.get_by_name(name)

    def get_components_by_type(self, component_type: type) -> Set[RegistrableComponent]:
        """Get all components of a specific type."""
        return self._component_registry.get_by_type(component_type)

    def all_components(self) -> Set[RegistrableComponent]:
        """Get all components managed by this object."""
        return self._component_registry.all_components()


def register_components(parent: Any, *components: RegistrableComponent):
    """Utility function to register multiple components with a parent."""
    for component in components:
        component.register_with(parent)


def unregister_components(*components: RegistrableComponent):
    """Utility function to unregister multiple components."""
    for component in components:
        component.unregister()
