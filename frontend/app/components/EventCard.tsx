import { motion } from 'framer-motion'
import { Newspaper, TrendingUp, Clock } from 'lucide-react'

interface EventCardProps {
  event: {
    ticker: string
    type: string
    description: string
    horizon: number
  }
}

export default function EventCard({ event }: EventCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-primary-600 rounded-lg p-6 shadow-xl"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="bg-primary-600 p-2 rounded-lg">
          <Newspaper className="w-6 h-6 text-white" />
        </div>
        <div className="flex-1">
          <h2 className="text-2xl font-bold text-white">{event.ticker}</h2>
          <p className="text-sm text-gray-400">{String(event.type ?? '').replace(/_/g, ' ') || '—'}</p>
        </div>
        <div className="flex items-center gap-2 bg-gray-700 px-3 py-1 rounded-full">
          <Clock className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-300">{event.horizon}d horizon</span>
        </div>
      </div>

      {/* Description */}
      <div className="bg-gray-900 bg-opacity-50 border border-gray-700 rounded-lg p-4">
        <p className="text-gray-200 leading-relaxed">{event.description}</p>
      </div>

      {/* Footer */}
      <div className="mt-4 flex items-center gap-2 text-sm text-gray-400">
        <TrendingUp className="w-4 h-4" />
        <span>What's your move?</span>
      </div>
    </motion.div>
  )
}
