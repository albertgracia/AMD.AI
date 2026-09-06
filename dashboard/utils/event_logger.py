import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

_log_lock = threading.Lock()
BASE_DIR = Path(r'G:\Proyectos\AMD.AI\dashboard')
EVENT_LOG_PATH = BASE_DIR / 'data' / 'events.jsonl'
BLOG_DRAFTS_PATH = BASE_DIR / 'data' / 'blog_drafts'

def log_event(event_type: str, data: Dict[str, Any], max_lines: int = 5000) -> bool:
    event = {'timestamp': datetime.now().isoformat(), 'event_type': event_type, 'data': data}
    try:
        with _log_lock:
            EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            # Rotación: si el archivo supera max_lines, mantener solo los últimos max_lines
            if EVENT_LOG_PATH.exists():
                lines = EVENT_LOG_PATH.read_text(encoding='utf-8').strip().splitlines()
                if len(lines) > max_lines:
                    EVENT_LOG_PATH.write_text('\n'.join(lines[-max_lines:]) + '\n', encoding='utf-8')
            with open(EVENT_LOG_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
        try:
            generate_blog_draft(event_type, data)
        except Exception:
            pass
        return True
    except Exception as e:
        print(f'Error: {e}')
        return False

def generate_blog_draft(event_type: str, data: Dict[str, Any]) -> bool:
    publishable_events = {'benchmark.completed', 'tuning.completed', 'analysis.generated', 'baseline.updated'}
    if event_type not in publishable_events: return False
    try:
        slug = event_type.replace('.', '_').replace(' ', '_').lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{slug}_{timestamp}.md'
        draft_path = BLOG_DRAFTS_PATH / filename
        content = f'''---
title: "{data.get("title", "New AMD.AI Update")}"
date: {datetime.now().isoformat()}
tags: [amd, ai, {event_type.split('.')[1]}]
category: logs
draft: true
---

## Event: {event_type}

{data.get("summary", "No summary provided.")}

### Details
```json
{json.dumps(data.get("details", {}), indent=2)}
```
'''
        BLOG_DRAFTS_PATH.mkdir(parents=True, exist_ok=True)
        with open(draft_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        return False
