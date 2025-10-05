'use client'

import Link from 'next/link'
import SpritesheetBackground from './components/SpritesheetBackground'

export default function HomePage() {
  return (
    <div className="min-h-screen relative flex flex-col items-center justify-center p-8">
      {/* Dashboard Spritesheet Animation - High Quality */}
      <SpritesheetBackground
        spritesheetPath="/animations/Sprite.png"
        frameWidth={1920}
        frameHeight={1080}
        totalFrames={53}
        framesPerRow={53}
        fps={8}
        className=""
      />
      

      
      {/* Main Content */}
      <div className="max-w-4xl text-center relative z-10">
        {/* Logo/Title */}
        <h1 className="text-6xl font-bold mb-4 text-white">
          Market Mayhem
        </h1>
        
        <p className="text-xl text-gray-300 mb-96">
          Face the Villain AI. Master your biases. Win the game.
        </p>

        {/* CTA Button - PNG Image */}
        <Link href="/portfolio">
          <img 
            src="/play-button.png" 
            alt="Play Button"
            className="cursor-pointer transition-all hover:scale-105 shadow-lg"
            style={{ maxWidth: '300px', height: 'auto' }}
          />
        </Link>

        <p className="mt-6 text-sm text-gray-400">
          3 rounds • 3 decisions • Real historical data
        </p>
      </div>
    </div>
  )
}


