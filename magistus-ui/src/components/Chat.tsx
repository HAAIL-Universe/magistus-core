import { useState, useEffect, useRef } from "react";

// Define the Message type
type Message = {
  id: string;         // Unique ID for each message
  text: string;
  sender: 'User' | 'Magistus';
  timestamp: string;  // Timestamps for each message
};

const Chat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Function to append messages to the chat
  const appendMessage = (text: string, sender: 'User' | 'Magistus') => {
    const timestamp = new Date().toLocaleTimeString(); // Add timestamp to the message
    setMessages([...messages, { text, sender, timestamp, id: `${sender}-${Date.now()}` }]);
  };

  // Scroll to the bottom of the chat container when a new message is added
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // MessageBubble Logic (directly inside Chat.tsx)
  const MessageBubble = ({ message, isUser, timestamp }: { message: string, isUser: boolean, timestamp?: string }) => {
    return (
      <div className={`flex gap-3 max-w-4xl mx-auto group transition-all duration-300 ${isUser ? "justify-end" : "justify-start"}`}>
        {/* Icon for Bot (Magistus) */}
        {!isUser && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center">
            <span className="w-4 h-4 text-primary">🤖</span> {/* Change to bot icon as needed */}
          </div>
        )}
        
        {/* Message Bubble Styling */}
        <div className={`max-w-[70%] rounded-lg px-4 py-3 shadow-card border transition-all duration-300 
          ${isUser ? "bg-user-message/10 border-user-message/30 text-foreground" 
          : "bg-assistant-message/90 border-primary/20 text-card-foreground"}`}>
          <p className="text-base leading-relaxed whitespace-pre-wrap">
            {message}
          </p>
          {/* Timestamp */}
          {timestamp && (
            <span className="text-xs text-muted-foreground mt-2 block">
              {timestamp}
            </span>
          )}
        </div>

        {/* Icon for User */}
        {isUser && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-user-message/20 border border-user-message/30 flex items-center justify-center">
            <span className="w-4 h-4 text-user-message">👤</span> {/* Replace with user icon */}
          </div>
        )}
      </div>
    );
  };


  return (
    <div className="chat-container" ref={chatContainerRef}>
      {messages.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-primary/10 border-2 border-primary/20 flex items-center justify-center">
            <span className="text-2xl">🤖</span>
          </div>
          <h3 className="text-xl font-semibold text-foreground mb-2">Welcome to Magistus AGI</h3>
          <p className="text-muted-foreground max-w-md mx-auto">
            Start a conversation with our advanced AI system. Ask questions, get insights, or have a natural conversation.
          </p>
        </div>
      ) : (
        messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg.text}
            isUser={msg.sender === 'User'}
            timestamp={msg.timestamp}
          />
        ))
      )}
    </div>
  );
};

export default Chat;
