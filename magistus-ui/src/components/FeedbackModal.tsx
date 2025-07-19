import React, { useState } from 'react';

const FeedbackModal = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [feedback, setFeedback] = useState('');

  const handleSubmit = () => {
    // Submit feedback logic (e.g., send to backend)
    console.log('Feedback submitted:', feedback);
    setFeedback('');
    setIsVisible(false);
  };

  return (
    isVisible && (
      <div className="modal">
        <div className="modal-content">
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Your feedback..."
          />
          <button onClick={handleSubmit}>Submit</button>
          <button onClick={() => setIsVisible(false)}>Close</button>
        </div>
      </div>
    )
  );
};

export default FeedbackModal;
