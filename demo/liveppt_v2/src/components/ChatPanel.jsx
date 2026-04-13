import React, { useState } from 'react';

function ChatPanel({ onSend, disabled }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input);
      setInput('');
    }
  };

  return (
    <div className="chat-panel">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter instruction to generate PPT..."
          disabled={disabled}
        />
        <button type="submit" disabled={disabled || !input.trim()}>
          {disabled ? 'Generating...' : 'Generate'}
        </button>
      </form>
    </div>
  );
}

export default ChatPanel;
