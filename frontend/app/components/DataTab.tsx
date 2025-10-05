import { motion } from 'framer-motion'
import { BarChart3, TrendingUp, Info, Newspaper } from 'lucide-react'

interface DataTabProps {
  data: {
    headlines: Array<{
      title: string
      source: string
      stance?: string
    }>
    consensus: string
    contradiction_score: number
    price_pattern: string
    neutral_tip: string
    historical_outcomes?: {
      similar_cases: number
      sell_all: { median_return: number, explanation: string }
      sell_half: { median_return: number, explanation: string }
      hold: { median_return: number, explanation: string }
    }
  }
}

export default function DataTab({ data }: DataTabProps) {
  const contradictionColor = 
    data.contradiction_score > 0.7 ? 'text-red-400' :
    data.contradiction_score > 0.4 ? 'text-yellow-400' :
    'text-green-400'

  return (
    <motion.div
      className="bg-gray-800 border-2 border-green-600 rounded-lg p-6 shadow-xl"
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-6">
        <BarChart3 className="w-6 h-6 text-green-400" />
        <h3 className="text-xl font-bold text-white">Data Tab</h3>
      </div>

      {/* Neutral Tip */}
      <div className="bg-gray-900 border-l-4 border-green-500 p-4 mb-6 rounded">
        <div className="flex items-start gap-2">
          <Info className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
          <p className="text-gray-200 text-sm leading-relaxed">{data.neutral_tip}</p>
        </div>
      </div>

      {/* Headlines */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
          <Newspaper className="w-4 h-4" />
          Recent Headlines
        </h4>
        <div className="space-y-2">
          {data.headlines.map((headline, idx) => (
            <div key={idx} className="bg-gray-900 p-3 rounded text-sm">
              <div className="flex items-start justify-between gap-2 mb-1">
                <p className="text-gray-200 flex-1">{headline.title}</p>
                {headline.stance && (
                  <span className={`text-xs px-2 py-0.5 rounded flex-shrink-0 ${
                    headline.stance === 'Bull' ? 'bg-green-900 text-green-300' :
                    headline.stance === 'Bear' ? 'bg-red-900 text-red-300' :
                    'bg-gray-700 text-gray-300'
                  }`}>
                    {headline.stance}
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-500">{headline.source}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Consensus */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-900 p-4 rounded">
          <p className="text-xs text-gray-400 mb-1">Consensus</p>
          <p className="text-lg font-bold text-white">{data.consensus}</p>
        </div>
        <div className="bg-gray-900 p-4 rounded">
          <p className="text-xs text-gray-400 mb-1">Contradiction</p>
          <p className={`text-lg font-bold ${contradictionColor}`}>
            {(data.contradiction_score * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Price Pattern */}
      <div className="bg-gray-900 p-4 rounded mb-6">
        <p className="text-xs text-gray-400 mb-1">Price Pattern</p>
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-gray-400" />
          <p className="text-sm font-semibold text-white">
            {data.price_pattern.replace(/_/g, ' ').toUpperCase()}
          </p>
        </div>
      </div>

      {/* Historical Outcomes */}
      {data.historical_outcomes && 
       data.historical_outcomes.sell_all && 
       data.historical_outcomes.sell_half && 
       data.historical_outcomes.hold && (
        <div className="border-t border-gray-700 pt-4">
          <h4 className="text-sm font-semibold text-gray-400 mb-3">
            Historical Outcomes ({data.historical_outcomes.similar_cases || 0} similar cases)
          </h4>
          <div className="space-y-2 text-xs">
            <OutcomeRow
              label="SELL ALL"
              return={data.historical_outcomes.sell_all.median_return}
              explanation={data.historical_outcomes.sell_all.explanation}
            />
            <OutcomeRow
              label="SELL HALF"
              return={data.historical_outcomes.sell_half.median_return}
              explanation={data.historical_outcomes.sell_half.explanation}
            />
            <OutcomeRow
              label="HOLD"
              return={data.historical_outcomes.hold.median_return}
              explanation={data.historical_outcomes.hold.explanation}
            />
          </div>
        </div>
      )}
    </motion.div>
  )
}

function OutcomeRow({ label, return: ret, explanation }: { label: string, return: number, explanation: string }) {
  const returnColor = ret > 0 ? 'text-green-400' : ret < 0 ? 'text-red-400' : 'text-gray-400'
  
  return (
    <div className="bg-gray-800 p-2 rounded">
      <div className="flex justify-between items-center mb-1">
        <span className="font-semibold text-gray-300">{label}</span>
        <span className={`font-bold ${returnColor}`}>
          {(ret * 100).toFixed(1)}%
        </span>
      </div>
      <p className="text-gray-500">{explanation}</p>
    </div>
  )
}
