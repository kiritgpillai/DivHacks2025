-- Market Mayhem Database Schema
-- Supabase (PostgreSQL) 

-- Portfolios table
CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id TEXT NOT NULL,
    risk_profile TEXT NOT NULL CHECK (risk_profile IN ('Risk-On', 'Balanced', 'Risk-Off')),
    tickers TEXT[] NOT NULL,
    allocations JSONB NOT NULL,
    cash DECIMAL NOT NULL DEFAULT 0,
    total_value DECIMAL NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Positions table (individual stock positions within portfolios)
CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    shares DECIMAL NOT NULL CHECK (shares >= 0),
    entry_price DECIMAL NOT NULL CHECK (entry_price > 0),
    current_price DECIMAL NOT NULL CHECK (current_price > 0),
    allocation DECIMAL NOT NULL CHECK (allocation >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (portfolio_id, ticker)
);

-- Game sessions table
CREATE TABLE IF NOT EXISTS game_sessions (
    id TEXT PRIMARY KEY,
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    current_round INT DEFAULT 0 CHECK (current_round >= 0 AND current_round <= 3),
    portfolio_value DECIMAL NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    final_profile TEXT
);

-- Game rounds table
CREATE TABLE IF NOT EXISTS game_rounds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    round_number INT NOT NULL CHECK (round_number >= 1 AND round_number <= 3),
    
    -- Event data
    ticker TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_description TEXT NOT NULL,
    event_horizon INT NOT NULL,
    
    -- Villain data
    villain_stance TEXT NOT NULL CHECK (villain_stance IN ('Bullish', 'Bearish')),
    villain_bias TEXT NOT NULL,
    villain_hot_take TEXT NOT NULL,
    
    -- Player decision
    player_decision TEXT NOT NULL CHECK (player_decision IN ('SELL_ALL', 'SELL_HALF', 'HOLD', 'BUY')),
    decision_time DECIMAL NOT NULL,
    opened_data_tab BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Outcome
    pl_dollars DECIMAL NOT NULL,
    pl_percent DECIMAL NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE (session_id, round_number)
);

-- Decision tracker table (behavioral analysis)
CREATE TABLE IF NOT EXISTS decision_tracker (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    round_id UUID NOT NULL REFERENCES game_rounds(id) ON DELETE CASCADE,
    
    -- News analysis
    headlines_shown JSONB NOT NULL,
    consensus TEXT NOT NULL,
    contradiction_score DECIMAL NOT NULL CHECK (contradiction_score >= 0 AND contradiction_score <= 1),
    
    -- Price data
    price_pattern TEXT NOT NULL,
    historical_case_date TEXT NOT NULL,
    
    -- Behavioral flags
    behavior_flags JSONB DEFAULT '[]'::JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Historical cases table (pre-seeded outcomes)
CREATE TABLE IF NOT EXISTS historical_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker TEXT NOT NULL,
    event_type TEXT NOT NULL,
    date DATE NOT NULL,
    horizon_days INT NOT NULL CHECK (horizon_days > 0),
    
    -- Price data
    day0_price DECIMAL NOT NULL,
    day_h_price DECIMAL NOT NULL,
    price_path JSONB NOT NULL,
    return_pct DECIMAL NOT NULL,
    
    -- Metadata
    sector TEXT,
    volatility DECIMAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Behavioral profiles table (aggregate player stats)
CREATE TABLE IF NOT EXISTS behavioral_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id TEXT NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    
    -- Profile classification
    profile TEXT NOT NULL CHECK (profile IN ('Rational', 'Emotional', 'Conservative', 'Balanced')),
    
    -- Metrics
    total_rounds INT NOT NULL,
    data_tab_usage DECIMAL NOT NULL,
    consensus_alignment DECIMAL NOT NULL,
    followed_villain_high_contradiction INT NOT NULL DEFAULT 0,
    panic_sells INT NOT NULL DEFAULT 0,
    chased_spikes INT NOT NULL DEFAULT 0,
    total_pl DECIMAL NOT NULL,
    beat_villain BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Coaching
    coaching_tips JSONB NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_portfolios_player ON portfolios(player_id);
CREATE INDEX IF NOT EXISTS idx_portfolios_created ON portfolios(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_positions_portfolio ON positions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_positions_ticker ON positions(ticker);
CREATE INDEX IF NOT EXISTS idx_game_portfolio ON game_sessions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_games_completed ON game_sessions(completed_at DESC) WHERE completed_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_rounds_ticker ON game_rounds(ticker);
CREATE INDEX IF NOT EXISTS idx_rounds_created ON game_rounds(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tracker_round ON decision_tracker(round_id);
CREATE INDEX IF NOT EXISTS idx_historical_ticker ON historical_cases(ticker);
CREATE INDEX IF NOT EXISTS idx_historical_event_type ON historical_cases(event_type);
CREATE INDEX IF NOT EXISTS idx_historical_date ON historical_cases(date);
CREATE INDEX IF NOT EXISTS idx_historical_ticker_event ON historical_cases(ticker, event_type);
CREATE INDEX IF NOT EXISTS idx_profile_game ON behavioral_profiles(game_id);

-- Enable Row Level Security (RLS) for multi-tenancy
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_rounds ENABLE ROW LEVEL SECURITY;
ALTER TABLE decision_tracker ENABLE ROW LEVEL SECURITY;
ALTER TABLE behavioral_profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policies (allow all for MVP, tighten in production)
CREATE POLICY "Enable all operations for all users" ON portfolios FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON positions FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON game_sessions FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON game_rounds FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON decision_tracker FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON behavioral_profiles FOR ALL USING (true);

-- Historical cases are public (read-only)
CREATE POLICY "Enable read access for all users" ON historical_cases FOR SELECT USING (true);

-- Functions for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_portfolios_updated_at
    BEFORE UPDATE ON portfolios
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at
    BEFORE UPDATE ON positions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE portfolios IS 'Player portfolios with stock allocations';
COMMENT ON TABLE positions IS 'Individual stock positions within portfolios (shares, prices, allocations)';
COMMENT ON TABLE game_sessions IS 'Game sessions linking portfolios to rounds';
COMMENT ON TABLE game_rounds IS 'Individual rounds with events, decisions, and outcomes';
COMMENT ON TABLE decision_tracker IS 'Behavioral analysis data for each round';
COMMENT ON TABLE historical_cases IS 'Pre-seeded historical price paths for outcome replay';
COMMENT ON TABLE behavioral_profiles IS 'Final behavioral profile and coaching for each game';
