import React, { useState, useEffect } from 'react';
import WikiSelector from './components/WikiSelector';
import SlideCanvas from './components/SlideCanvas';
import ControlPanel from './components/ControlPanel';
import ChatPanel from './components/ChatPanel';
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

  // 处理 SSE 事件
  const handleSSEEvent = (event) => {
    console.log('SSE Event:', event);

    switch (event.type) {
      case 'outline':
        console.log('Outline received:', event.slides);
        break;
      case 'job_id':
        setJobId(event.job_id);
        break;
      case 'slide':
        setSlides(prev => [...prev, event.slide]);
        break;
      case 'done':
        setGenerationStatus('idle');
        break;
      case 'error':
        console.error('Generation error:', event.message);
        setGenerationStatus('idle');
        break;
    }
  };

  const handleGenerate = async (instruction) => {
    setSlides([]);
    setCurrentSlideIndex(0);
    setGenerationStatus('generating');

    try {
      // Step 1: POST to start generation
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wiki_ids: selectedWikiIds,
          instruction: instruction,
          template_path: null
        })
      });

      if (!response.ok) {
        throw new Error('Failed to start generation');
      }

      // Step 2: Read SSE stream from response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              handleSSEEvent(data);
            } catch (err) {
              console.error('Failed to parse SSE event:', err);
            }
          }
        }
      }
    } catch (error) {
      console.error('Generation error:', error);
      setGenerationStatus('idle');
    }
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
