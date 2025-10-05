import { motion } from 'framer-motion'
import { Skull, AlertTriangle } from 'lucide-react'

interface VillainBubbleProps {
  villainTake: {
    text: string
    stance: string
    bias: string
  }
}

export default function VillainBubble({ villainTake }: VillainBubbleProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.2 }}
      className="bg-gradient-to-br from-villain-900 to-villain-800 border-2 border-villain-600 rounded-lg p-6 shadow-xl relative overflow-hidden"
    >
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{ backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 10px, currentColor 10px, currentColor 20px)' }} />
      </div>

      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-villain-700 p-2 rounded-lg">
            <Skull className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="text-xl font-bold text-white">The Villain's Take</h3>
            <div className="flex items-center gap-2 mt-1">
              <span className={`text-xs px-2 py-0.5 rounded-full ${
                villainTake.stance === 'Bullish' 
                  ? 'bg-green-900 text-green-300' 
                  : 'bg-red-900 text-red-300'
              }`}>
                {villainTake.stance}
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-villain-800 text-villain-300">
                {villainTake.bias}
              </span>
            </div>
          </div>
        </div>

        {/* Hot Take */}
        <div className="bg-villain-950 bg-opacity-50 border border-villain-700 rounded-lg p-4 mb-3">
          <p className="text-white text-lg font-medium leading-relaxed italic">
            "{villainTake.text}"
          </p>
        </div>

        {/* Warning */}
        <div className="flex items-start gap-2 text-villain-300 text-sm">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <p className="text-xs">
            The Villain's motives are <strong>unclear</strong>. Are they trying to help you... or mislead you?
          </p>
        </div>
      </div>
    </motion.div>
  )
}
