'use client'

import Link from 'next/link'
import SpritesheetBackground from './components/SpritesheetBackground'
import JsonSpritesheetBackground from './components/JsonSpritesheetBackground'

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
      

      
      {/* Heading Image - At the top */}
      <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10">
        <img 
          src="/Heading.png" 
          alt="Market Mayhem"
          className="max-w-2xl w-full h-auto"
        />
      </div>

      {/* Villain Animation - Slightly below center */}
      <div className="absolute left-1/2 transform -translate-x-1/2 z-10" style={{top: 'calc(50% + 50px)', transform: 'translateX(-50%) translateY(-50%)'}}>
        <JsonSpritesheetBackground
          spritesheetPath="/villan.png"
          jsonPath="/villan.json"
          fps={12}
          maxWidth="400px"
          maxHeight="400px"
          className=""
        />
      </div>

      {/* CTA Button - At the bottom */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-10 text-center">
        <Link href="/portfolio">
          <div className="relative cursor-pointer transition-all hover:scale-105 shadow-lg group" style={{ maxWidth: '300px', height: 'auto' }}>
            <img 
              src="/play-button.png" 
              alt="Play Button"
              className="transition-opacity duration-300 group-hover:opacity-0 w-full h-auto"
            />
            <img 
              src="/play-buttonhovered.png" 
              alt="Play Button Hovered"
              className="absolute inset-0 transition-opacity duration-300 opacity-0 group-hover:opacity-100 w-full h-auto"
            />
          </div>
        </Link>
        <p className="mt-4 text-sm text-white">
          3 rounds • 3 decisions • Real historical data
        </p>
      </div>
    </div>
  )
}


