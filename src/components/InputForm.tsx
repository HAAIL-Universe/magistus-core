import React, { useState } from 'react';

const InputForm = () => {
  const [inputText, setInputText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputText.trim()) {
      // Handle form submission logic (e.g., sending the message to the backend)
      console.log('Message sent:', inputText);
    }
    setInputText('');
  };

  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        placeholder="Type your message..."
      />
      <button type="submit">Send</button>
    </form>
  );
};

export default InputForm;
