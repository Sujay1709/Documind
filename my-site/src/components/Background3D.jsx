import { useMemo, useRef, useState, useEffect } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float, Sparkles, RoundedBox, AdaptiveDpr } from '@react-three/drei'

// Palette per theme. Kept in sync with index.css accents.
const THEMES = {
  light: {
    panel: '#ffffff',
    panelEmissive: '#9db4ff',
    light1: '#5b7cfa',
    light2: '#8b5cf6',
    light3: '#22c4c4',
    spark: '#6e86ff',
    fog: '#dfe6f8',
    ambient: 0.85,
    panelOpacity: 0.9,
  },
  dark: {
    panel: '#132550',
    panelEmissive: '#3355aa',
    light1: '#6e9bff',
    light2: '#a985ff',
    light3: '#34e0de',
    spark: '#8fb0ff',
    fog: '#050a18',
    ambient: 0.35,
    panelOpacity: 0.92,
  },
}

// Positions/rotations for the drifting "document" panels.
const PANELS = [
  { p: [-3.6, 1.3, -1], r: [0.3, 0.5, -0.15], s: 1.0, speed: 1.1 },
  { p: [3.5, 1.7, -2], r: [-0.2, -0.4, 0.2], s: 1.25, speed: 0.9 },
  { p: [-2.6, -1.8, 0.5], r: [0.15, 0.3, 0.1], s: 0.85, speed: 1.3 },
  { p: [3.0, -1.4, 0], r: [0.1, -0.5, -0.1], s: 0.95, speed: 1.0 },
  { p: [0.2, 2.4, -3], r: [-0.3, 0.2, 0.05], s: 1.4, speed: 0.8 },
  { p: [-0.5, -2.6, -1.5], r: [0.2, -0.2, 0.12], s: 1.1, speed: 1.15 },
  { p: [5.2, 0.2, -3.5], r: [0.1, -0.7, 0.1], s: 1.15, speed: 0.85 },
]

function DocPanel({ p, r, s, speed, theme }) {
  return (
    <Float speed={speed} rotationIntensity={0.6} floatIntensity={1.1} position={p}>
      <group rotation={r} scale={s}>
        {/* page */}
        <RoundedBox args={[1.5, 2, 0.06]} radius={0.07} smoothness={4}>
          <meshStandardMaterial
            color={theme.panel}
            emissive={theme.panelEmissive}
            emissiveIntensity={0.28}
            roughness={0.32}
            metalness={0.12}
            transparent
            opacity={theme.panelOpacity}
          />
        </RoundedBox>
        {/* accent spine along the top edge */}
        <mesh position={[0, 0.92, 0.035]}>
          <boxGeometry args={[1.5, 0.09, 0.02]} />
          <meshStandardMaterial color={theme.light2} emissive={theme.light2} emissiveIntensity={0.9} toneMapped={false} />
        </mesh>
      </group>
    </Float>
  )
}

function Scene({ theme }) {
  const group = useRef()
  useFrame((state, delta) => {
    if (!group.current) return
    // Slow drift + a whisper of parallax toward the pointer.
    group.current.rotation.y += delta * 0.04
    const px = state.pointer.x * 0.15
    const py = state.pointer.y * 0.1
    group.current.rotation.x += (py - group.current.rotation.x) * 0.03
    group.current.position.x += (px - group.current.position.x) * 0.03
  })
  return (
    <>
      <fog attach="fog" args={[theme.fog, 6, 16]} />
      <ambientLight intensity={theme.ambient} />
      <directionalLight position={[4, 6, 5]} intensity={0.7} />
      <pointLight position={[-6, 3, 2]} intensity={90} color={theme.light1} distance={30} decay={2} />
      <pointLight position={[6, -3, 1]} intensity={80} color={theme.light2} distance={30} decay={2} />
      <pointLight position={[0, 4, -4]} intensity={60} color={theme.light3} distance={30} decay={2} />
      <group ref={group}>
        {PANELS.map((cfg, i) => (
          <DocPanel key={i} {...cfg} theme={theme} />
        ))}
      </group>
      <Sparkles count={140} scale={[16, 9, 7]} size={2.2} speed={0.3} opacity={0.55} color={theme.spark} />
    </>
  )
}

export default function Background3D({ theme = 'dark' }) {
  const t = THEMES[theme] || THEMES.dark
  const reduced = useMemo(
    () => typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches,
    [],
  )
  // Pause rendering when the tab is hidden to save battery/GPU.
  const [visible, setVisible] = useState(true)
  useEffect(() => {
    const onVis = () => setVisible(!document.hidden)
    document.addEventListener('visibilitychange', onVis)
    return () => document.removeEventListener('visibilitychange', onVis)
  }, [])

  const frameloop = reduced || !visible ? 'never' : 'always'

  return (
    <div className="bg3d" aria-hidden="true">
      <Canvas
        camera={{ position: [0, 0, 7], fov: 50 }}
        dpr={[1, 1.75]}
        frameloop={frameloop}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      >
        <Scene theme={t} />
        <AdaptiveDpr pixelated />
      </Canvas>
    </div>
  )
}
