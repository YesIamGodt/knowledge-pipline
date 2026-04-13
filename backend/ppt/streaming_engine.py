"""
智能分批流式输出引擎
监控 LLM 输出速度，动态调整发送节奏，提供真实的直播体验
"""
import time
import random
from typing import Generator, Dict, Any, Callable

class StreamingEngine:
    """智能分批流式输出引擎"""

    THINKING_THRESHOLD = 2.0  # tokens/秒 - 低于此速度显示思考提示
    FAST_THRESHOLD = 10.0     # tokens/秒 - 高于此速度人为延迟

    def __init__(self):
        self.thinking_messages = [
            "🤔 正在分析知识库...",
            "📚 正在整理内容...",
            "💡 正在规划布局...",
            "🎨 正在选择样式...",
            "✨ 正在优化设计..."
        ]

    def stream_with_pacing(
        self,
        llm_generator: Generator[str, None, None],
        on_should_stop: Callable[[], bool] = lambda: False
    ) -> Generator[Dict[str, Any], None, None]:
        """
        监控 LLM 输出速度，动态调整发送节奏

        Args:
            llm_generator: LLM token 生成器
            on_should_stop: 检查是否应该停止的回调函数

        Yields:
            SSE 事件字典:
            - {'type': 'thinking', 'message': str}
            - {'type': 'token', 'text': str}
        """
        token_buffer = []
        last_token_time = time.time()
        last_yield_time = time.time()
        thinking_sent = False  # Track if we've sent a thinking message

        for token in llm_generator:
            # 检查是否应该停止
            if on_should_stop():
                yield {'type': 'stopped', 'message': '用户已停止生成'}
                return

            now = time.time()
            time_delta = now - last_token_time
            speed = 1.0 / time_delta if time_delta > 0 else 0
            last_token_time = now

            token_buffer.append(token)

            # 状态 1: 思考中（速度过慢）
            if speed < self.THINKING_THRESHOLD and len(token_buffer) < 5:
                # 如果等待超过 3 秒，发送思考提示
                if now - last_yield_time > 3.0 and not thinking_sent:
                    yield {
                        'type': 'thinking',
                        'message': random.choice(self.thinking_messages)
                    }
                    last_yield_time = now
                    thinking_sent = True
                    continue

            # 状态 2: 输出太快，放慢节奏
            if speed > self.FAST_THRESHOLD:
                # 人为延迟，让用户看清
                time.sleep(0.05)

            # 状态 3: 正常输出，批量发送
            # 积累 3-5 个 token 或等待超过 80ms 后发送
            if len(token_buffer) >= 3 or (now - last_yield_time > 0.08):
                yield {
                    'type': 'token',
                    'text': ''.join(token_buffer)
                }
                token_buffer = []
                last_yield_time = now
                thinking_sent = False  # Reset after yielding tokens

        # 发送剩余内容
        if token_buffer:
            yield {'type': 'token', 'text': ''.join(token_buffer)}
