'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import EventCard from '@/app/components/EventCard'
import VillainBubble from '@/app/components/VillainBubble'
import DataTab from '@/app/components/DataTab'
import DecisionButtons from '@/app/components/DecisionButtons'
import OutcomeModal from '@/app/components/OutcomeModal'
import { Loader2 } from 'lucide-react'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

interface GameState {
  round: number
  event: any | null
  villainTake: any | null
  dataTab: any | null
  outcome: any | null
  loading: boolean
  error: string | null
}

export default function GamePage() {
  const params = useParams()
  const router = useRouter()
  const gameId = params.id as string
  
  const [state, setState] = useState<GameState>({
    round: 1,
    event: null,
    villainTake: null,
    dataTab: null,
    outcome: null,
    loading: true,
    error: null
  })
  
  const [showDataTab, setShowDataTab] = useState(false)
  const [dataTabOpenTime, setDataTabOpenTime] = useState<number | null>(null)
  const [startTime, setStartTime] = useState<number>(Date.now())
  
  const wsRef = useRef<WebSocket | null>(null)

  // WebSocket connection
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/game/${gameId}/ws`)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected')
      // Start first round
      ws.send(JSON.stringify({
        type: 'start_round',
        round_number: 1
      }))
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('Received:', data)

      if (data.type === 'round_started') {
        setState(prev => ({
          ...prev,
          event: data.data.event,
          villainTake: data.data.villain_take,
          dataTab: data.data.data_tab,
          loading: false,
          outcome: null
        }))
        setStartTime(Date.now())
      } else if (data.type === 'outcome') {
        setState(prev => ({
          ...prev,
          outcome: data.data,
          loading: false
        }))
      } else if (data.type === 'error') {
        setState(prev => ({
          ...prev,
          error: data.message,
          loading: false
        }))
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setState(prev => ({
        ...prev,
        error: 'Connection error. Please refresh.',
        loading: false
      }))
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
    }

    return () => {
      ws.close()
    }
  }, [gameId])

  const handleDecision = (decision: string) => {
    if (!wsRef.current || state.loading) return

    setState(prev => ({ ...prev, loading: true }))
    
    const decisionTime = (Date.now() - startTime) / 1000
    const openedDataTab = dataTabOpenTime !== null

    wsRef.current.send(JSON.stringify({
      type: 'submit_decision',
      round_number: state.round,
      decision,
      decision_time: decisionTime,
      opened_data_tab: openedDataTab
    }))
  }

  const handleNextRound = () => {
    if (!wsRef.current) return

    const nextRound = state.round + 1
    
    if (nextRound > 5) {
      // Game complete, show final report
      wsRef.current.send(JSON.stringify({ type: 'get_report' }))
      router.push(`/game/${gameId}/report`)
      return
    }

    setState(prev => ({
      ...prev,
      round: nextRound,
      event: null,
      villainTake: null,
      dataTab: null,
      outcome: null,
      loading: true
    }))
    
    setShowDataTab(false)
    setDataTabOpenTime(null)
    setStartTime(Date.now())

    wsRef.current.send(JSON.stringify({
      type: 'start_round',
      round_number: nextRound
    }))
  }

  const handleToggleDataTab = () => {
    if (!showDataTab && dataTabOpenTime === null) {
      setDataTabOpenTime(Date.now())
    }
    setShowDataTab(!showDataTab)
  }

  if (state.error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="bg-red-900 bg-opacity-30 border border-red-500 rounded-lg p-8 max-w-md">
          <h2 className="text-2xl font-bold text-red-300 mb-4">Error</h2>
          <p className="text-red-200">{state.error}</p>
          <button
            onClick={() => router.push('/')}
            className="mt-6 bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg"
          >
            Return Home
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">
            Round {state.round} of 5
          </h1>
          {state.dataTab && (
            <button
              onClick={handleToggleDataTab}
              className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                showDataTab
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-gray-700 hover:bg-gray-600 text-gray-300 border-2 border-dashed border-gray-500'
              }`}
            >
              {showDataTab ? 'Hide' : 'Show'} Data Tab
            </button>
          )}
        </div>

        {/* Loading State */}
        {state.loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-16 h-16 animate-spin text-primary-400 mb-4" />
            <p className="text-gray-400 text-lg">
              {state.event ? 'Processing your decision...' : 'Generating market scenario...'}
            </p>
            <p className="text-gray-500 text-sm mt-2">
              Multi-agent system at work (this may take 30-60 seconds)
            </p>
          </div>
        )}

        {/* Game Content */}
        {!state.loading && state.event && (
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Main Column */}
            <div className="lg:col-span-2 space-y-6">
              {/* Event Card */}
              <EventCard event={state.event} />

              {/* Villain Bubble */}
              {state.villainTake && (
                <VillainBubble villainTake={state.villainTake} />
              )}

              {/* Decision Buttons */}
              {!state.outcome && (
                <DecisionButtons onDecision={handleDecision} />
              )}
            </div>

            {/* Data Tab Column */}
            <div className="lg:col-span-1">
              <AnimatePresence>
                {showDataTab && state.dataTab && (
                  <motion.div
                    initial={{ opacity: 0, x: 50 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 50 }}
                  >
                    <DataTab data={state.dataTab} />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        )}

        {/* Outcome Modal */}
        {state.outcome && (
          <OutcomeModal
            outcome={state.outcome}
            onNextRound={handleNextRound}
            isLastRound={state.round === 5}
          />
        )}
      </div>
    </div>
  )
}
