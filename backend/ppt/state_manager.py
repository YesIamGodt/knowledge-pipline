"""
Generation State Manager - Stub implementation (Task 2.2)
"""
from backend.ppt.models import GenerationState

class GenerationStateManager:
    """Manages generation state for pause/resume functionality"""

    def __init__(self):
        self.jobs = {}

    def create_job(self, job_id, wiki_ids, instruction, template_layouts):
        """Create a new generation job"""
        self.jobs[job_id] = GenerationState(
            job_id=job_id,
            wiki_ids=wiki_ids,
            instruction=instruction,
            template_layouts=template_layouts,
            status='running'
        )

    def get_state(self, job_id):
        """Get the current state of a job"""
        return self.jobs.get(job_id)

    def pause(self, job_id):
        """Pause a generation job"""
        if job_id in self.jobs:
            self.jobs[job_id].status = 'paused'

    def resume(self, job_id, user_edits=None):
        """Resume a paused generation job"""
        if job_id in self.jobs:
            self.jobs[job_id].status = 'running'
