import React, { useState } from 'react';

// Define the Message type
type Message = {
  text: string;
  sender: 'User' | 'Magistus'; // Assuming these are the two senders
};

const Chat = () => {
  const [messages, setMessages] = useState<Message[]>([]);

  const appendMessage = (text: string, sender: 'User' | 'Magistus') => {
    setMessages([...messages, { text, sender }]);
  };

  return (
    <div className="chat-container">
      {messages.map((msg, index) => (
        <div key={index} className={`message ${msg.sender === 'User' ? 'user' : 'magistus'}`}>
          <p>{msg.sender === 'User' ? 'You: ' : 'Magistus: '}{msg.text}</p>
        </div>
      ))}
    </div>
  );
};

export default Chat;
