import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, ArrowRight, Award } from 'lucide-react'

interface OutcomeModalProps {
  outcome: {
    pl_dollars: number
    pl_percent: number
    outcome: {
      explanation: string
      historical_case_used?: {
        date: string
        ticker: string
        day0_price: number
        day_h_price: number
      }
    }
    behavior_flags?: string[]
  }
  onNextRound: () => void
  isLastRound: boolean
}

export default function OutcomeModal({ outcome, onNextRound, isLastRound }: OutcomeModalProps) {
  const isProfit = outcome.pl_dollars > 0
  const Icon = isProfit ? TrendingUp : TrendingDown

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center p-8 z-50"
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        className="bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-gray-700 rounded-lg p-8 max-w-2xl w-full shadow-2xl"
      >
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <div className={`p-3 rounded-full ${isProfit ? 'bg-green-900 bg-opacity-50' : 'bg-red-900 bg-opacity-50'}`}>
            <Icon className={`w-8 h-8 ${isProfit ? 'text-green-400' : 'text-red-400'}`} />
          </div>
          <div>
            <h2 className="text-3xl font-bold text-white">Round Complete!</h2>
            <p className="text-gray-400">Here's what happened...</p>
          </div>
        </div>

        {/* P/L Display */}
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 mb-6">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-gray-400 mb-1">P/L (Dollars)</p>
              <p className={`text-3xl font-bold ${isProfit ? 'text-green-400' : 'text-red-400'}`}>
                {isProfit ? '+' : ''}${outcome.pl_dollars.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-1">P/L (Percent)</p>
              <p className={`text-3xl font-bold ${isProfit ? 'text-green-400' : 'text-red-400'}`}>
                {isProfit ? '+' : ''}{(outcome.pl_percent * 100).toFixed(2)}%
              </p>
            </div>
          </div>
        </div>

        {/* Explanation */}
        <div className="bg-gray-900 border-l-4 border-primary-500 rounded p-4 mb-6">
          <p className="text-gray-200 leading-relaxed">{outcome.outcome.explanation}</p>
        </div>

        {/* Historical Case Info */}
        {outcome.outcome.historical_case_used && (
          <div className="bg-gray-900 rounded p-4 mb-6 text-sm">
            <p className="text-gray-400 mb-2">Historical Case Used:</p>
            <div className="grid grid-cols-2 gap-4 text-gray-300">
              <div>
                <span className="text-gray-500">Ticker:</span> {outcome.outcome.historical_case_used.ticker}
              </div>
              <div>
                <span className="text-gray-500">Date:</span> {outcome.outcome.historical_case_used.date}
              </div>
              <div>
                <span className="text-gray-500">Day 0 Price:</span> ${outcome.outcome.historical_case_used.day0_price.toFixed(2)}
              </div>
              <div>
                <span className="text-gray-500">Final Price:</span> ${outcome.outcome.historical_case_used.day_h_price.toFixed(2)}
              </div>
            </div>
          </div>
        )}

        {/* Behavior Flags */}
        {outcome.behavior_flags && outcome.behavior_flags.length > 0 && (
          <div className="bg-yellow-900 bg-opacity-20 border border-yellow-700 rounded p-4 mb-6">
            <p className="text-yellow-300 text-sm font-semibold mb-2">🧠 Behavioral Insights:</p>
            <ul className="text-yellow-200 text-sm space-y-1">
              {outcome.behavior_flags.map((flag, idx) => (
                <li key={idx}>• {flag.replace(/_/g, ' ')}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Next Round Button */}
        <button
          onClick={onNextRound}
          className="w-full bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white font-bold text-lg py-4 rounded-lg flex items-center justify-center gap-2 transition-all"
        >
          {isLastRound ? (
            <>
              <Award className="w-5 h-5" />
              View Final Report
            </>
          ) : (
            <>
              Next Round
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </button>
      </motion.div>
    </motion.div>
  )
}
