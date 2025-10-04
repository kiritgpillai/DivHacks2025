# Database Setup Guide

This folder contains the database schema and seeding scripts for Market Mayhem.

## Overview

- **`schema.sql`**: PostgreSQL schema with all tables, indexes, and RLS policies
- **`seed_historical_cases.py`**: Python script to populate historical price data

## Setup Instructions

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Wait for the project to initialize
3. Go to Settings → Database → Connection String
4. Copy the "URI" connection string

### 2. Update Environment Variables

Add to your `.env` file:

```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/postgres
```

### 3. Run Schema Migration

```bash
# Option A: Using Supabase Dashboard
# 1. Go to SQL Editor in Supabase dashboard
# 2. Paste contents of schema.sql
# 3. Click "Run"

# Option B: Using psql command-line
psql $DATABASE_URL -f database/schema.sql
```

### 4. Seed Historical Cases

```bash
# Install dependencies
pip install yfinance asyncpg python-dotenv

# Run seeder
python database/seed_historical_cases.py
```

This will:
- Fetch real historical price data using yfinance
- Generate 200 historical cases (20 per ticker)
- Populate the `historical_cases` table

Expected output:
```
Processing AAPL...
  ✅ Case 1/20: 2023-05-15 | Return: 4.28% | Volatility: 1.52%
  ✅ Case 2/20: 2023-08-22 | Return: -2.14% | Volatility: 1.85%
  ...

✅ Successfully seeded 200 historical cases
```

## Database Schema

### Tables

1. **portfolios**: Player portfolios with stock allocations
2. **game_sessions**: Game sessions linking portfolios to rounds
3. **game_rounds**: Individual rounds with events, decisions, and outcomes
4. **decision_tracker**: Behavioral analysis data for each round
5. **historical_cases**: Pre-seeded historical price paths for outcome replay ⭐
6. **behavioral_profiles**: Final behavioral profile and coaching for each game

### Key Features

- **Row Level Security (RLS)** enabled for multi-tenancy
- **Indexes** for fast queries
- **Foreign keys** for data integrity
- **Check constraints** for validation
- **Timestamps** for audit trail

## Verification

After setup, verify the data:

```sql
-- Check historical cases
SELECT 
    ticker,
    COUNT(*) as cases,
    AVG(return_pct) * 100 as avg_return
FROM historical_cases
GROUP BY ticker;

-- Sample historical case
SELECT * FROM historical_cases LIMIT 1;
```

## Repository Implementation (Optional)

To use the database in your backend, create repository classes:

```python
# backend/infrastructure/db/supabase_portfolio_repository.py
class SupabasePortfolioRepository:
    async def save(self, portfolio: Portfolio):
        # Save portfolio to database
        pass
    
    async def get(self, portfolio_id: str) -> Portfolio:
        # Fetch portfolio from database
        pass
```

Then inject into handlers:

```python
# backend/main.py
portfolio_repo = SupabasePortfolioRepository(database_url)
create_portfolio_handler = CreatePortfolioHandler(portfolio_repo)
```

## Troubleshooting

### Connection Error

If you get "connection refused":
- Check DATABASE_URL is correct
- Verify Supabase project is running
- Check firewall/network settings

### Insufficient Data

If seeding fails with "insufficient data":
- Some tickers may not have enough historical data
- The script will skip those cases automatically
- You should still get 150-200 cases total

### Permission Denied

If you get permission errors:
- Ensure RLS policies are created (check schema.sql)
- For MVP, policies allow all operations
- Tighten security in production

## Production Considerations

1. **Tighten RLS Policies**: Replace "allow all" with proper user-based policies
2. **Add Authentication**: Integrate with Supabase Auth
3. **Backup Strategy**: Enable Supabase's point-in-time recovery
4. **Monitoring**: Set up query performance monitoring
5. **Scaling**: Use connection pooling (PgBouncer) for high traffic

## Next Steps

After database setup:
1. Update backend handlers to use repositories
2. Test persistence with `test_backend.py`
3. Deploy to production
