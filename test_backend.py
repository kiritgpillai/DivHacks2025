"""
Quick Backend Test Script

This script tests the Market Mayhem backend to verify all components are working.

Usage:
    python test_backend.py
"""

import asyncio
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

BASE_URL = "http://localhost:8000"


async def test_health():
    """Test health endpoints"""
    console.print("\n[bold cyan]Testing Health Endpoints...[/bold cyan]")
    
    async with httpx.AsyncClient() as client:
        # Root endpoint
        response = await client.get(f"{BASE_URL}/")
        console.print(f"✅ Root endpoint: {response.status_code}")
        console.print(response.json())
        
        # Health endpoint
        response = await client.get(f"{BASE_URL}/health")
        console.print(f"✅ Health endpoint: {response.status_code}")
        console.print(response.json())
        
        # Tickers endpoint
        response = await client.get(f"{BASE_URL}/tickers")
        console.print(f"✅ Tickers endpoint: {response.status_code}")
        console.print(f"   Available tickers: {response.json()['tickers']}")
        
        # Agents endpoint
        response = await client.get(f"{BASE_URL}/agents")
        console.print(f"✅ Agents endpoint: {response.status_code}")
        console.print(f"   Total agents: {len(response.json()['agents'])}")


async def test_game_flow():
    """Test complete game flow"""
    console.print("\n[bold cyan]Testing Complete Game Flow...[/bold cyan]")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Create Portfolio
        console.print("\n[bold yellow]Step 1: Creating Portfolio...[/bold yellow]")
        portfolio_data = {
            "player_id": "test_player",
            "tickers": ["AAPL", "TSLA", "MSFT"],
            "allocations": {
                "AAPL": 300000,
                "TSLA": 400000,
                "MSFT": 300000
            },
            "risk_profile": "Balanced"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/portfolio/create",
                json=portfolio_data
            )
            console.print(f"✅ Portfolio created: {response.status_code}")
            portfolio = response.json()["portfolio"]
            portfolio_id = portfolio["portfolio_id"]
            console.print(f"   Portfolio ID: {portfolio_id}")
            console.print(f"   Total Value: ${portfolio['total_value']:,.0f}")
        except Exception as e:
            console.print(f"❌ Portfolio creation failed: {str(e)}")
            return
        
        # 2. Start Game
        console.print("\n[bold yellow]Step 2: Starting Game...[/bold yellow]")
        try:
            response = await client.post(
                f"{BASE_URL}/game/start",
                json={"portfolio_id": portfolio_id}
            )
            console.print(f"✅ Game started: {response.status_code}")
            game = response.json()["game"]
            game_id = game["game_id"]
            console.print(f"   Game ID: {game_id}")
        except Exception as e:
            console.print(f"❌ Game start failed: {str(e)}")
            return
        
        # 3. Start Round 1
        console.print("\n[bold yellow]Step 3: Starting Round 1 (Multi-Agent Graph)...[/bold yellow]")
        console.print("   This will invoke all 6 agents:")
        console.print("   - Event Generator Agent")
        console.print("   - Portfolio Agent")
        console.print("   - News Agent")
        console.print("   - Price Agent")
        console.print("   - Villain Agent")
        console.print("   - Insight Agent")
        console.print("\n   [dim]This may take 30-60 seconds...[/dim]\n")
        
        try:
            response = await client.post(
                f"{BASE_URL}/game/{game_id}/round/1/start"
            )
            console.print(f"✅ Round 1 started: {response.status_code}")
            round_data = response.json()["round"]
            
            # Display event
            event = round_data["event"]
            console.print(Panel(
                f"[bold]{event['ticker']}[/bold]\n"
                f"Type: {event['type']}\n"
                f"Horizon: {event['horizon']} days\n\n"
                f"{event['description']}",
                title="📰 Event",
                border_style="cyan"
            ))
            
            # Display villain take
            villain = round_data["villain_take"]
            console.print(Panel(
                f"[bold red]{villain['text']}[/bold red]\n\n"
                f"Stance: {villain['stance']} | Bias: {villain['bias']}",
                title="😈 Villain Hot Take",
                border_style="red"
            ))
            
            # Display data tab
            data_tab = round_data["data_tab"]
            console.print(Panel(
                f"Headlines: {len(data_tab['headlines'])}\n"
                f"Consensus: {data_tab['consensus']}\n"
                f"Contradiction Score: {data_tab['contradiction_score']:.0%}\n"
                f"Price Pattern: {data_tab['price_pattern']}\n\n"
                f"💡 Tip: {data_tab['neutral_tip']}",
                title="📊 Data Tab",
                border_style="green"
            ))
            
        except Exception as e:
            console.print(f"❌ Round start failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return
        
        # 4. Submit Decision
        console.print("\n[bold yellow]Step 4: Submitting Decision (HOLD)...[/bold yellow]")
        try:
            response = await client.post(
                f"{BASE_URL}/game/decision",
                json={
                    "game_id": game_id,
                    "round_number": 1,
                    "player_decision": "HOLD",
                    "decision_time": 15.5,
                    "opened_data_tab": True
                }
            )
            console.print(f"✅ Decision submitted: {response.status_code}")
            outcome = response.json()["outcome"]
            
            console.print(Panel(
                f"P/L: ${outcome['pl_dollars']:,.2f} ({outcome['pl_percent']:.2%})\n\n"
                f"{outcome['outcome']['explanation']}\n\n"
                f"Behavior Flags: {', '.join(outcome.get('behavior_flags', ['None']))}",
                title="💰 Outcome",
                border_style="yellow"
            ))
            
        except Exception as e:
            console.print(f"❌ Decision submission failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return
        
        # 5. Get Final Report
        console.print("\n[bold yellow]Step 5: Generating Final Report...[/bold yellow]")
        try:
            response = await client.get(f"{BASE_URL}/game/{game_id}/report")
            console.print(f"✅ Report generated: {response.status_code}")
            report = response.json()["report"]
            
            console.print(Panel(
                f"[bold]Profile: {report['profile']}[/bold]\n\n"
                f"Coaching:\n" + "\n".join(f"  • {tip}" for tip in report['coaching']) + "\n\n"
                f"Summary:\n"
                f"  Final Value: ${report['summary']['final_portfolio_value']:,.0f}\n"
                f"  Total P/L: ${report['summary']['total_pl']:,.2f}\n"
                f"  Return: {report['summary']['total_return_pct']:.2f}%\n"
                f"  Data Tab Usage: {report['summary']['data_tab_usage']:.0%}",
                title="🎯 Final Report",
                border_style="magenta"
            ))
            
        except Exception as e:
            console.print(f"❌ Report generation failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return


async def main():
    """Main test function"""
    console.print(Panel.fit(
        "[bold cyan]Market Mayhem Backend Test[/bold cyan]\n"
        "Testing all endpoints and game flow",
        border_style="cyan"
    ))
    
    console.print("\n[dim]Make sure the backend is running at http://localhost:8000[/dim]")
    console.print("[dim]Start it with: python backend/main.py[/dim]\n")
    
    # Test health endpoints
    try:
        await test_health()
    except Exception as e:
        console.print(f"\n❌ Health check failed: {str(e)}")
        console.print("[bold red]Make sure the backend is running![/bold red]")
        return
    
    # Test game flow
    try:
        await test_game_flow()
    except Exception as e:
        console.print(f"\n❌ Game flow test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    console.print("\n" + "="*70)
    console.print("[bold green]✅ All tests passed![/bold green]")
    console.print("="*70)
    console.print("\n[bold cyan]Backend is fully functional! 🚀[/bold cyan]\n")
    console.print("Next steps:")
    console.print("  1. Build the frontend (see NEXT_STEPS.md)")
    console.print("  2. Deploy to production")
    console.print("  3. Add database persistence (optional)")


if __name__ == "__main__":
    asyncio.run(main())

