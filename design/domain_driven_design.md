# Domain-Driven Design - Market Mayhem

## Core Principles

1. **Domain is pure**: No dependencies on infrastructure, frameworks, or external APIs
2. **Use repositories**: Interfaces in domain, implementations in infrastructure
3. **ACL for external services**: Never leak Tavily, yfinance, Gemini types into domain
4. **Ubiquitous language**: Portfolio, Position, Event, Decision, Villain, Behavioral Profile

---

## Bounded Contexts

### 1. Portfolio Context

**Aggregates**:
- **Portfolio** (root): Player's holdings with initial $1M
- **Position** (entity): Single stock holding (ticker, shares, entry price, current value)

**Value Objects**:
- **RiskProfile**: Risk-On | Balanced | Risk-Off
- **Allocation**: Dollar amount per ticker
- **PortfolioValue**: Current total value

**Repository Interface**:
```python
# domain/portfolio/PortfolioRepository.py
from abc import ABC, abstractmethod

class PortfolioRepository(ABC):
    @abstractmethod
    async def save(self, portfolio: Portfolio) -> None:
        pass
    
    @abstractmethod
    async def find_by_id(self, portfolio_id: str) -> Portfolio | None:
        pass
```

**Implementation**:
```python
# infrastructure/db/SupabasePortfolioRepository.py
class SupabasePortfolioRepository(PortfolioRepository):
    async def save(self, portfolio: Portfolio) -> None:
        await self.client.table('portfolios').upsert({
            'id': portfolio.id,
            'player_id': portfolio.player_id,
            'risk_profile': portfolio.risk_profile.value,
            'tickers': portfolio.tickers,
            'allocations': {p.ticker: p.allocation for p in portfolio.positions},
            'current_value': portfolio.calculate_total_value()
        })
```

---

### 2. Event Context

**Entities**:
- **MarketEvent**: Scenario tied to a ticker
- **EventType**: EARNINGS_SURPRISE | REGULATORY_NEWS | ANALYST_ACTION | VOLATILITY_SPIKE

**Value Objects**:
- **Horizon**: Time window for outcome (e.g., 3 days)
- **EventDescription**: Text description

**Domain Service**:
```python
# domain/event/EventGenerator.py (interface)
class EventGenerator(ABC):
    @abstractmethod
    async def generate_event(
        self, 
        ticker: str,
        event_type: EventType
    ) -> MarketEvent:
        pass
```

---

### 3. News Context

**Entities**:
- **Headline**: Single news article with stance
- **NewsStance**: Bull | Bear | Neutral

**Value Objects**:
- **Consensus**: Aggregated stance ("Two-thirds Bull")
- **ContradictionScore**: 0.0-1.0 (how much headlines disagree with Villain)

**Domain Service**:
```python
# domain/news/StanceClassifier.py
class StanceClassifier:
    def classify_consensus(self, headlines: List[Headline]) -> Consensus:
        bull_count = sum(1 for h in headlines if h.stance == NewsStance.BULL)
        bear_count = sum(1 for h in headlines if h.stance == NewsStance.BEAR)
        total = len(headlines)
        
        if bull_count / total > 0.66:
            return Consensus("Two-thirds Bull")
        elif bear_count / total > 0.66:
            return Consensus("Two-thirds Bear")
        else:
            return Consensus("Mixed")
    
    def calculate_contradiction(
        self,
        headlines: List[Headline],
        villain_stance: str
    ) -> ContradictionScore:
        opposing = sum(
            1 for h in headlines
            if (villain_stance == "Bearish" and h.stance == NewsStance.BULL) or
               (villain_stance == "Bullish" and h.stance == NewsStance.BEAR)
        )
        return ContradictionScore(opposing / len(headlines))
```

---

### 4. Villain Context

**Entities**:
- **VillainTake**: Biased hot take with labeled bias
- **CognitiveBias**: Fear Appeal | Overconfidence | Authority Lure | Recency Bias

**Value Objects**:
- **VillainStance**: Bullish | Bearish
- **EmotionalIntensity**: How aggressive the take is

**Domain Model**:
```python
# domain/villain/VillainTake.py
from dataclasses import dataclass

@dataclass(frozen=True)
class CognitiveBias:
    name: str  # Fear Appeal, Overconfidence, etc.
    description: str

class VillainTake:
    def __init__(
        self, 
        text: str,
        stance: str,  # Bullish/Bearish
        bias: CognitiveBias
    ):
        if len(text) < 20:
            raise DomainError("Villain take too short")
        
        self.text = text
        self.stance = stance
        self.bias = bias
    
    def is_contrarian_to_consensus(self, consensus: Consensus) -> bool:
        """Check if Villain contradicts news consensus"""
        if "Bull" in consensus.value and self.stance == "Bearish":
            return True
        if "Bear" in consensus.value and self.stance == "Bullish":
            return True
        return False
```

---

### 5. Historical Outcome Context

**Entities**:
- **HistoricalCase**: Past event instance with price path
- **PricePath**: Day 0 to Day H prices

**Value Objects**:
- **DecisionType**: Sell All | Sell Half | Hold | Buy
- **PLImpact**: P/L in dollars and percentage

**Domain Service**:
```python
# domain/historical/OutcomeCalculator.py
class OutcomeCalculator:
    def calculate_outcome(
        self, 
        decision: DecisionType,
        case: HistoricalCase,
        position_size: float
    ) -> PLImpact:
        """Calculate P/L based on decision and historical case"""
        
        if decision == DecisionType.SELL_ALL:
            # Exit at day 0, no further impact
            return PLImpact(dollars=0, percent=0)
        
        elif decision == DecisionType.SELL_HALF:
            # Realize half at day 0, other half rides to day H
            half_size = position_size / 2
            day_h_return = (case.day_h_price - case.day0_price) / case.day0_price
            pl_dollars = half_size * day_h_return
            pl_percent = day_h_return / 2  # Weighted average
            return PLImpact(dollars=pl_dollars, percent=pl_percent)
        
        elif decision == DecisionType.HOLD:
            # Full position rides to day H
            day_h_return = (case.day_h_price - case.day0_price) / case.day0_price
            pl_dollars = position_size * day_h_return
            return PLImpact(dollars=pl_dollars, percent=day_h_return)
        
        elif decision == DecisionType.BUY:
            # Add small increment, rides to day H
            buy_size = position_size * 0.1  # 10% of position
            total_size = position_size + buy_size
            day_h_return = (case.day_h_price - case.day0_price) / case.day0_price
            pl_dollars = total_size * day_h_return
            return PLImpact(dollars=pl_dollars, percent=day_h_return)
```

---

### 6. Decision Tracking Context

**Entities**:
- **DecisionLog**: Complete record of a single round decision
- **BehaviorFlag**: Pattern detected

**Value Objects**:
- **DataTabUsage**: Boolean (opened or not)
- **DecisionTime**: Time taken to decide

**Domain Model**:
```python
# domain/decision/DecisionLog.py
from datetime import datetime

class DecisionLog:
    def __init__(
        self,
        round_number: int,
        ticker: str,
        event: MarketEvent,
        villain_take: VillainTake,
        headlines: List[Headline],
        consensus: Consensus,
        contradiction_score: ContradictionScore,
        player_decision: DecisionType,
        opened_data_tab: bool,
        decision_time: float,
        historical_case: HistoricalCase,
        pl_impact: PLImpact
    ):
        self.round_number = round_number
        self.ticker = ticker
        self.event = event
        self.villain_take = villain_take
        self.headlines = headlines
        self.consensus = consensus
        self.contradiction_score = contradiction_score
        self.player_decision = player_decision
        self.opened_data_tab = opened_data_tab
        self.decision_time = decision_time
        self.historical_case = historical_case
        self.pl_impact = pl_impact
        self.timestamp = datetime.now()
        self.behavior_flags = []
    
    def flag_panic_sell(self, price_pattern: str):
        """Flag if player panic-sold after down days"""
        if self.player_decision == DecisionType.SELL_ALL and "3_down_closes" in price_pattern:
            self.behavior_flags.append("panic_sell")
    
    def flag_chased_spike(self, price_pattern: str):
        """Flag if player chased after up moves"""
        if self.player_decision == DecisionType.BUY and "3_up_closes" in price_pattern:
            self.behavior_flags.append("chased_spike")
    
    def flag_ignored_data(self):
        """Flag if player didn't check data"""
        if not self.opened_data_tab:
            self.behavior_flags.append("ignored_data")
    
    def flag_followed_villain_high_contradiction(self):
        """Flag if player followed Villain when headlines strongly disagreed"""
        if self.contradiction_score.value > 0.7:
            # Check if player aligned with Villain
            if (self.villain_take.stance == "Bullish" and self.player_decision == DecisionType.BUY) or \
               (self.villain_take.stance == "Bearish" and self.player_decision in [DecisionType.SELL_ALL, DecisionType.SELL_HALF]):
                self.behavior_flags.append("followed_villain_high_contradiction")
```

---

### 7. Behavioral Profiling Context

**Entities**:
- **BehavioralProfile**: Classification (Rational/Emotional/Conservative)
- **CoachingTip**: Personalized recommendation

**Value Objects**:
- **ProfileMetrics**: Data tab usage %, consensus alignment, etc.
- **TradeQuality**: Best/worst trades

**Domain Service**:
```python
# domain/profile/ProfileClassifier.py
class ProfileClassifier:
    def classify(self, logs: List[DecisionLog]) -> BehavioralProfile:
        """Rule-based classification (transparent, explainable)"""
        
        # Calculate metrics
        data_tab_usage = sum(1 for log in logs if log.opened_data_tab) / len(logs)
        
        consensus_alignment = sum(
            1 for log in logs
            if self._aligns_with_consensus(log.player_decision, log.consensus)
        ) / len(logs)
        
        panic_sells = sum(1 for log in logs if "panic_sell" in log.behavior_flags)
        chased_spikes = sum(1 for log in logs if "chased_spike" in log.behavior_flags)
        followed_villain_high_contradiction = sum(
            1 for log in logs if "followed_villain_high_contradiction" in log.behavior_flags
        )
        
        total_pl = sum(log.pl_impact.dollars for log in logs)
        
        # Classify
        if data_tab_usage > 0.7 and consensus_alignment > 0.6 and total_pl > 0:
            return BehavioralProfile.RATIONAL
        elif followed_villain_high_contradiction > len(logs) * 0.4 or panic_sells > 2:
            return BehavioralProfile.EMOTIONAL
        elif self._small_sizes(logs) and self._low_drawdowns(logs):
            return BehavioralProfile.CONSERVATIVE
        else:
            return BehavioralProfile.BALANCED
    
    def _aligns_with_consensus(self, decision: DecisionType, consensus: Consensus) -> bool:
        """Check if decision aligns with news consensus"""
        if "Bull" in consensus.value and decision in [DecisionType.HOLD, DecisionType.BUY]:
            return True
        if "Bear" in consensus.value and decision in [DecisionType.SELL_ALL, DecisionType.SELL_HALF]:
            return True
        return False
```

---

## Domain Models

### Portfolio Aggregate

```python
# domain/portfolio/Portfolio.py
from typing import List
from dataclasses import dataclass

@dataclass(frozen=True)
class RiskProfile:
    value: str  # Risk-On | Balanced | Risk-Off
    
    @property
    def max_position_size_pct(self) -> float:
        """Maximum % of portfolio per position"""
        return {
            "Risk-On": 0.50,      # 50% max
            "Balanced": 0.33,     # 33% max
            "Risk-Off": 0.25      # 25% max
        }[self.value]

class Position:
    def __init__(
        self,
        ticker: str,
        allocation: float,
        entry_price: float
    ):
        self.ticker = ticker
        self.allocation = allocation  # Dollars allocated
        self.entry_price = entry_price
        self.shares = allocation / entry_price
        self.current_price = entry_price
    
    def calculate_value(self) -> float:
        return self.shares * self.current_price
    
    def calculate_pl(self) -> tuple[float, float]:
        """Return (dollars, percent)"""
        current_value = self.calculate_value()
        pl_dollars = current_value - self.allocation
        pl_percent = pl_dollars / self.allocation
        return (pl_dollars, pl_percent)

class Portfolio:
    def __init__(
        self, 
        id: str,
        player_id: str,
        risk_profile: RiskProfile,
        initial_cash: float = 1_000_000
    ):
        self.id = id
        self.player_id = player_id
        self.risk_profile = risk_profile
        self.initial_cash = initial_cash
        self._positions: List[Position] = []
        self._cash = initial_cash
        self._validate_invariants()
    
    def _validate_invariants(self):
        if self.initial_cash <= 0:
            raise DomainError("Initial cash must be positive")
    
    def add_position(self, ticker: str, allocation: float, entry_price: float):
        """Add position during setup"""
        if allocation > self._cash:
            raise DomainError(f"Insufficient cash: {self._cash} < {allocation}")
        
        # Check risk profile limits
        max_pct = self.risk_profile.max_position_size_pct
        if allocation / self.initial_cash > max_pct:
            raise DomainError(f"Position exceeds {max_pct*100}% limit for {self.risk_profile.value}")
        
        position = Position(ticker, allocation, entry_price)
        self._positions.append(position)
        self._cash -= allocation
    
    def get_position(self, ticker: str) -> Position | None:
        return next((p for p in self._positions if p.ticker == ticker), None)
    
    def calculate_total_value(self) -> float:
        """Current portfolio value"""
        positions_value = sum(p.calculate_value() for p in self._positions)
        return positions_value + self._cash
    
    def apply_decision(
        self,
        ticker: str,
        decision: DecisionType,
        pl_dollars: float
    ):
        """Apply decision outcome to portfolio"""
        position = self.get_position(ticker)
        if not position:
            raise DomainError(f"Position not found: {ticker}")
        
        if decision == DecisionType.SELL_ALL:
            # Remove position, add to cash
            self._cash += position.calculate_value()
            self._positions.remove(position)
        
        elif decision == DecisionType.SELL_HALF:
            # Halve position, add to cash
            half_value = position.calculate_value() / 2
            self._cash += half_value
            position.shares /= 2
            position.allocation /= 2
        
        elif decision == DecisionType.HOLD:
            # Position value updated by P/L
            pass  # Current price already updated
        
        elif decision == DecisionType.BUY:
            # Add to position
            buy_amount = position.allocation * 0.1
            if buy_amount > self._cash:
                raise DomainError("Insufficient cash for buy")
            position.shares += buy_amount / position.current_price
            position.allocation += buy_amount
            self._cash -= buy_amount
    
    @property
    def positions(self) -> List[Position]:
        return self._positions.copy()
    
    @property
    def tickers(self) -> List[str]:
        return [p.ticker for p in self._positions]
    
    @property
    def cash(self) -> float:
        return self._cash
```

---

## Ubiquitous Language

| Term | Definition | Usage |
|------|-----------|--------|
| **Portfolio** | Player's holdings ($1M initial) | "Create portfolio" |
| **Position** | Single stock holding | "AAPL position" |
| **Event** | Market scenario tied to ticker | "Earnings event" |
| **Villain Take** | Biased hot take | "Villain says sell" |
| **Stance** | Bull/Bear/Neutral | "Headline stance" |
| **Consensus** | Aggregated stance | "Two-thirds Bull" |
| **Contradiction Score** | How much headlines disagree with Villain | "80% contradiction" |
| **Decision** | Player action | "Sell Half" |
| **Historical Case** | Past event with price path | "Sample case" |
| **P/L Impact** | Profit/loss from decision | "+$7,240 P/L" |
| **Behavioral Profile** | Rational/Emotional/Conservative | "You're Rational" |

---

## Dependency Injection

```python
# application/game/StartRoundHandler.py
class StartRoundHandler:
    def __init__(
        self,
        portfolio_repo: PortfolioRepository,      # Interface
        event_generator: EventGenerator,          # Interface
        historical_sampler: HistoricalSampler    # Interface
    ):
        self.portfolio_repo = portfolio_repo
        self.event_generator = event_generator
        self.historical_sampler = historical_sampler
    
    async def execute(self, game_id: str, round_number: int):
        # Use interfaces only
        portfolio = await self.portfolio_repo.find_by_game(game_id)
        
        # Select ticker from portfolio
        ticker = self._select_ticker(portfolio)
        
        # Generate event
        event = await self.event_generator.generate_event(ticker)
        
        return event
```

---

## Key Rules

1. ✅ Domain layer: Pure Python, no external dependencies
2. ✅ Interfaces in domain, implementations in infrastructure
3. ✅ Use ACL pattern for Gemini, Tavily, yfinance
4. ✅ Value objects are immutable (`@dataclass(frozen=True)`)
5. ✅ Aggregates enforce invariants (validation in constructors)
6. ✅ Repository returns domain objects (not DB models)
7. ❌ Never import infrastructure in domain
8. ❌ Never import external libraries in domain
9. ❌ Never expose domain internals (use properties/methods)

---

**Domain designed for: Portfolio management, historical replay, behavioral profiling—all pure business logic with zero infrastructure coupling.** 🚀
