'use client'

import Link from 'next/link'
import { TrendingUp, Brain, Zap, Target } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex flex-col items-center justify-center p-8">
      <div className="max-w-4xl text-center">
        {/* Logo/Title */}
        <h1 className="text-6xl font-bold mb-4 text-white">
          Market Mayhem
        </h1>
        
        <p className="text-xl text-gray-300 mb-12">
          Face the Villain AI. Master your biases. Win the game.
        </p>

        {/* Features */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <FeatureCard
            icon={<TrendingUp className="w-8 h-8" />}
            title="Real Market Data"
            description="Historical outcomes, not random"
          />
          <FeatureCard
            icon={<Brain className="w-8 h-8" />}
            title="6 AI Agents"
            description="Multi-agent system powered by LangGraph"
          />
          <FeatureCard
            icon={<Zap className="w-8 h-8" />}
            title="Villain AI"
            description="Trash-talking hot takes to mislead you"
          />
          <FeatureCard
            icon={<Target className="w-8 h-8" />}
            title="Behavioral Coaching"
            description="Learn your investing psychology"
          />
        </div>

        {/* CTA Button */}
        <Link href="/portfolio">
          <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold text-lg px-12 py-4 rounded-lg shadow-lg transition-all hover:scale-105">
            Build Your Portfolio & Start Playing
          </button>
        </Link>

        <p className="mt-6 text-sm text-gray-400">
          5 rounds • 5 decisions • Real historical data
        </p>
      </div>
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <div className="bg-gray-800 bg-opacity-50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 text-center hover:scale-105 transition-transform">
      <div className="text-blue-400 mb-3 flex justify-center">{icon}</div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-sm text-gray-400">{description}</p>
    </div>
  )
}
