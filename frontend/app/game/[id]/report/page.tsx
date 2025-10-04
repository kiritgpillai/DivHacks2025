'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Award, TrendingUp, Brain, Target, Home, BarChart3 } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Report {
  profile: string
  coaching: string[]
  summary: {
    total_rounds: number
    final_portfolio_value: number
    total_pl: number
    total_return_pct: number
    data_tab_usage: number
    consensus_alignment: number
  }
  metrics: {
    total_rounds: number
    data_tab_usage: number
    consensus_alignment: number
    followed_villain_high_contradiction: number
    panic_sells: number
    chased_spikes: number
    total_pl: number
    beat_villain: boolean
  }
}

export default function ReportPage() {
  const params = useParams()
  const router = useRouter()
  const gameId = params.id as string

  const [report, setReport] = useState<Report | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_URL}/game/${gameId}/report`)
      .then(res => res.json())
      .then(data => {
        setReport(data.report)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [gameId])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Generating your final report...</p>
        </div>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="bg-red-900 bg-opacity-30 border border-red-500 rounded-lg p-8 max-w-md">
          <h2 className="text-2xl font-bold text-red-300 mb-4">Error</h2>
          <p className="text-red-200">{error || 'Failed to load report'}</p>
        </div>
      </div>
    )
  }

  const profileColors = {
    'Rational': 'from-blue-600 to-blue-700',
    'Emotional': 'from-red-600 to-red-700',
    'Conservative': 'from-green-600 to-green-700',
    'Balanced': 'from-purple-600 to-purple-700'
  }

  const profileColor = profileColors[report.profile as keyof typeof profileColors] || profileColors['Balanced']

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {/* Header */}
          <div className="text-center mb-12">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15 }}
              className="inline-block bg-gradient-to-br from-yellow-500 to-yellow-600 p-4 rounded-full mb-4"
            >
              <Award className="w-12 h-12 text-white" />
            </motion.div>
            <h1 className="text-4xl font-bold text-white mb-2">Game Complete!</h1>
            <p className="text-gray-400">Here's your behavioral profile and coaching</p>
          </div>

          {/* Profile Badge */}
          <div className={`bg-gradient-to-br ${profileColor} rounded-lg p-8 mb-8 text-center shadow-xl`}>
            <Brain className="w-12 h-12 text-white mx-auto mb-4" />
            <h2 className="text-3xl font-bold text-white mb-2">Your Profile</h2>
            <p className="text-2xl font-semibold text-white text-opacity-90">{report.profile}</p>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatCard
              icon={<BarChart3 className="w-6 h-6" />}
              label="Final Value"
              value={`$${report.summary.final_portfolio_value.toLocaleString()}`}
              subValue={`${report.summary.total_return_pct > 0 ? '+' : ''}${report.summary.total_return_pct.toFixed(2)}%`}
              color="text-primary-400"
            />
            <StatCard
              icon={<TrendingUp className="w-6 h-6" />}
              label="Total P/L"
              value={`$${report.summary.total_pl.toLocaleString()}`}
              color={report.summary.total_pl >= 0 ? 'text-green-400' : 'text-red-400'}
            />
            <StatCard
              icon={<Target className="w-6 h-6" />}
              label="Data Tab Usage"
              value={`${(report.summary.data_tab_usage * 100).toFixed(0)}%`}
              color="text-green-400"
            />
            <StatCard
              icon={<Brain className="w-6 h-6" />}
              label="Consensus Align"
              value={`${(report.summary.consensus_alignment * 100).toFixed(0)}%`}
              color="text-blue-400"
            />
          </div>

          {/* Coaching Tips */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-8">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <Target className="w-6 h-6 text-primary-400" />
              Personalized Coaching
            </h3>
            <div className="space-y-3">
              {report.coaching.map((tip, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="flex gap-3 bg-gray-900 p-4 rounded-lg"
                >
                  <span className="text-primary-400 font-bold flex-shrink-0">{idx + 1}.</span>
                  <p className="text-gray-200">{tip}</p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Detailed Metrics */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-8">
            <h3 className="text-xl font-bold text-white mb-4">Detailed Metrics</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <MetricRow label="Followed Villain (High Contradiction)" value={report.metrics.followed_villain_high_contradiction} />
              <MetricRow label="Panic Sells" value={report.metrics.panic_sells} />
              <MetricRow label="Chased Spikes" value={report.metrics.chased_spikes} />
              <MetricRow label="Beat the Villain" value={report.metrics.beat_villain ? 'Yes' : 'No'} />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4">
            <button
              onClick={() => router.push('/portfolio')}
              className="flex-1 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white font-bold py-4 rounded-lg flex items-center justify-center gap-2 transition-all"
            >
              <Target className="w-5 h-5" />
              Play Again
            </button>
            <button
              onClick={() => router.push('/')}
              className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-4 rounded-lg flex items-center justify-center gap-2 transition-all"
            >
              <Home className="w-5 h-5" />
              Home
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, subValue, color }: { icon: React.ReactNode, label: string, value: string, subValue?: string, color: string }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
      <div className={`${color} mb-2`}>{icon}</div>
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className="text-lg font-bold text-white">{value}</p>
      {subValue && <p className="text-xs text-gray-400">{subValue}</p>}
    </div>
  )
}

function MetricRow({ label, value }: { label: string, value: number | string }) {
  return (
    <div className="flex justify-between bg-gray-900 p-3 rounded">
      <span className="text-gray-400">{label}:</span>
      <span className="text-white font-semibold">{value}</span>
    </div>
  )
}
