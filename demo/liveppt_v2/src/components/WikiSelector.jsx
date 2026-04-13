import React from 'react';

function WikiSelector({ wikiPages, selectedIds, onSelect, onToggleCollapse, isCollapsed }) {
  if (isCollapsed) {
    return (
      <div className="wiki-selector collapsed" onClick={onToggleCollapse}>
        <button className="toggle-btn">»</button>
      </div>
    );
  }

  return (
    <div className="wiki-selector">
      <div className="wiki-selector-header">
        <h3>Knowledge Base</h3>
        <button className="toggle-btn" onClick={onToggleCollapse}>«</button>
      </div>
      <div className="wiki-list">
        {Object.entries(wikiPages).map(([id, page]) => (
          <label key={id} className="wiki-item">
            <input
              type="checkbox"
              checked={selectedIds.includes(id)}
              onChange={(e) => {
                if (e.target.checked) {
                  onSelect([...selectedIds, id]);
                } else {
                  onSelect(selectedIds.filter(i => i !== id));
                }
              }}
            />
            <span>{page.title || id}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

export default WikiSelector;
