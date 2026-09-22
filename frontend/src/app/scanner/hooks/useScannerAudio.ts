'use client';

import { useState, useCallback, useEffect } from 'react';

const SOUNDS = {
  SCAN_COMPLETE: 'https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0c6ff1cbd.mp3?filename=ui-click-43196.mp3', // Industrial ping
  THREAT_DETECTED: 'https://cdn.pixabay.com/download/audio/2021/08/04/audio_bb643039d5.mp3?filename=error-126627.mp3', // Low alert
};

export function useScannerAudio() {
  const [isMuted, setIsMuted] = useState(false);

  const playSound = useCallback((type: keyof typeof SOUNDS) => {
    if (isMuted) return;

    try {
      const audio = new Audio(SOUNDS[type]);
      audio.volume = type === 'THREAT_DETECTED' ? 0.4 : 0.2;
      audio.play().catch(err => console.warn('Audio playback failed:', err));
    } catch (err) {
      console.error('Audio initialization failed:', err);
    }
  }, [isMuted]);

  const toggleMute = () => setIsMuted(prev => !prev);

  return { isMuted, toggleMute, playSound };
}
