"""Position entity"""

from decimal import Decimal
from typing import Tuple


class Position:
    """Single stock holding within a portfolio"""
    
    def __init__(
        self,
        ticker: str,
        allocation: float,
        entry_price: float,
        current_price: float | None = None
    ):
        self.ticker = ticker
        self.allocation = Decimal(str(allocation))  # Dollars allocated
        self.entry_price = Decimal(str(entry_price))
        self.shares = self.allocation / self.entry_price
        self.current_price = Decimal(str(current_price or entry_price))
    
    def calculate_value(self) -> Decimal:
        """Calculate current value of position"""
        return self.shares * self.current_price
    
    def calculate_pl(self) -> Tuple[Decimal, Decimal]:
        """
        Calculate profit/loss
        
        Returns:
            (pl_dollars, pl_percent)
        """
        current_value = self.calculate_value()
        pl_dollars = current_value - self.allocation
        pl_percent = pl_dollars / self.allocation if self.allocation > 0 else Decimal(0)
        return (pl_dollars, pl_percent)
    
    def update_price(self, new_price: float) -> None:
        """Update current price"""
        self.current_price = Decimal(str(new_price))
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        pl_dollars, pl_percent = self.calculate_pl()
        return {
            "ticker": self.ticker,
            "allocation": float(self.allocation),
            "entry_price": float(self.entry_price),
            "current_price": float(self.current_price),
            "shares": float(self.shares),
            "current_value": float(self.calculate_value()),
            "pl_dollars": float(pl_dollars),
            "pl_percent": float(pl_percent)
        }
    
    def __repr__(self) -> str:
        return f"Position({self.ticker}, {float(self.shares):.2f} shares @ ${float(self.current_price):.2f})"

