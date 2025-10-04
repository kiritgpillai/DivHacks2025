"""
Seed Historical Cases for Market Mayhem

This script fetches real historical price data using yfinance
and populates the historical_cases table for outcome replay.

Usage:
    python database/seed_historical_cases.py

Requirements:
    pip install yfinance asyncpg python-dotenv
"""

import asyncio
import asyncpg
import yfinance as yf
from datetime import datetime, timedelta
import random
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'WMT']
EVENT_TYPES = [
    'EARNINGS_SURPRISE',
    'REGULATORY_NEWS',
    'ANALYST_ACTION',
    'VOLATILITY_SPIKE',
    'PRODUCT_NEWS',
    'MACRO_EVENT'
]
HORIZON_OPTIONS = [2, 3, 4, 5]  # Trading days
CASES_PER_TICKER = 20  # Number of historical cases to generate per ticker


async def fetch_historical_data(ticker: str, days_back: int, horizon: int):
    """Fetch historical price data for a ticker"""
    try:
        stock = yf.Ticker(ticker)
        end_date = datetime.now() - timedelta(days=days_back)
        start_date = end_date - timedelta(days=horizon + 10)  # Extra buffer
        
        hist = stock.history(start=start_date, end=end_date)
        
        if len(hist) < horizon + 1:
            return None
        
        # Extract price path
        price_path = hist['Close'].tolist()[:horizon + 1]
        day0_price = float(price_path[0])
        day_h_price = float(price_path[min(horizon, len(price_path) - 1)])
        return_pct = (day_h_price - day0_price) / day0_price
        
        return {
            'ticker': ticker,
            'date': start_date.date(),
            'horizon': horizon,
            'day0_price': day0_price,
            'day_h_price': day_h_price,
            'price_path': [float(p) for p in price_path],
            'return_pct': float(return_pct),
            'volatility': float(hist['Close'].pct_change().std()) if len(hist) > 1 else 0.0
        }
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return None


async def seed_database():
    """Seed the historical_cases table"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL not set in environment variables")
        print("Please set DATABASE_URL in your .env file")
        return
    
    print("Connecting to database...")
    conn = await asyncpg.connect(database_url)
    
    try:
        # Clear existing data (optional)
        print("Clearing existing historical cases...")
        await conn.execute("DELETE FROM historical_cases")
        
        total_cases = 0
        
        for ticker in TICKERS:
            print(f"\nProcessing {ticker}...")
            
            for i in range(CASES_PER_TICKER):
                # Random parameters
                horizon = random.choice(HORIZON_OPTIONS)
                event_type = random.choice(EVENT_TYPES)
                days_back = random.randint(horizon + 10, 730)  # Between 10 days and 2 years back
                
                # Fetch data
                data = await fetch_historical_data(ticker, days_back, horizon)
                
                if not data:
                    print(f"  ⚠️  Skipping case {i+1}/{CASES_PER_TICKER} (insufficient data)")
                    continue
                
                # Insert into database
                await conn.execute("""
                    INSERT INTO historical_cases (
                        ticker, event_type, date, horizon_days,
                        day0_price, day_h_price, price_path, return_pct, volatility
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, 
                    data['ticker'],
                    event_type,
                    data['date'],
                    data['horizon'],
                    data['day0_price'],
                    data['day_h_price'],
                    data['price_path'],
                    data['return_pct'],
                    data['volatility']
                )
                
                total_cases += 1
                print(f"  ✅ Case {i+1}/{CASES_PER_TICKER}: {data['date']} | "
                      f"Return: {data['return_pct']*100:.2f}% | "
                      f"Volatility: {data['volatility']*100:.2f}%")
        
        print(f"\n{'='*60}")
        print(f"✅ Successfully seeded {total_cases} historical cases")
        print(f"{'='*60}")
        
        # Print summary stats
        stats = await conn.fetch("""
            SELECT 
                ticker,
                COUNT(*) as count,
                AVG(return_pct) * 100 as avg_return_pct,
                AVG(volatility) * 100 as avg_volatility
            FROM historical_cases
            GROUP BY ticker
            ORDER BY ticker
        """)
        
        print("\nSummary by Ticker:")
        print("-" * 60)
        for row in stats:
            print(f"{row['ticker']:7} | Cases: {row['count']:3} | "
                  f"Avg Return: {row['avg_return_pct']:6.2f}% | "
                  f"Avg Volatility: {row['avg_volatility']:5.2f}%")
        
    finally:
        await conn.close()
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║          Market Mayhem - Historical Cases Seeder          ║
    ╚═══════════════════════════════════════════════════════════╝
    
    This will populate the historical_cases table with real
    historical price data for outcome replay.
    
    """)
    
    asyncio.run(seed_database())
    
    print("\n✅ Seeding complete!")
    print("\nNext steps:")
    print("  1. Verify data: SELECT * FROM historical_cases LIMIT 10;")
    print("  2. Test backend: python test_backend.py")
    print("  3. Start game!")
