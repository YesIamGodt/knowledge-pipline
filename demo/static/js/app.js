// LLM Wiki Agent - Frontend Application

// API Base URL
const API_BASE = window.location.origin;

// State
let currentConfig = null;
let currentAnswer = null;
let currentQuestion = null;

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initConfig();
    initUpload();
    initExplore();
    initQuery();
    initGraph();
    loadStats();
});

// Smooth scroll navigation
function initNavigation() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Configuration Management
async function initConfig() {
    await checkConfig();

    document.getElementById('configForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveConfig();
    });

    document.getElementById('reconfigureBtn').addEventListener('click', () => {
        showConfigForm();
    });
}

async function checkConfig() {
    const statusDiv = document.getElementById('configStatus');
    const statusText = statusDiv.querySelector('.status-text');
    const indicator = statusDiv.querySelector('.status-indicator');

    try {
        const response = await fetch(`${API_BASE}/api/config`);
        const data = await response.json();

        if (data.configured) {
            currentConfig = data;
            indicator.className = 'status-indicator status-configured';
            statusText.textContent = '✅ Configured';
            document.getElementById('configuredModel').textContent = data.model;
            document.getElementById('configuredInfo').style.display = 'block';
            document.getElementById('configForm').style.display = 'none';
        } else {
            indicator.className = 'status-indicator status-error';
            statusText.textContent = '⚠️ Not configured';
            showConfigForm();
        }
    } catch (error) {
        indicator.className = 'status-indicator status-error';
        statusText.textContent = '❌ Error checking configuration';
        console.error('Config check error:', error);
    }
}

function showConfigForm() {
    document.getElementById('configForm').style.display = 'flex';
    document.getElementById('configuredInfo').style.display = 'none';
}

async function saveConfig() {
    const baseUrl = document.getElementById('baseUrl').value;
    const model = document.getElementById('model').value;
    const apiKey = document.getElementById('apiKey').value;

    try {
        const response = await fetch(`${API_BASE}/api/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ baseUrl, model, apiKey })
        });

        const data = await response.json();

        if (data.success) {
            await checkConfig();
            showNotification('Configuration saved successfully!', 'success');
        } else {
            showNotification(data.error || 'Failed to save configuration', 'error');
        }
    } catch (error) {
        showNotification('Error saving configuration', 'error');
        console.error('Config save error:', error);
    }
}

// File Upload
function initUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.querySelector('.upload-btn');

    // Click to upload
    uploadBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        handleFiles(files);
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

async function handleFiles(files) {
    const progressDiv = document.getElementById('uploadProgress');
    const resultsDiv = document.getElementById('uploadResults');
    const resultsList = document.getElementById('uploadResultsList');

    progressDiv.style.display = 'block';
    resultsDiv.style.display = 'block';
    resultsList.innerHTML = '';

    for (const file of files) {
        await uploadAndIngest(file);
    }

    setTimeout(() => {
        progressDiv.style.display = 'none';
    }, 1000);
}

async function uploadAndIngest(file) {
    const progressFilename = document.getElementById('progressFilename');
    const progressStatus = document.getElementById('progressStatus');
    const progressBar = document.getElementById('progressBar');
    const resultsList = document.getElementById('uploadResultsList');

    progressFilename.textContent = file.name;
    progressStatus.textContent = 'Uploading...';
    progressBar.style.width = '0%';

    try {
        // Upload file
        const formData = new FormData();
        formData.append('file', file);

        progressStatus.textContent = 'Uploading...';
        progressBar.style.width = '30%';

        const uploadResponse = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: formData
        });

        const uploadData = await uploadResponse.json();

        if (!uploadData.success) {
            throw new Error(uploadData.error || 'Upload failed');
        }

        progressBar.style.width = '60%';
        progressStatus.textContent = 'Ingesting...';

        // Ingest file
        const ingestResponse = await fetch(`${API_BASE}/api/ingest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filename: file.name })
        });

        const ingestData = await ingestResponse.json();

        progressBar.style.width = '100%';
        progressStatus.textContent = 'Complete!';

        // Add result item
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item ' + (ingestData.success ? 'success' : 'error');
        resultItem.innerHTML = `
            <div>
                <div class="item-title">${file.name}</div>
                <div class="item-description">${ingestData.message || ingestData.error}</div>
            </div>
            ${ingestData.success ? '<span>✅</span>' : '<span>❌</span>'}
        `;
        resultsList.appendChild(resultItem);

        if (ingestData.success) {
            loadStats();
            loadIndex();
        }

    } catch (error) {
        console.error('Upload error:', error);
        progressStatus.textContent = 'Failed';

        const resultItem = document.createElement('div');
        resultItem.className = 'result-item error';
        resultItem.innerHTML = `
            <div>
                <div class="item-title">${file.name}</div>
                <div class="item-description">${error.message}</div>
            </div>
            <span>❌</span>
        `;
        resultsList.appendChild(resultItem);
    }
}

// Explore Wiki
function initExplore() {
    loadIndex();

    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active tab
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Show corresponding content
            const tabName = btn.dataset.tab;
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabName}Tab`).classList.add('active');
        });
    });

    // Modal close
    document.getElementById('modalClose').addEventListener('click', () => {
        document.getElementById('pageModal').style.display = 'none';
    });

    // Close modal on outside click
    document.getElementById('pageModal').addEventListener('click', (e) => {
        if (e.target.id === 'pageModal') {
            document.getElementById('pageModal').style.display = 'none';
        }
    });
}

async function loadIndex() {
    try {
        const response = await fetch(`${API_BASE}/api/index`);
        const index = await response.json();

        renderItems('sourcesList', index.sources, 'sources');
        renderItems('entitiesList', index.entities, 'entities');
        renderItems('conceptsList', index.concepts, 'concepts');
        renderItems('synthesesList', index.syntheses, 'syntheses');
    } catch (error) {
        console.error('Error loading index:', error);
    }
}

function renderItems(containerId, items, category) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    if (!items || items.length === 0) {
        container.innerHTML = '<p class="item-description">No items yet.</p>';
        return;
    }

    items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.innerHTML = `
            <div class="item-title">${item.title}</div>
            <div class="item-description">${item.description || 'No description'}</div>
        `;
        card.addEventListener('click', () => loadPage(item.path));
        container.appendChild(card);
    });
}

async function loadPage(pagePath) {
    try {
        const response = await fetch(`${API_BASE}/api/page/${pagePath}`);
        const data = await response.json();

        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }

        // Show modal
        const modal = document.getElementById('pageModal');
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');

        modalTitle.textContent = data.frontmatter.title || pagePath;

        // Parse markdown content (simple parsing for demo)
        let html = markdownToHtml(data.content);
        modalBody.innerHTML = html;

        modal.style.display = 'flex';
    } catch (error) {
        console.error('Error loading page:', error);
        showNotification('Error loading page', 'error');
    }
}

function markdownToHtml(markdown) {
    // Simple markdown parser for demo
    let html = markdown
        // Headers
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        // Bold
        .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.*)\*/gim, '<em>$1</em>')
        // Links
        .replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2" target="_blank">$1</a>')
        // Wiki links
        .replace(/\[\[([^\]]+)\]\]/gim, '<span class="wiki-link">$1</span>')
        // Lists
        .replace(/^\- (.*$)/gim, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>')
        // Line breaks
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');

    return '<p>' + html + '</p>';
}

// Query System
function initQuery() {
    const queryForm = document.getElementById('queryForm');

    queryForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = document.getElementById('queryInput').value.trim();
        if (!question) return;

        await queryWiki(question);
    });

    document.getElementById('saveSynthesisBtn').addEventListener('click', () => {
        if (currentAnswer && currentQuestion) {
            saveSynthesis(currentQuestion, currentAnswer);
        }
    });
}

async function queryWiki(question) {
    const resultsDiv = document.getElementById('queryResults');
    const answerContent = document.getElementById('answerContent');
    const sourcesList = document.getElementById('sourcesList');
    const queryInput = document.getElementById('queryInput');

    queryInput.disabled = true;
    resultsDiv.style.display = 'block';
    answerContent.innerHTML = '<div class="loading-spinner"></div> Generating answer...';
    sourcesList.innerHTML = '';

    try {
        const response = await fetch(`${API_BASE}/api/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        if (data.success) {
            currentQuestion = question;
            currentAnswer = data.answer;

            answerContent.innerHTML = markdownToHtml(data.answer);

            // Render sources
            if (data.sources && data.sources.length > 0) {
                sourcesList.innerHTML = data.sources.map(source =>
                    `<span class="source-tag">${source}</span>`
                ).join('');
            }

            showNotification('Answer generated successfully!', 'success');
        } else {
            answerContent.innerHTML = `<p style="color: #ff3b30;">${data.error || 'Failed to generate answer'}</p>`;
        }
    } catch (error) {
        console.error('Query error:', error);
        answerContent.innerHTML = '<p style="color: #ff3b30;">Error generating answer</p>';
        showNotification('Error querying wiki', 'error');
    } finally {
        queryInput.disabled = false;
    }
}

async function saveSynthesis(question, answer) {
    try {
        const response = await fetch(`${API_BASE}/api/synthesis`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question, answer })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Synthesis saved to wiki!', 'success');
            loadStats();
            loadIndex();
        } else {
            showNotification(data.error || 'Failed to save synthesis', 'error');
        }
    } catch (error) {
        console.error('Save synthesis error:', error);
        showNotification('Error saving synthesis', 'error');
    }
}

// Knowledge Graph
function initGraph() {
    loadGraph();

    document.getElementById('refreshGraph').addEventListener('click', loadGraph);
    document.getElementById('resetZoom').addEventListener('click', () => {
        // Reset zoom (to be implemented with proper graph library)
        loadGraph();
    });
}

async function loadGraph() {
    const canvas = document.getElementById('graphCanvas');

    try {
        const response = await fetch(`${API_BASE}/api/graph`);
        const data = await response.json();

        if (data.nodes && data.nodes.length > 0) {
            renderGraph(data);
        } else {
            canvas.innerHTML = '<p style="text-align: center; padding: 40px; color: rgba(255, 255, 255, 0.5);">No graph data yet. Upload documents to generate the knowledge graph.</p>';
        }
    } catch (error) {
        console.error('Graph loading error:', error);
        canvas.innerHTML = '<p style="text-align: center; padding: 40px; color: #ff3b30;">Error loading graph</p>';
    }
}

function renderGraph(data) {
    const canvas = document.getElementById('graphCanvas');

    // Simple canvas-based graph rendering for demo
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    const nodes = data.nodes || [];
    const edges = data.edges || [];

    // Position nodes randomly for demo
    nodes.forEach(node => {
        node.x = Math.random() * (canvas.width - 100) + 50;
        node.y = Math.random() * (canvas.height - 100) + 50;
    });

    // Clear canvas
    ctx.fillStyle = '#272729';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw edges
    edges.forEach(edge => {
        const source = nodes.find(n => n.id === edge.source);
        const target = nodes.find(n => n.id === edge.target);

        if (source && target) {
            ctx.beginPath();
            ctx.moveTo(source.x, source.y);
            ctx.lineTo(target.x, target.y);
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
            ctx.lineWidth = 1;
            ctx.stroke();
        }
    });

    // Draw nodes
    nodes.forEach(node => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI);

        // Color by type
        switch(node.type) {
            case 'source':
                ctx.fillStyle = '#34c759';
                break;
            case 'entity':
                ctx.fillStyle = '#0071e3';
                break;
            case 'concept':
                ctx.fillStyle = '#ff9500';
                break;
            case 'synthesis':
                ctx.fillStyle = '#af52de';
                break;
            default:
                ctx.fillStyle = '#888';
        }

        ctx.fill();

        // Draw label
        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.font = '12px -apple-system, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(node.label || node.id, node.x, node.y + 20);
    });

    // Add interaction hint
    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.font = '14px -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`Graph: ${nodes.length} nodes, ${edges.length} edges`, canvas.width / 2, canvas.height - 20);
}

// Statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        const stats = await response.json();

        document.getElementById('totalPages').textContent = stats.total_pages || 0;
        document.getElementById('totalSources').textContent = stats.total_sources || 0;
        document.getElementById('totalEntities').textContent = stats.total_entities || 0;
        document.getElementById('totalConcepts').textContent = stats.total_concepts || 0;
    } catch (error) {
        console.error('Stats loading error:', error);
    }
}

// Notification System
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }

    // Create notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    // Style
    Object.assign(notification.style, {
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        padding: '16px 24px',
        borderRadius: '8px',
        backgroundColor: type === 'success' ? '#34c759' : type === 'error' ? '#ff3b30' : '#0071e3',
        color: 'white',
        fontFamily: '-apple-system, sans-serif',
        fontSize: '14px',
        fontWeight: '400',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        zIndex: '9999',
        animation: 'slideIn 0.3s ease'
    });

    document.body.appendChild(notification);

    // Auto remove
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .wiki-link {
        color: #0071e3;
        font-weight: 500;
    }
`;
document.head.appendChild(style);
