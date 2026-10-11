import { useState, useEffect } from 'react';

export const useTimer = (initialSeconds = 60) => {
  const [timeLeft, setTimeLeft] = useState(initialSeconds);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    let interval = null;
    if (isActive && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
    } else if (timeLeft === 0) {
      clearInterval(interval);
      setIsActive(false);
    }
    return () => clearInterval(interval);
  }, [isActive, timeLeft]);

  const start = () => setIsActive(true);
  const reset = (seconds = initialSeconds) => {
    setTimeLeft(seconds);
    setIsActive(false);
  };

  return { timeLeft, isActive, start, reset };
};

