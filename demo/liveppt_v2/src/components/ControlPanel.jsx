import React from 'react';

function ControlPanel({ status, onPause, onResume, slideCount, currentIndex }) {
  return (
    <div className="control-panel">
      <div className="status-info">
        <span className={`status-badge ${status}`}>
          {status === 'idle' && 'Ready'}
          {status === 'generating' && 'Generating...'}
          {status === 'paused' && 'Paused'}
        </span>
        <span className="slide-count">
          Slide {currentIndex + 1} / {slideCount}
        </span>
      </div>
      <div className="control-buttons">
        {status === 'generating' && (
          <button onClick={onPause} className="btn-pause">Pause</button>
        )}
        {status === 'paused' && (
          <button onClick={onResume} className="btn-resume">Resume</button>
        )}
      </div>
    </div>
  );
}

export default ControlPanel;
