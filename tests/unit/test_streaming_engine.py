# tests/unit/test_streaming_engine.py
import pytest
import time
from backend.ppt.streaming_engine import StreamingEngine

class MockLLMGenerator:
    """模拟 LLM 生成器"""

    def __init__(self, tokens, delays):
        """
        Args:
            tokens: token 列表
            delays: 每个 token 之前的延迟（秒）
        """
        self.tokens = tokens
        self.delays = delays

    def __iter__(self):
        for token, delay in zip(self.tokens, self.delays):
            time.sleep(delay)
            yield token

def test_thinking_detection():
    """测试思考状态检测"""
    engine = StreamingEngine()

    # 模拟极慢速生成 - 第一个 token 后等待很长时间
    # Token 1: 0.1s (快速)
    # Token 2: 4.0s 后 (非常慢，触发思考)
    # Token 3: 0.1s
    slow_generator = MockLLMGenerator(
        tokens=['A', 'B', 'C'],
        delays=[0.1, 4.0, 0.1]
    )

    events = list(engine.stream_with_pacing(slow_generator))

    # 应该包含 thinking 事件
    thinking_events = [e for e in events if e['type'] == 'thinking']
    assert len(thinking_events) > 0, f"Expected thinking events, got: {[e['type'] for e in events]}"

    # 应该包含 token 事件
    token_events = [e for e in events if e['type'] == 'token']
    assert len(token_events) > 0

def test_normal_streaming():
    """测试正常流式输出"""
    engine = StreamingEngine()

    # 模拟正常速度（5 tokens/秒）
    normal_generator = MockLLMGenerator(
        tokens=['Fast', ' ', 'output'],
        delays=[0.2, 0.2, 0.2]
    )

    events = list(engine.stream_with_pacing(normal_generator))

    # 不应该包含 thinking 事件
    thinking_events = [e for e in events if e['type'] == 'thinking']
    assert len(thinking_events) == 0

    # 应该包含完整的 token
    all_text = ''.join([e['text'] for e in events if e['type'] == 'token'])
    assert 'Fast output' in all_text

def test_stop_callback():
    """测试停止回调"""
    engine = StreamingEngine()

    # 创建一个在第 2 个 token 后返回 True 的回调
    stop_after_two = [False]
    def should_stop():
        if stop_after_two[0]:
            return True
        stop_after_two[0] = True
        return False

    generator = MockLLMGenerator(
        tokens=['1', '2', '3', '4'],
        delays=[0.1, 0.1, 0.1, 0.1]
    )

    events = list(engine.stream_with_pacing(generator, on_should_stop=should_stop))

    # 最后一个事件应该是 stopped
    assert events[-1]['type'] == 'stopped'
