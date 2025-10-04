"""Portfolio aggregate root"""

from decimal import Decimal
from typing import List
from uuid import UUID, uuid4

from ..exceptions import (
    DomainError,
    InvalidAllocationError,
    InsufficientFundsError,
    PositionNotFoundError
)
from .position import Position
from .risk_profile import RiskProfile


class Portfolio:
    """
    Portfolio aggregate root
    
    Manages player's holdings with initial $1M budget.
    Enforces risk profile limits and validates all operations.
    """
    
    def __init__(
        self,
        id: str | UUID,
        player_id: str,
        risk_profile: RiskProfile,
        initial_cash: float = 1_000_000
    ):
        self.id = str(id) if not isinstance(id, str) else id
        self.player_id = player_id
        self.risk_profile = risk_profile
        self.initial_cash = Decimal(str(initial_cash))
        self._positions: List[Position] = []
        self._cash = self.initial_cash
        self._validate_invariants()
    
    def _validate_invariants(self):
        """Validate domain invariants"""
        if self.initial_cash <= 0:
            raise DomainError("Initial cash must be positive")
    
    def add_position(
        self,
        ticker: str,
        allocation: float,
        entry_price: float
    ) -> Position:
        """
        Add position during portfolio setup
        
        Validates:
        - Sufficient cash available
        - Position size within risk profile limits
        
        Args:
            ticker: Stock ticker symbol
            allocation: Dollar amount to allocate
            entry_price: Entry price for the position
            
        Returns:
            Created Position
            
        Raises:
            InsufficientFundsError: Not enough cash
            InvalidAllocationError: Exceeds risk profile limits
        """
        allocation_decimal = Decimal(str(allocation))
        
        # Check sufficient cash
        if allocation_decimal > self._cash:
            raise InsufficientFundsError(
                f"Insufficient cash: ${float(self._cash):.2f} < ${allocation:.2f}"
            )
        
        # Check risk profile limits
        max_pct = self.risk_profile.max_position_size_pct
        max_allocation = self.initial_cash * Decimal(str(max_pct))
        
        if allocation_decimal > max_allocation:
            raise InvalidAllocationError(
                f"Position exceeds {max_pct*100:.0f}% limit for {self.risk_profile.value}"
            )
        
        # Create position
        position = Position(ticker, allocation, entry_price)
        self._positions.append(position)
        self._cash -= allocation_decimal
        
        return position
    
    def get_position(self, ticker: str) -> Position | None:
        """Get position by ticker"""
        return next((p for p in self._positions if p.ticker == ticker), None)
    
    def calculate_total_value(self) -> Decimal:
        """Calculate current total portfolio value"""
        positions_value = sum(p.calculate_value() for p in self._positions)
        return positions_value + self._cash
    
    def apply_sell_all(self, ticker: str) -> Decimal:
        """
        Apply SELL_ALL decision
        
        Removes position and adds value to cash.
        
        Returns:
            Value added to cash
        """
        position = self.get_position(ticker)
        if not position:
            raise PositionNotFoundError(f"Position not found: {ticker}")
        
        value = position.calculate_value()
        self._cash += value
        self._positions.remove(position)
        
        return value
    
    def apply_sell_half(self, ticker: str) -> Decimal:
        """
        Apply SELL_HALF decision
        
        Halves position size and adds half value to cash.
        
        Returns:
            Value added to cash
        """
        position = self.get_position(ticker)
        if not position:
            raise PositionNotFoundError(f"Position not found: {ticker}")
        
        half_value = position.calculate_value() / Decimal(2)
        
        # Update position
        position.shares = position.shares / Decimal(2)
        position.allocation = position.allocation / Decimal(2)
        
        # Add to cash
        self._cash += half_value
        
        return half_value
    
    def apply_hold(self, ticker: str, new_price: float) -> None:
        """
        Apply HOLD decision
        
        Updates current price, no position changes.
        """
        position = self.get_position(ticker)
        if not position:
            raise PositionNotFoundError(f"Position not found: {ticker}")
        
        position.update_price(new_price)
    
    def apply_buy(self, ticker: str, new_price: float) -> Decimal:
        """
        Apply BUY decision
        
        Adds 10% of current position size.
        
        Returns:
            Amount spent
        """
        position = self.get_position(ticker)
        if not position:
            raise PositionNotFoundError(f"Position not found: {ticker}")
        
        # Calculate 10% addition
        buy_amount = position.allocation * Decimal("0.1")
        
        if buy_amount > self._cash:
            raise InsufficientFundsError("Insufficient cash for buy")
        
        # Update position
        position.shares += buy_amount / Decimal(str(new_price))
        position.allocation += buy_amount
        position.update_price(new_price)
        
        # Reduce cash
        self._cash -= buy_amount
        
        return buy_amount
    
    @property
    def positions(self) -> List[Position]:
        """Get all positions (copy)"""
        return self._positions.copy()
    
    @property
    def tickers(self) -> List[str]:
        """Get all tickers"""
        return [p.ticker for p in self._positions]
    
    @property
    def cash(self) -> Decimal:
        """Get current cash"""
        return self._cash
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "player_id": self.player_id,
            "risk_profile": str(self.risk_profile),
            "initial_cash": float(self.initial_cash),
            "current_cash": float(self._cash),
            "positions": [p.to_dict() for p in self._positions],
            "total_value": float(self.calculate_total_value()),
            "tickers": self.tickers
        }
    
    def __repr__(self) -> str:
        return f"Portfolio({self.id}, {len(self._positions)} positions, ${float(self.calculate_total_value()):.2f})"

