'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Minus, Plus, ArrowRight } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface TickerAllocation {
  ticker: string
  allocation: number
}

export default function PortfolioBuilderPage() {
  const router = useRouter()
  const [tickers, setTickers] = useState<string[]>([])
  const [selectedTickers, setSelectedTickers] = useState<TickerAllocation[]>([])
  const [riskProfile, setRiskProfile] = useState<string>('Balanced')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const TOTAL_BUDGET = 1_000_000

  // Fetch available tickers
  useEffect(() => {
    fetch(`${API_URL}/tickers`)
      .then(res => res.json())
      .then(data => setTickers(data.tickers))
      .catch(err => console.error('Failed to fetch tickers:', err))
  }, [])

  const totalAllocated = selectedTickers.reduce((sum, t) => sum + t.allocation, 0)
  const remaining = TOTAL_BUDGET - totalAllocated
  const isValid = Math.abs(remaining) < 1 && selectedTickers.length >= 2

  const addTicker = (ticker: string) => {
    if (selectedTickers.find(t => t.ticker === ticker)) return
    
    // Distribute remaining evenly or suggest
    const suggested = remaining / (selectedTickers.length + 1)
    setSelectedTickers([...selectedTickers, { ticker, allocation: Math.floor(suggested) }])
  }

  const removeTicker = (ticker: string) => {
    setSelectedTickers(selectedTickers.filter(t => t.ticker !== ticker))
  }

  const updateAllocation = (ticker: string, allocation: number) => {
    setSelectedTickers(
      selectedTickers.map(t => 
        t.ticker === ticker ? { ...t, allocation } : t
      )
    )
  }

  const handleCreate = async () => {
    setLoading(true)
    setError(null)

    try {
      const allocations: { [key: string]: number } = {}
      selectedTickers.forEach(t => {
        allocations[t.ticker] = t.allocation
      })

      const response = await fetch(`${API_URL}/portfolio/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_id: `player_${Date.now()}`,
          tickers: selectedTickers.map(t => t.ticker),
          allocations,
          risk_profile: riskProfile
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create portfolio')
      }

      const data = await response.json()
      const portfolioId = data.portfolio.portfolio_id

      // Start game immediately
      const gameResponse = await fetch(`${API_URL}/game/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ portfolio_id: portfolioId })
      })

      if (!gameResponse.ok) {
        throw new Error('Failed to start game')
      }

      const gameData = await gameResponse.json()
      const gameId = gameData.game.game_id

      // Navigate to game
      router.push(`/game/${gameId}`)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {/* Header */}
          <h1 className="text-4xl font-bold text-white mb-2">Build Your Portfolio</h1>
          <p className="text-gray-400 mb-8">
            Select stocks and allocate your $1,000,000 budget
          </p>

          {/* Risk Profile Selector */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Risk Profile
            </label>
            <div className="grid grid-cols-3 gap-4">
              {['Risk-Off', 'Balanced', 'Risk-On'].map(profile => (
                <button
                  key={profile}
                  onClick={() => setRiskProfile(profile)}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    riskProfile === profile
                      ? 'border-primary-500 bg-primary-900 bg-opacity-30'
                      : 'border-gray-600 bg-gray-700 hover:border-gray-500'
                  }`}
                >
                  <div className="text-white font-semibold mb-1">{profile}</div>
                  <div className="text-xs text-gray-400">
                    {profile === 'Risk-Off' && 'Max 25% per position'}
                    {profile === 'Balanced' && 'Max 33% per position'}
                    {profile === 'Risk-On' && 'Max 50% per position'}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Ticker Selector */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Available Tickers
            </label>
            <div className="flex flex-wrap gap-2">
              {tickers.map(ticker => (
                <button
                  key={ticker}
                  onClick={() => addTicker(ticker)}
                  disabled={!!selectedTickers.find(t => t.ticker === ticker)}
                  className={`px-4 py-2 rounded-md font-medium transition-all ${
                    selectedTickers.find(t => t.ticker === ticker)
                      ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                      : 'bg-primary-600 hover:bg-primary-700 text-white'
                  }`}
                >
                  {ticker}
                </button>
              ))}
            </div>
          </div>

          {/* Selected Tickers & Allocations */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Your Portfolio ({selectedTickers.length} stocks)
            </label>
            
            {selectedTickers.length === 0 ? (
              <p className="text-gray-500 text-center py-8">Select at least 2 tickers to start</p>
            ) : (
              <div className="space-y-4">
                {selectedTickers.map(({ ticker, allocation }) => (
                  <div key={ticker} className="flex items-center gap-4">
                    <button
                      onClick={() => removeTicker(ticker)}
                      className="text-red-400 hover:text-red-300"
                    >
                      <Minus className="w-5 h-5" />
                    </button>
                    
                    <div className="w-20 font-bold text-white">{ticker}</div>
                    
                    <input
                      type="range"
                      min="0"
                      max={TOTAL_BUDGET}
                      step="10000"
                      value={allocation}
                      onChange={(e) => updateAllocation(ticker, parseInt(e.target.value))}
                      className="flex-1"
                    />
                    
                    <input
                      type="number"
                      value={allocation}
                      onChange={(e) => updateAllocation(ticker, parseInt(e.target.value) || 0)}
                      className="w-32 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                    />
                    
                    <div className="w-16 text-right text-gray-400">
                      {((allocation / TOTAL_BUDGET) * 100).toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Budget Summary */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-300">Total Allocated:</span>
              <span className="text-white font-bold">${totalAllocated.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Remaining:</span>
              <span className={`font-bold ${remaining > 1000 ? 'text-yellow-400' : remaining < -1 ? 'text-red-400' : 'text-green-400'}`}>
                ${remaining.toLocaleString()}
              </span>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-900 bg-opacity-30 border border-red-500 rounded-lg p-4 mb-6 text-red-300">
              {error}
            </div>
          )}

          {/* Create Button */}
          <button
            onClick={handleCreate}
            disabled={!isValid || loading}
            className={`w-full py-4 rounded-lg font-bold text-lg flex items-center justify-center gap-2 transition-all ${
              isValid && !loading
                ? 'bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white'
                : 'bg-gray-700 text-gray-500 cursor-not-allowed'
            }`}
          >
            {loading ? 'Creating Portfolio...' : 'Start Game'}
            {!loading && <ArrowRight className="w-5 h-5" />}
          </button>
        </motion.div>
      </div>
    </div>
  )
}
