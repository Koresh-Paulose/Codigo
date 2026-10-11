import React from 'react';

export const HintLevelBadge = ({ level }) => {
  const dots = [1, 2, 3, 4];
  
  return (
    <div className="hint-level-badge" style={{ display: 'flex', gap: '4px' }}>
      {dots.map((dot) => (
        <span
          key={dot}
          className={`dot ${dot <= level ? 'filled' : 'empty'}`}
          style={{
            display: 'inline-block',
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            backgroundColor: dot <= level ? '#007bff' : '#e0e0e0',
          }}
          title={`Hint Level ${dot}`}
        />
      ))}
    </div>
  );
};

