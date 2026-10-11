import React from 'react';

export const ConceptChecklist = ({ concepts }) => {
  const getColor = (level) => {
    if (level === 0) return '#28a745'; // green
    if (level <= 2) return '#ffc107'; // yellow
    return '#dc3545'; // red
  };

  return (
    <div className="concept-checklist card" style={{ padding: '15px', border: '1px solid #ddd', borderRadius: '8px' }}>
      <h3 style={{ marginTop: 0 }}>Concepts</h3>
      <ul style={{ listStyleType: 'none', padding: 0, margin: 0 }}>
        {concepts.map((concept) => (
          <li 
            key={concept.id} 
            style={{ 
              display: 'flex',
              alignItems: 'center',
              padding: '8px 0',
              borderBottom: '1px solid #eee'
            }}
          >
            <span 
              className="status-indicator"
              style={{
                display: 'inline-block',
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: getColor(concept.hintLevel),
                marginRight: '10px'
              }}
            />
            <span style={{ flex: 1 }}>{concept.name}</span>
            <span style={{ fontSize: '0.85em', color: '#666' }}>
              Level: {concept.hintLevel}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};

