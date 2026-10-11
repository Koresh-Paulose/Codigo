import React from 'react';
import { HintLevelBadge } from './HintLevelBadge';

export const ChatView = ({ messages }) => {
  return (
    <div className="chat-view" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {messages.map((msg, index) => {
        if (msg.type === 'hint') {
          return (
            <div 
              key={index} 
              className="hint-message card lightbulb-card" 
              style={{ 
                backgroundColor: '#fff3cd', 
                padding: '12px', 
                borderRadius: '8px',
                border: '1px solid #ffeeba'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <strong>💡 Hint (Level {msg.level})</strong>
                <HintLevelBadge level={msg.level} />
              </div>
              <div className="hint-text">{msg.text}</div>
              {msg.level >= 4 && (
                <div 
                  className="tag revealed-tag" 
                  style={{ 
                    color: '#842029', 
                    backgroundColor: '#f8d7da',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '0.85em',
                    marginTop: '10px',
                    display: 'inline-block'
                  }}
                >
                  Revealed: not independently learned
                </div>
              )}
            </div>
          );
        }
        
        // Render regular messages
        return (
          <div 
            key={index} 
            className={`message ${msg.sender}`}
            style={{
              alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              backgroundColor: msg.sender === 'user' ? '#007bff' : '#f1f1f1',
              color: msg.sender === 'user' ? '#fff' : '#333',
              padding: '10px',
              borderRadius: '8px',
              maxWidth: '80%'
            }}
          >
            {msg.text}
          </div>
        );
      })}
    </div>
  );
};

