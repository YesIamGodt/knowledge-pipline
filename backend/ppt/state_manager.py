"""
生成状态管理器
管理所有活跃的生成任务，支持暂停/恢复、编辑记录
"""
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
from copy import deepcopy
from backend.ppt.models import GenerationState, SlideLayout


class GenerationStateManager:
    """管理生成任务状态，支持暂停/恢复"""

    # Valid state transitions
    VALID_TRANSITIONS = {
        'idle': ['generating'],
        'generating': ['paused', 'completed', 'failed'],
        'paused': ['generating'],
        'completed': [],
        'failed': ['generating']
    }

    def __init__(self):
        self.states: Dict[str, GenerationState] = {}
        self.lock = threading.Lock()

    def create_job(
        self,
        job_id: str,
        wiki_ids: List[str],
        instruction: str,
        template_layouts: List[SlideLayout]
    ) -> GenerationState:
        """创建新的生成任务"""
        with self.lock:
            state = GenerationState(
                job_id=job_id,
                status='idle',
                slides=[],
                current_index=0,
                wiki_ids=wiki_ids,
                instruction=instruction,
                template_layouts=template_layouts,
                user_edits={},
                context_stack=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.states[job_id] = state
            return state

    def get_state(self, job_id: str) -> Optional[GenerationState]:
        """获取任务状态（返回防御性拷贝）"""
        with self.lock:
            state = self.states.get(job_id)
            if state:
                # Return a copy to prevent external mutation
                return deepcopy(state)
            return None

    def pause(self, job_id: str) -> bool:
        """暂停任务"""
        with self.lock:
            state = self.states.get(job_id)
            if not state:
                return False

            # Validate state transition
            if state.status not in self.VALID_TRANSITIONS or 'paused' not in self.VALID_TRANSITIONS[state.status]:
                return False

            if state.status == 'generating':
                state.status = 'paused'
                state.updated_at = datetime.now()
                # 保存当前上下文到 stack
                state.context_stack.append({
                    'slides': state.slides.copy(),
                    'current_index': state.current_index
                })
                return True
            return False

    def resume(
        self,
        job_id: str,
        user_edits: Dict[int, Dict[str, Any]] = None
    ) -> bool:
        """恢复任务"""
        with self.lock:
            state = self.states.get(job_id)
            if not state:
                return False

            # Validate state transition
            if state.status not in self.VALID_TRANSITIONS or 'generating' not in self.VALID_TRANSITIONS[state.status]:
                return False

            if state.status == 'paused':
                state.status = 'generating'
                state.updated_at = datetime.now()

                # 合并用户编辑
                if user_edits:
                    state.user_edits.update(user_edits)

                return True
            return False

    def add_slide(self, job_id: str, slide_data: Dict[str, Any]) -> bool:
        """添加幻灯片"""
        with self.lock:
            state = self.states.get(job_id)
            if state:
                state.slides.append(slide_data)
                state.current_index = len(state.slides) - 1
                state.updated_at = datetime.now()
                return True
            return False

    def add_edit(self, job_id: str, slide_index: int, fabric_json: Dict[str, Any]) -> bool:
        """记录用户编辑"""
        with self.lock:
            state = self.states.get(job_id)
            if state:
                state.user_edits[slide_index] = fabric_json
                state.updated_at = datetime.now()
                return True
            return False

    def get_context_for_resume(self, job_id: str) -> Optional[Dict[str, Any]]:
        """生成恢复时的上下文（包含用户编辑）"""
        with self.lock:  # Hold lock for entire read
            state = self.states.get(job_id)
            if not state:
                return None

            return {
                'original_instruction': state.instruction,
                'slides_so_far': state.slides.copy(),
                'recent_user_edits': self._get_recent_edits(state),
                'next_slide_index': state.current_index,
                'template_layouts': [l.__dict__ for l in state.template_layouts]
            }

    def _get_recent_edits(self, state: GenerationState) -> Dict[int, Dict[str, Any]]:
        """获取最近的用户编辑（最近 3 个）"""
        if not state.user_edits:
            return {}

        # 按索引排序，返回最近的 3 个
        sorted_edits = sorted(state.user_edits.items(), key=lambda x: x[0], reverse=True)
        return dict(sorted_edits[:3])

    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """清理超过指定时间的旧任务"""
        with self.lock:
            now = datetime.now()
            to_delete = []

            for job_id, state in self.states.items():
                age = now - state.created_at
                if age.total_seconds() > max_age_hours * 3600:
                    to_delete.append(job_id)

            for job_id in to_delete:
                del self.states[job_id]

            return len(to_delete)

    def _update_state_directly(self, job_id: str, **kwargs) -> bool:
        """直接更新状态（仅供测试使用）"""
        with self.lock:
            state = self.states.get(job_id)
            if state:
                for key, value in kwargs.items():
                    if hasattr(state, key):
                        setattr(state, key, value)
                return True
            return False
