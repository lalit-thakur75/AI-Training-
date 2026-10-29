import React from 'react';

export default function CrisisAlert({ onClose }) {
  return (
    <div className="crisis-banner">
      <div>
        <strong>🚨 Immediate Support & Safety Helpline:</strong>
        <div style={{ marginTop: '0.2rem', fontSize: '0.8rem' }}>
          If you or someone you know is in distress or immediate danger, please reach out now:
          <strong> India National Emergency: 112</strong> | 
          <strong> Vandrevala Foundation: 9999 666 555</strong> | 
          <strong> Tele-MANAS: 14416</strong>
        </div>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: 'inherit',
            fontWeight: 'bold',
            cursor: 'pointer',
            marginLeft: '1rem',
            fontSize: '1rem'
          }}
        >
          ✕
        </button>
      )}
    </div>
  );
}
