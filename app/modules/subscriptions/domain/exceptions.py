"""Domain exceptions for Subscriptions module."""


class SubscriptionDomainException(Exception):
    """Base domain exception for Subscriptions."""

    pass


class SubscriptionNotFoundError(SubscriptionDomainException):
    """Raised when a subscription is not found."""

    def __init__(self, subscription_id: str) -> None:
        self.subscription_id = subscription_id
        super().__init__(f"Subscription not found: {subscription_id}")


class SubscriptionAlreadyExistsError(SubscriptionDomainException):
    """Raised when a subscription with the given ID already exists."""

    def __init__(self, subscription_id: str) -> None:
        self.subscription_id = subscription_id
        super().__init__(f"Subscription already exists: {subscription_id}")
