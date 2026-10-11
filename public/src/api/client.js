export const requestHint = async (sessionId, conceptId) => {
  const response = await fetch('/api/hint', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ sessionId, conceptId }),
  });
  
  if (response.status === 429) {
    throw new Error('Too many requests');
  }
  
  if (!response.ok) {
    throw new Error('Failed to request hint');
  }
  
  return response.json();
};

