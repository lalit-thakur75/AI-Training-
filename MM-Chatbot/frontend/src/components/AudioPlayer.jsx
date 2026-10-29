import React, { useRef, useState, useEffect } from 'react';

export default function AudioPlayer({ audioBase64, textContent }) {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    setIsPlaying(false);
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, [audioBase64, textContent]);

  if (!audioBase64 && !textContent) return null;

  const audioSrc = audioBase64 ? `data:audio/mp3;base64,${audioBase64}` : null;

  const togglePlay = () => {
    if (audioBase64 && audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        audioRef.current.play().then(() => setIsPlaying(true)).catch((e) => console.error(e));
      }
    } else if (textContent && window.speechSynthesis) {
      if (isPlaying) {
        window.speechSynthesis.cancel();
        setIsPlaying(false);
      } else {
        window.speechSynthesis.cancel();
        // Clean markdown symbols for cleaner speech
        const cleanSpeech = textContent.replace(/[*#`_\[\]()]/g, ' ').trim();
        const utterance = new SpeechSynthesisUtterance(cleanSpeech);
        utterance.rate = 1.0;
        utterance.onend = () => setIsPlaying(false);
        utterance.onerror = () => setIsPlaying(false);
        window.speechSynthesis.speak(utterance);
        setIsPlaying(true);
      }
    }
  };

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.5rem',
      marginTop: '0.6rem',
      background: '#f1f5f9',
      padding: '0.35rem 0.75rem',
      borderRadius: '20px',
      fontSize: '0.8rem',
      color: '#334155'
    }}>
      <audio
        ref={audioRef}
        src={audioSrc}
        onEnded={() => setIsPlaying(false)}
        style={{ display: 'none' }}
      />
      <button
        onClick={togglePlay}
        style={{
          border: 'none',
          background: '#2563eb',
          color: 'white',
          borderRadius: '50%',
          width: '24px',
          height: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          fontSize: '0.75rem'
        }}
        title={isPlaying ? "Pause audio" : "Play audio"}
      >
        {isPlaying ? "❚❚" : "▶"}
      </button>
      <span>{isPlaying ? "Playing voice response..." : "Listen to answer"}</span>
    </div>
  );
}
