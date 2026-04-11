#!/usr/bin/env python3
"""
LLM Wiki Agent - Demo Web Application

A Flask-based web application demonstrating the wiki system with:
- File upload and wiki ingestion
- Knowledge graph visualization
- Query and answer system
- Continuous wiki enrichment loop
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import sys

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.llm_config import LLMConfig

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
WIKI_DIR = PROJECT_ROOT / "wiki"
RAW_DIR = PROJECT_ROOT / "raw"
GRAPH_DIR = PROJECT_ROOT / "graph"
UPLOAD_DIR = PROJECT_ROOT / "uploads"

# Create necessary directories
UPLOAD_DIR.mkdir(exist_ok=True)


class WikiManager:
    """Manage wiki operations."""

    def __init__(self):
        self.wiki_dir = WIKI_DIR
        self.raw_dir = RAW_DIR
        self.graph_dir = GRAPH_DIR
        self.upload_dir = UPLOAD_DIR

    def get_index(self) -> Dict[str, Any]:
        """Read wiki index."""
        index_file = self.wiki_dir / "index.md"
        if not index_file.exists():
            return {"sources": [], "entities": [], "concepts": [], "syntheses": []}

        content = index_file.read_text(encoding='utf-8')
        # Simple parsing - in production, use proper markdown parser
        return self._parse_index(content)

    def _parse_index(self, content: str) -> Dict[str, Any]:
        """Parse index.md content."""
        sections = {"sources": [], "entities": [], "concepts": [], "syntheses": []}
        current_section = None

        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('## Sources'):
                current_section = "sources"
            elif line.startswith('## Entities'):
                current_section = "entities"
            elif line.startswith('## Concepts'):
                current_section = "concepts"
            elif line.startswith('## Syntheses'):
                current_section = "syntheses"
            elif line.startswith('- [') and current_section:
                # Parse markdown link: [Title](path) — description
                try:
                    title_part = line.split('[', 1)[1].split(']', 1)[0]
                    path_part = line.split('(', 1)[1].split(')', 1)[0]
                    desc = line.split('—', 1)[1].strip() if '—' in line else ""
                    sections[current_section].append({
                        "title": title_part,
                        "path": path_part,
                        "description": desc
                    })
                except:
                    pass

        return sections

    def read_page(self, page_path: str) -> Dict[str, Any]:
        """Read a wiki page."""
        full_path = self.wiki_dir / page_path
        if not full_path.exists():
            return {"error": "Page not found"}

        content = full_path.read_text(encoding='utf-8')

        # Parse frontmatter
        frontmatter = {}
        body_start = 0
        if content.startswith('---'):
            fm_end = content.find('---', 3)
            if fm_end > 0:
                fm_text = content[3:fm_end].strip()
                body_start = fm_end + 3
                for line in fm_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()

        return {
            "frontmatter": frontmatter,
            "content": content[body_start:].strip(),
            "full_path": str(full_path)
        }

    def save_page(self, page_path: str, content: str, frontmatter: Dict[str, Any]):
        """Save a wiki page."""
        full_path = self.wiki_dir / page_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Build frontmatter string
        fm_lines = ['---']
        for key, value in frontmatter.items():
            if isinstance(value, list):
                fm_lines.append(f'{key}: {json.dumps(value)}')
            else:
                fm_lines.append(f'{key}: {value}')
        fm_lines.append('---')

        full_content = '\n'.join(fm_lines) + '\n\n' + content
        full_path.write_text(full_content, encoding='utf-8')

        return {"success": True, "path": str(full_path)}

    def append_log(self, operation: str, title: str, details: str = ""):
        """Append entry to wiki log."""
        log_file = self.wiki_dir / "log.md"
        date_str = datetime.now().strftime("%Y-%m-%d")

        entry = f"""
## [{date_str}] {operation} | {title}

{details}

"""

        if log_file.exists():
            existing = log_file.read_text(encoding='utf-8')
            log_file.write_text(existing + entry, encoding='utf-8')
        else:
            log_file.write_text(f"# Wiki Log\n{entry}", encoding='utf-8')

    def get_graph_data(self) -> Dict[str, Any]:
        """Get knowledge graph data."""
        graph_file = self.graph_dir / "graph.json"
        if not graph_file.exists():
            return {"nodes": [], "edges": []}

        return json.loads(graph_file.read_text(encoding='utf-8'))

    def search_pages(self, query: str) -> List[Dict[str, Any]]:
        """Search wiki pages."""
        results = []
        query_lower = query.lower()

        # Search in all markdown files
        for md_file in self.wiki_dir.rglob("*.md"):
            if md_file.name == "index.md" or md_file.name == "log.md":
                continue

            try:
                content = md_file.read_text(encoding='utf-8')
                if query_lower in content.lower():
                    rel_path = md_file.relative_to(self.wiki_dir)
                    results.append({
                        "path": str(rel_path),
                        "preview": content[:200] + "..." if len(content) > 200 else content
                    })
            except:
                pass

        return results


# Initialize wiki manager
wiki_manager = WikiManager()


@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html')


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current LLM configuration status."""
    config = LLMConfig()
    return jsonify({
        "configured": config.is_configured(),
        "model": config.config.get("model", ""),
        "base_url": config.config.get("base_url", "")
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update LLM configuration."""
    data = request.json
    config = LLMConfig()

    try:
        config.update_config(
            base_url=data.get('base_url'),
            model=data.get('model'),
            api_key=data.get('api_key')
        )
        return jsonify({"success": True, "message": "Configuration updated"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/index', methods=['GET'])
def api_get_index():
    """Get wiki index."""
    return jsonify(wiki_manager.get_index())


@app.route('/api/page/<path:page_path>', methods=['GET'])
def api_get_page(page_path):
    """Get a wiki page."""
    return jsonify(wiki_manager.read_page(page_path))


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload a file for ingestion."""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400

    # Save uploaded file
    filename = file.filename
    upload_path = wiki_manager.upload_dir / filename
    file.save(str(upload_path))

    # Copy to raw directory
    raw_path = wiki_manager.raw_dir / filename
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(str(upload_path), str(raw_path))

    return jsonify({
        "success": True,
        "filename": filename,
        "path": str(raw_path.relative_to(PROJECT_ROOT))
    })


@app.route('/api/ingest', methods=['POST'])
def ingest_file():
    """Ingest a file into the wiki."""
    data = request.json
    filename = data.get('filename')

    if not filename:
        return jsonify({"success": False, "error": "No filename provided"}), 400

    # In a real implementation, this would:
    # 1. Read the file
    # 2. Use LLM to extract entities, concepts, relationships
    # 3. Create wiki pages
    # 4. Update index

    # For demo, create a simple source page
    raw_path = wiki_manager.raw_dir / filename
    if not raw_path.exists():
        return jsonify({"success": False, "error": "File not found"}), 404

    content = raw_path.read_text(encoding='utf-8')
    slug = Path(filename).stem

    # Create source page
    frontmatter = {
        "title": f"Source: {slug}",
        "type": "source",
        "tags": [],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source_file": f"raw/{filename}"
    }

    page_content = f"""## Summary

Source document ingested from {filename}.

## Content

{content[:500]}...

## Key Claims

- Document processed successfully
- Content extracted for wiki integration

## Connections

- This source can be linked to entities and concepts as they are discovered
"""

    wiki_manager.save_page(f"sources/{slug}.md", page_content, frontmatter)
    wiki_manager.append_log("ingest", slug, f"Ingested from {filename}")

    return jsonify({
        "success": True,
        "slug": slug,
        "message": "File ingested successfully"
    })


@app.route('/api/query', methods=['POST'])
def query_wiki():
    """Query the wiki and generate answer."""
    data = request.json
    question = data.get('question', '')

    if not question:
        return jsonify({"success": False, "error": "No question provided"}), 400

    # Search relevant pages
    search_results = wiki_manager.search_pages(question)

    # In a real implementation, this would:
    # 1. Use RAG with graph context
    # 2. Generate comprehensive answer
    # 3. Cite sources

    answer = f"""# Answer to: {question}

Based on the wiki knowledge base, here's what I found:

## Relevant Information

I searched through {len(search_results)} relevant pages in the wiki.

{"".join([f"- [[{r['path']}]]: {r['preview']}\n" for r in search_results[:5]])}

## Sources

{"".join([f"- [[{r['path']}]]\n" for r in search_results[:3]])}

---

*This answer was generated based on the current wiki content. Would you like me to save this as a synthesis page?*
"""

    return jsonify({
        "success": True,
        "answer": answer,
        "sources": [r['path'] for r in search_results[:5]]
    })


@app.route('/api/synthesis', methods=['POST'])
def save_synthesis():
    """Save a query answer as a synthesis page."""
    data = request.json
    question = data.get('question', '')
    answer = data.get('answer', '')

    if not question or not answer:
        return jsonify({"success": False, "error": "Missing question or answer"}), 400

    # Create slug from question
    slug = question.lower().replace(' ', '-')[:50]

    frontmatter = {
        "title": f"Q: {question}",
        "type": "synthesis",
        "tags": ["query"],
        "last_updated": datetime.now().strftime("%Y-%m-%d")
    }

    wiki_manager.save_page(f"syntheses/{slug}.md", answer, frontmatter)
    wiki_manager.append_log("query", question, f"Saved as syntheses/{slug}.md")

    return jsonify({
        "success": True,
        "slug": slug,
        "message": "Synthesis saved successfully"
    })


@app.route('/api/graph', methods=['GET'])
def api_get_graph():
    """Get knowledge graph data."""
    return jsonify(wiki_manager.get_graph_data())


@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    """Get wiki statistics."""
    index = wiki_manager.get_index()

    return jsonify({
        "total_sources": len(index['sources']),
        "total_entities": len(index['entities']),
        "total_concepts": len(index['concepts']),
        "total_syntheses": len(index['syntheses']),
        "total_pages": sum([
            len(index['sources']),
            len(index['entities']),
            len(index['concepts']),
            len(index['syntheses'])
        ])
    })


if __name__ == '__main__':
    print("🚀 Starting LLM Wiki Agent Demo Server...")
    print("📁 Wiki directory:", WIKI_DIR)
    print("📊 Graph directory:", GRAPH_DIR)
    print("📤 Upload directory:", UPLOAD_DIR)
    print("\n🌐 Server running at: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")

    app.run(debug=True, host='0.0.0.0', port=5000)
