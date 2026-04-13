import React from 'react';

function SlideCanvas({ slides, currentIndex, onSelectIndex }) {
  return (
    <div className="slide-canvas">
      {slides.length === 0 ? (
        <div className="empty-state">
          <p>No slides generated yet</p>
        </div>
      ) : (
        <div className="slide-container">
          <div className="slide-content">
            <h2>{slides[currentIndex]?.title || ''}</h2>
            <div className="slide-body">
              {slides[currentIndex]?.content || ''}
            </div>
          </div>
          <div className="slide-nav">
            <button
              onClick={() => onSelectIndex(Math.max(0, currentIndex - 1))}
              disabled={currentIndex === 0}
            >
              ←
            </button>
            <span>{currentIndex + 1} / {slides.length}</span>
            <button
              onClick={() => onSelectIndex(Math.min(slides.length - 1, currentIndex + 1))}
              disabled={currentIndex === slides.length - 1}
            >
              →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default SlideCanvas;
