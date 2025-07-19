import './MagistusUI.css'; // Assuming external CSS for global styles
import React, { useState } from 'react';
import Header from './components/Header';  // Adjust paths if needed
import Chat from './components/Chat';
import InputForm from './components/InputForm';
import FeedbackModal from './components/FeedbackModal';

const App = () => {
  // Global state for toggles
  const [reasoningEnabled, setReasoningEnabled] = useState(true);
  const [selfEvalEnabled, setSelfEvalEnabled] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);

  return (
    <div className="magistus-container">
      {/* Header Component */}
      <Header
        reasoningEnabled={reasoningEnabled}
        setReasoningEnabled={setReasoningEnabled}
        selfEvalEnabled={selfEvalEnabled}
        setSelfEvalEnabled={setSelfEvalEnabled}
        ttsEnabled={ttsEnabled}
        setTtsEnabled={setTtsEnabled}
      />
      <main>
        {/* Chat Component */}
        <Chat />

        {/* Input Form Component */}
        <InputForm />
      </main>

      {/* Feedback Modal Component */}
      <FeedbackModal />
    </div>
  );
};

export default App;
