# tests/unit/test_state_manager.py
import pytest
import time
from datetime import datetime
from backend.ppt.state_manager import GenerationStateManager
from backend.ppt.models import SlideLayout, LayoutElement


def test_create_job():
    """测试创建任务"""
    manager = GenerationStateManager()

    state = manager.create_job(
        job_id='test-job',
        wiki_ids=['test'],
        instruction='Test',
        template_layouts=[]
    )

    assert state.job_id == 'test-job'
    assert state.status == 'idle'
    assert len(state.slides) == 0


def test_pause_and_resume():
    """测试暂停和恢复"""
    manager = GenerationStateManager()

    # 创建任务
    manager.create_job(
        job_id='test-job',
        wiki_ids=['test'],
        instruction='Test',
        template_layouts=[]
    )

    # 暂停
    assert manager.pause('test-job') == False  # 不能暂停 idle 状态

    # 先设为 generating（使用测试专用方法）
    manager._update_state_directly('test-job', status='generating')

    # 现在可以暂停
    assert manager.pause('test-job') == True
    assert manager.get_state('test-job').status == 'paused'

    # 恢复
    assert manager.resume('test-job') == True
    assert manager.get_state('test-job').status == 'generating'


def test_add_slide():
    """测试添加幻灯片"""
    manager = GenerationStateManager()

    manager.create_job(
        job_id='test-job',
        wiki_ids=['test'],
        instruction='Test',
        template_layouts=[]
    )

    slide_data = {'type': 'title', 'text': 'Test Slide'}
    assert manager.add_slide('test-job', slide_data) == True

    state = manager.get_state('test-job')
    assert len(state.slides) == 1
    assert state.slides[0] == slide_data
    assert state.current_index == 0


def test_user_edits():
    """测试用户编辑记录"""
    manager = GenerationStateManager()

    manager.create_job(
        job_id='test-job',
        wiki_ids=['test'],
        instruction='Test',
        template_layouts=[]
    )

    edit_data = {'type': 'text', 'x': 100, 'y': 200}
    assert manager.add_edit('test-job', 0, edit_data) == True

    state = manager.get_state('test-job')
    assert 0 in state.user_edits
    assert state.user_edits[0] == edit_data


def test_cleanup_old_jobs():
    """测试清理旧任务"""
    manager = GenerationStateManager()

    # 创建一个任务
    manager.create_job(
        job_id='test-job',
        wiki_ids=['test'],
        instruction='Test',
        template_layouts=[]
    )

    # 立即清理，应该没有删除
    deleted = manager.cleanup_old_jobs(max_age_hours=0)
    assert deleted == 0

    # 手动修改创建时间，模拟旧任务（使用测试专用方法）
    manager._update_state_directly('test-job', created_at=datetime.fromtimestamp(0))  # 1970年

    deleted = manager.cleanup_old_jobs(max_age_hours=0)
    assert deleted == 1
    assert manager.get_state('test-job') is None


def test_concurrent_pause_resume():
    """Test concurrent access to pause/resume"""
    import threading

    manager = GenerationStateManager()
    manager.create_job('test-job', ['test'], 'Test', [])

    # Modify to generating state (using test-only method)
    manager._update_state_directly('test-job', status='generating')

    results = []

    def pause_job():
        time.sleep(0.01)
        results.append(manager.pause('test-job'))

    threads = [threading.Thread(target=pause_job) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Only one should succeed
    success_count = sum(1 for r in results if r)
    assert success_count == 1
