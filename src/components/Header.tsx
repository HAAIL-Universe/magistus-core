import React from 'react';

const Header = ({
  reasoningEnabled,
  setReasoningEnabled,
  selfEvalEnabled,
  setSelfEvalEnabled,
  ttsEnabled,
  setTtsEnabled
}) => {
  return (
    <header>
      <div className="branding">🌐 Magistus AGI</div>
      <div className="control-group">
        <button 
          className="toggle-btn" 
          onClick={() => setReasoningEnabled(!reasoningEnabled)}
          aria-checked={reasoningEnabled}
        >
          🧠 Reasoning: {reasoningEnabled ? 'ON' : 'OFF'}
        </button>
        <button 
          className="toggle-btn" 
          onClick={() => setSelfEvalEnabled(!selfEvalEnabled)}
          aria-checked={selfEvalEnabled}
        >
          📝 Self‑Eval: {selfEvalEnabled ? 'ON' : 'OFF'}
        </button>
        <button 
          className="toggle-btn" 
          onClick={() => setTtsEnabled(!ttsEnabled)}
          aria-checked={ttsEnabled}
        >
          🔈 TTS: {ttsEnabled ? 'ON' : 'OFF'}
        </button>
      </div>
    </header>
  );
};

export default Header;
