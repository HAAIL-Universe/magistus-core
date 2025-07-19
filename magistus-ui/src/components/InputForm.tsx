import React, { useState, useRef, useEffect } from 'react';

const InputForm = () => {
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState<{ text: string, sender: string }[]>([]);
  const [isRecording, setIsRecording] = useState(false); // For the microphone button
  const textareaRef = useRef<HTMLTextAreaElement | null>(null); // Explicitly define the type

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputText.trim()) {
      setMessages([...messages, { text: inputText, sender: 'User' }]); // Add user message
      setInputText('');
    }
  };

  // Auto-expand textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';  // Reset height
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;  // Set new height
    }
  }, [inputText]);

  // Handle microphone button click
  const handleMicClick = () => {
    setIsRecording(!isRecording);
    // Placeholder logic for handling audio recording
    if (!isRecording) {
      console.log('Recording started');
    } else {
      console.log('Recording stopped');
    }
  };

  // Enter key logic for sending the message, and Shift + Enter for a line break
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();  // Prevent the default behavior (line break)
      handleSubmit(e);  // Pass the event to handleSubmit
    }
  };

  return (
    <form onSubmit={handleSubmit} className="chat-form">
      <div className="message-container">
        {/* Chat output area */}
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender === 'User' ? 'user' : 'magistus'}`}>
            <p>{msg.sender}: {msg.text}</p>
          </div>
        ))}
      </div>

      <div className="button-container">
        {/* Microphone button */}
        <button
          type="button"
          className={`mic-button ${isRecording ? 'mic-recording' : ''}`}
          onClick={handleMicClick}
        >
          {isRecording ? (
            <span className="w-4 h-4">🔴</span> // Using a red circle for recording indicator
          ) : (
            <span className="w-4 h-4">🎤</span> // Microphone icon
          )}
        </button>

        {/* Textarea */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown} // Handle Enter key logic
            style={{ resize: 'none', width: '100%', maxWidth: '600px' }}  // Set width and max-width limits
            rows={1}  // Start with 1 row
            placeholder="Type your message..."
            className="bg-input border-primary/30 focus:border-primary focus:ring-primary/20 placeholder:text-muted-foreground 
              px-4 py-3 rounded-lg transition-all duration-300 focus:shadow-md focus:ring-2 focus:ring-primary/50"
          />
        </div>

        {/* Send Button */}
        <button
          type="submit"
          disabled={!inputText.trim()}
          className="bg-primary hover:bg-primary/90 text-white p-2 rounded"
        >
          <span className="w-4 h-4">➤</span> {/* Send icon */}
        </button>
      </div>
    </form>
  );
};

export default InputForm;
