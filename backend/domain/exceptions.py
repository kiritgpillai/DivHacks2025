"""Domain-level exceptions"""


class DomainError(Exception):
    """Base exception for domain errors"""
    pass


class InvalidPortfolioError(DomainError):
    """Portfolio validation error"""
    pass


class InvalidAllocationError(DomainError):
    """Allocation validation error"""
    pass


class InsufficientFundsError(DomainError):
    """Insufficient cash for operation"""
    pass


class InvalidTickerError(DomainError):
    """Invalid or unknown ticker"""
    pass


class InvalidDecisionError(DomainError):
    """Invalid decision type or parameters"""
    pass


class PositionNotFoundError(DomainError):
    """Position not found in portfolio"""
    pass

