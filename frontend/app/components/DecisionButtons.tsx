import { motion } from 'framer-motion'
import { TrendingDown, MinusCircle, Circle, TrendingUp } from 'lucide-react'

interface DecisionButtonsProps {
  onDecision: (decision: string) => void
}

const decisions = [
  {
    value: 'SELL_ALL',
    label: 'SELL ALL',
    description: 'Exit entire position',
    icon: TrendingDown,
    color: 'from-red-600 to-red-700 hover:from-red-700 hover:to-red-800',
    textColor: 'text-red-100'
  },
  {
    value: 'SELL_HALF',
    label: 'SELL HALF',
    description: 'Lock in 50%, reduce risk',
    icon: MinusCircle,
    color: 'from-orange-600 to-orange-700 hover:from-orange-700 hover:to-orange-800',
    textColor: 'text-orange-100'
  },
  {
    value: 'HOLD',
    label: 'HOLD',
    description: 'Maintain current position',
    icon: Circle,
    color: 'from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800',
    textColor: 'text-blue-100'
  },
  {
    value: 'BUY',
    label: 'BUY MORE',
    description: 'Add 10% to position',
    icon: TrendingUp,
    color: 'from-green-600 to-green-700 hover:from-green-700 hover:to-green-800',
    textColor: 'text-green-100'
  }
]

export default function DecisionButtons({ onDecision }: DecisionButtonsProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="bg-gray-800 border border-gray-700 rounded-lg p-6"
    >
      <h3 className="text-xl font-bold text-white mb-4">Make Your Decision</h3>
      <p className="text-gray-400 mb-6 text-sm">
        Choose wisely. Your decision will be applied to the historical price path.
      </p>

      <div className="grid grid-cols-2 gap-4">
        {decisions.map((decision, idx) => (
          <motion.button
            key={decision.value}
            onClick={() => onDecision(decision.value)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 + idx * 0.1 }}
            className={`bg-gradient-to-br ${decision.color} rounded-lg p-6 text-left shadow-lg transition-all border-2 border-transparent hover:border-white hover:border-opacity-20`}
          >
            <div className="flex items-start gap-3 mb-3">
              <decision.icon className={`w-6 h-6 ${decision.textColor} flex-shrink-0 mt-1`} />
              <div className="flex-1">
                <h4 className="text-xl font-bold text-white mb-1">
                  {decision.label}
                </h4>
                <p className={`text-sm ${decision.textColor}`}>
                  {decision.description}
                </p>
              </div>
            </div>
          </motion.button>
        ))}
      </div>

      <p className="text-xs text-gray-500 mt-4 text-center">
        Your decision time and data tab usage will be tracked
      </p>
    </motion.div>
  )
}
