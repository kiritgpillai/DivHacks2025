'use client'

import { useEffect, useRef } from 'react'

interface SpritesheetBackgroundProps {
  spritesheetPath: string
  jsonPath?: string
  frameWidth?: number
  frameHeight?: number
  totalFrames?: number
  framesPerRow?: number
  fps?: number
  className?: string
}

export default function SpritesheetBackground({
  spritesheetPath,
  jsonPath,
  frameWidth = 64,
  frameHeight = 64,
  totalFrames = 16,
  framesPerRow = 4,
  fps = 12,
  className = ""
}: SpritesheetBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number>()
  const lastFrameTimeRef = useRef<number>(0)
  const currentFrameRef = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    const resizeCanvas = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    
    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    // Load spritesheet
    const img = new Image()
    img.onload = () => {
      console.log('Simple spritesheet loaded successfully')
      console.log('Image actual dimensions:', img.width, 'x', img.height)
      console.log('Frame dimensions in code:', frameWidth, 'x', frameHeight)
      console.log('Total frames:', totalFrames, 'Frames per row:', framesPerRow)
      
      const animate = (currentTime: number) => {
        // Control frame rate
        if (currentTime - lastFrameTimeRef.current >= 1000 / fps) {
          // Clear canvas
          ctx.clearRect(0, 0, canvas.width, canvas.height)
          
          // Calculate source position on spritesheet
          const frameX = (currentFrameRef.current % framesPerRow) * frameWidth
          const frameY = Math.floor(currentFrameRef.current / framesPerRow) * frameHeight
          
          // Scale to fill the entire screen (stretch to fit)
          const scaledWidth = canvas.width
          const scaledHeight = canvas.height
          
          // Draw frame stretched to fill entire screen
          ctx.drawImage(
            img,
            frameX, frameY, frameWidth, frameHeight,
            0, 0, scaledWidth, scaledHeight
          )
          
          // Move to next frame
          currentFrameRef.current = (currentFrameRef.current + 1) % totalFrames
          lastFrameTimeRef.current = currentTime
        }
        
        animationRef.current = requestAnimationFrame(animate)
      }
      
      animate(0)
    }
    
    img.onerror = (error) => {
      console.error('Failed to load simple spritesheet:', spritesheetPath, error)
    }
    
    console.log('Loading simple spritesheet from:', spritesheetPath)
    img.src = spritesheetPath

    return () => {
      window.removeEventListener('resize', resizeCanvas)
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [spritesheetPath, frameWidth, frameHeight, totalFrames, framesPerRow, fps])

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 ${className}`}
      style={{ 
        pointerEvents: 'none',
        zIndex: -1
      }}
    />
  )
}