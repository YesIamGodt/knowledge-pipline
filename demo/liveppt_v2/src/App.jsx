import React, { useState, useEffect } from 'react';
import WikiSelector from './components/WikiSelector';
import SlideCanvas from './components/SlideCanvas';
import ControlPanel from './components/ControlPanel';
import ChatPanel from './components/ChatPanel';
import { useSSE } from './hooks/useSSE';
import './App.css';

function App() {
  const [wikiPages, setWikiPages] = useState({});
  const [selectedWikiIds, setSelectedWikiIds] = useState([]);
  const [slides, setSlides] = useState([]);
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [isWikiPanelCollapsed, setIsWikiPanelCollapsed] = useState(false);
  const [generationStatus, setGenerationStatus] = useState('idle'); // idle, generating, paused
  const [jobId, setJobId] = useState(null);

  // 加载 Wiki 列表
  useEffect(() => {
    fetch('/api/wiki/list')
      .then(res => res.json())
      .then(data => setWikiPages(data))
      .catch(err => console.error('Failed to load wiki:', err));
  }, []);

  // SSE 连接
  const { events, isConnected, error } = useSSE(
    generationStatus === 'generating' ? `/api/generate` : null,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        wiki_ids: selectedWikiIds,
        instruction: 'Generate PPT',
        template_path: null
      })
    }
  );

  // 处理 SSE 事件
  useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[events.length - 1];
      console.log('SSE Event:', latestEvent);

      switch (latestEvent.type) {
        case 'outline':
          console.log('Outline received:', latestEvent.slides);
          break;
        case 'slide':
          setSlides(prev => [...prev, latestEvent.slide]);
          break;
        case 'done':
          setGenerationStatus('idle');
          break;
        case 'error':
          console.error('Generation error:', latestEvent.message);
          setGenerationStatus('idle');
          break;
      }
    }
  }, [events]);

  const handleGenerate = (instruction) => {
    setSlides([]);
    setCurrentSlideIndex(0);
    setGenerationStatus('generating');
  };

  const handlePause = async () => {
    if (!jobId) return;
    await fetch('/api/pause', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: jobId })
    });
    setGenerationStatus('paused');
  };

  const handleResume = async () => {
    if (!jobId) return;
    await fetch('/api/resume', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: jobId, user_edits: {} })
    });
    setGenerationStatus('generating');
  };

  return (
    <div className="app">
      <div className={`panel-left ${isWikiPanelCollapsed ? 'collapsed' : ''}`}>
        <WikiSelector
          wikiPages={wikiPages}
          selectedIds={selectedWikiIds}
          onSelect={setSelectedWikiIds}
          onToggleCollapse={() => setIsWikiPanelCollapsed(!isWikiPanelCollapsed)}
          isCollapsed={isWikiPanelCollapsed}
        />
      </div>

      <div className="panel-right">
        <SlideCanvas
          slides={slides}
          currentIndex={currentSlideIndex}
          onSelectIndex={setCurrentSlideIndex}
        />

        <ChatPanel
          onSend={handleGenerate}
          disabled={generationStatus === 'generating'}
        />

        <ControlPanel
          status={generationStatus}
          onPause={handlePause}
          onResume={handleResume}
          slideCount={slides.length}
          currentIndex={currentSlideIndex}
        />
      </div>
    </div>
  );
}

export default App;
