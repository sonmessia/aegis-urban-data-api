"""Domain exceptions for Entities module."""


class EntityDomainException(Exception):
    """Base exception for all entities domain errors."""
    pass


class EntityNotFoundError(EntityDomainException):
    """Raised when an entity is not found in the repository."""

    def __init__(self, entity_id: str) -> None:
        self.entity_id = entity_id
        super().__init__(f"Entity not found: {entity_id}")


class EntityAlreadyExistsError(EntityDomainException):
    """Raised when attempting to create a duplicate entity."""

    def __init__(self, entity_id: str) -> None:
        self.entity_id = entity_id
        super().__init__(f"Entity already exists: {entity_id}")
