import React, { useState } from 'react';
import Header from './Header';
import Chat from './Chat';
import InputForm from './InputForm';
import FeedbackModal from './FeedbackModal';
import './MagistusUI.css'; // Assuming external CSS for global styles

const MagistusUI = () => {
  // Global state for toggles
  const [reasoningEnabled, setReasoningEnabled] = useState(true);
  const [selfEvalEnabled, setSelfEvalEnabled] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);

  return (
    <div className="magistus-container">
      <Header
        reasoningEnabled={reasoningEnabled}
        setReasoningEnabled={setReasoningEnabled}
        selfEvalEnabled={selfEvalEnabled}
        setSelfEvalEnabled={setSelfEvalEnabled}
        ttsEnabled={ttsEnabled}
        setTtsEnabled={setTtsEnabled}
      />
      <main>
        <Chat />
        <InputForm />
      </main>
      <FeedbackModal />
    </div>
  );
};

export default MagistusUI;
