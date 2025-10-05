'use client'

import { useEffect, useRef, useState } from 'react'

interface FrameData {
  frame: {
    x: number
    y: number
    w: number
    h: number
  }
  sourceSize: {
    w: number
    h: number
  }
}

interface SpritesheetData {
  frames: Record<string, FrameData> | FrameData[]
  meta: {
    size: {
      w: number
      h: number
    }
  }
}

interface JsonSpritesheetBackgroundProps {
  spritesheetPath: string
  jsonPath: string
  fps?: number
  className?: string
  scale?: number
  maxWidth?: string
  maxHeight?: string
}

export default function JsonSpritesheetBackground({
  spritesheetPath,
  jsonPath,
  fps = 12,
  className = "",
  scale = 1,
  maxWidth = "400px",
  maxHeight = "300px"
}: JsonSpritesheetBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number>()
  const lastFrameTimeRef = useRef<number>(0)
  const currentFrameRef = useRef<number>(0)
  const [spriteData, setSpriteData] = useState<SpritesheetData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Load JSON data
  useEffect(() => {
    console.log('Loading JSON from:', jsonPath)
    fetch(jsonPath)
      .then(response => {
        console.log('JSON response status:', response.status)
        return response.json()
      })
      .then((data: SpritesheetData) => {
        console.log('Loaded spritesheet data:', data)
        setSpriteData(data)
        setIsLoading(false)
      })
      .catch(error => {
        console.error('Failed to load spritesheet JSON:', error)
        setIsLoading(false)
      })
  }, [jsonPath])

  useEffect(() => {
    if (isLoading || !spriteData) return

    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Load spritesheet image
    const img = new Image()
    img.onload = () => {
      console.log('Spritesheet image loaded successfully')
      const frames = Array.isArray(spriteData.frames) 
        ? spriteData.frames 
        : Object.values(spriteData.frames)

      console.log('Total frames:', frames.length)

      const animate = (currentTime: number) => {
        if (currentTime - lastFrameTimeRef.current >= 1000 / fps) {
          ctx.clearRect(0, 0, canvas.width, canvas.height)
          
          const currentFrame = frames[currentFrameRef.current]
          if (currentFrame) {
            const { frame } = currentFrame
            
            // Simplest approach: draw at 0,0, fill canvas
            ctx.drawImage(
              img,
              frame.x, frame.y, frame.w, frame.h,
              0, 0, canvas.width, canvas.height
            )
          }
          
          currentFrameRef.current = (currentFrameRef.current + 1) % frames.length
          lastFrameTimeRef.current = currentTime
        }
        
        animationRef.current = requestAnimationFrame(animate)
      }
      
      animate(0)
    }
    
    img.onerror = (error) => {
      console.error('Failed to load spritesheet image:', spritesheetPath, error)
    }
    
    console.log('Loading spritesheet image from:', spritesheetPath)
    img.src = spritesheetPath

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [spritesheetPath, fps, spriteData, isLoading])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    // Set canvas size based on maxWidth and maxHeight
    const maxW = parseInt(maxWidth.replace('px', ''))
    const maxH = parseInt(maxHeight.replace('px', ''))
    
    canvas.width = maxW
    canvas.height = maxH
  }, [maxWidth, maxHeight])

  if (isLoading) {
    return null
  }

  return (
    <canvas
      ref={canvasRef}
      className={`${className}`}
      style={{ 
        width: maxWidth,
        height: maxHeight
      }}
    />
  )
}