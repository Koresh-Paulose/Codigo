import React, { useState, useEffect } from 'react';
import { useTimer } from '../../shared/useTimer';
import { requestHint } from '../../api/client';

export const HintButton = ({ sessionId, conceptId, suggestHint }) => {
  const { timeLeft, isActive, start, reset } = useTimer(60);
  const [isCounting, setIsCounting] = useState(false);
  const [error, setError] = useState(null);
  const [hintAvailable, setHintAvailable] = useState(false);

  useEffect(() => {
    if (isCounting && !isActive && timeLeft === 0 && !hintAvailable) {
      setHintAvailable(true);
      setIsCounting(false);
    }
  }, [isCounting, isActive, timeLeft, hintAvailable]);

  const handleStuckClick = () => {
    if (!isCounting && !hintAvailable) {
      setIsCounting(true);
      start();
    }
  };

  const handleGetHint = async () => {
    try {
      setError(null);
      await requestHint(sessionId, conceptId);
      setHintAvailable(false);
      reset();
    } catch (err) {
      if (err.message === 'Too many requests') {
        setError('Please wait before requesting another hint.');
      } else {
        setError('Failed to get hint.');
      }
    }
  };

  return (
    <div className={`hint-button-container ${suggestHint ? 'highlight' : ''}`}>
      {suggestHint && <div className="suggestion-banner">💡 A hint might be useful right now!</div>}
      
      {!isCounting && !hintAvailable && (
        <button className="btn-stuck" onClick={handleStuckClick}>I'm stuck</button>
      )}
      
      {isCounting && timeLeft > 0 && (
        <button className="btn-counting" disabled>Think first: {timeLeft}s</button>
      )}
      
      {hintAvailable && (
        <button className="btn-get-hint" onClick={handleGetHint}>Get hint</button>
      )}
      
      {error && <div className="error-message">{error}</div>}
    </div>
  );
};

