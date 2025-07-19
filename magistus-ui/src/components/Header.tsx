import React from 'react';

// Define types for the props
interface HeaderProps {
  reasoningEnabled: boolean;
  setReasoningEnabled: React.Dispatch<React.SetStateAction<boolean>>;
  selfEvalEnabled: boolean;
  setSelfEvalEnabled: React.Dispatch<React.SetStateAction<boolean>>;
  ttsEnabled: boolean;
  setTtsEnabled: React.Dispatch<React.SetStateAction<boolean>>;
}

const Header: React.FC<HeaderProps> = ({
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
