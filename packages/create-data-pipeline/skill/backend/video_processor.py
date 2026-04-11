"""
视频处理器 - 使用 OpenCV 提取关键帧 + 多模态 LLM 理解视频内容

核心算法：
1. 读取视频元数据（时长、分辨率、FPS、编码器）
2. 关键帧提取：场景变化检测 + 均匀采样混合策略
3. 去重 + 限制帧数 → 送入多模态 LLM 理解
4. 可选：提取音频并转写（需要 ffmpeg + whisper）
5. 合成：元数据 + 帧描述 + 音频转写 → 完整文档
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .file_processor import ProcessedDocument

logger = logging.getLogger(__name__)

# 视频文件扩展名
VIDEO_EXTENSIONS = {
    ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv",
    ".webm", ".m4v", ".mpg", ".mpeg", ".3gp", ".ts",
}


class VideoProcessor:
    """
    视频处理器 - 提取关键帧并用传统方法（OCR/描述）处理

    这是不使用多模态 LLM 的回退处理器。
    完整的视频理解功能在 MultimodalProcessor 中实现。
    """

    # ---- 关键帧提取参数 ----
    MAX_KEYFRAMES = 16          # 最多提取的关键帧数
    MIN_KEYFRAMES = 4           # 最少保留的关键帧数
    SCENE_THRESHOLD = 0.65      # 场景变化检测阈值（直方图相关性 < 此值 = 新场景）
    UNIFORM_INTERVAL_SEC = 10   # 均匀采样间隔（秒）
    MIN_FRAME_INTERVAL_SEC = 2  # 两个关键帧之间最小间隔（秒），防止连续变化导致帧过密
    MAX_VIDEO_DURATION = 3600   # 最大处理视频时长（秒），超过截断
    FRAME_JPEG_QUALITY = 85     # 关键帧 JPEG 压缩质量

    def process(self, file_path: str) -> ProcessedDocument:
        """
        处理视频文件 - 提取元数据和关键帧（不使用 LLM）

        Args:
            file_path: 视频文件路径

        Returns:
            ProcessedDocument 对象
        """
        path = Path(file_path)
        errors = []
        content_parts = []
        metadata = {
            "source": str(path),
            "type": path.suffix.lstrip('.'),
            "processor": "video_basic",
        }

        try:
            import cv2
        except ImportError:
            return ProcessedDocument(
                content="[视频处理需要 opencv-python，请安装: pip install opencv-python]",
                metadata=metadata,
                errors=["opencv-python 未安装"]
            )

        try:
            video_meta = self._extract_video_metadata(file_path)
            metadata.update(video_meta)

            content_parts.append(self._format_metadata(video_meta))

            # 提取关键帧的基本描述（不使用 LLM）
            keyframes = self.extract_keyframes(file_path)
            if keyframes:
                content_parts.append(
                    f"\n视频共提取 {len(keyframes)} 个关键帧，"
                    f"时间戳覆盖: {keyframes[0]['timestamp_sec']:.1f}s - {keyframes[-1]['timestamp_sec']:.1f}s"
                )
                metadata["keyframes_count"] = len(keyframes)

        except Exception as e:
            logger.error(f"视频处理失败: {e}")
            errors.append(f"视频处理失败: {str(e)}")

        return ProcessedDocument(
            content="\n".join(content_parts),
            metadata=metadata,
            errors=errors
        )

    def _extract_video_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取视频元数据"""
        import cv2

        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise RuntimeError(f"无法打开视频文件: {file_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration_sec = frame_count / fps if fps > 0 else 0
            fourcc_code = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = "".join([chr((fourcc_code >> 8 * i) & 0xFF) for i in range(4)])

            file_size = os.path.getsize(file_path)

            return {
                "fps": round(fps, 2),
                "frame_count": frame_count,
                "width": width,
                "height": height,
                "duration_sec": round(duration_sec, 2),
                "duration_str": self._format_duration(duration_sec),
                "codec": codec.strip(),
                "file_size_mb": round(file_size / (1024 * 1024), 2),
            }
        finally:
            cap.release()

    def extract_keyframes(self, file_path: str) -> List[Dict[str, Any]]:
        """
        关键帧提取 - 场景变化检测 + 均匀采样混合策略

        算法：
        1. 始终保留首帧和尾帧
        2. 通过直方图相关性检测场景变化帧
        3. 在场景变化帧之间补充均匀采样帧
        4. 合并去重，控制在 MAX_KEYFRAMES 以内

        Returns:
            关键帧列表，每个元素包含:
            - frame_index: 帧序号
            - timestamp_sec: 时间戳（秒）
            - frame_bytes: JPEG 编码的帧数据
            - source: 来源（'first', 'last', 'scene_change', 'uniform'）
        """
        import cv2
        import numpy as np

        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise RuntimeError(f"无法打开视频: {file_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            if total_frames <= 0:
                return []

            # 限制处理时长
            max_frames = int(min(duration, self.MAX_VIDEO_DURATION) * fps)
            max_frames = min(max_frames, total_frames)

            # ---- 第一步：场景变化检测 ----
            scene_changes = []
            min_frame_gap = int(self.MIN_FRAME_INTERVAL_SEC * fps)
            sample_step = max(1, int(fps / 2))  # 每秒检测 2 次（节省 CPU）

            prev_hist = None
            last_scene_frame = -min_frame_gap  # 确保首帧可以被选中

            for frame_idx in range(0, max_frames, sample_step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    break

                # 计算灰度直方图
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                hist = cv2.calcHist([gray], [0], None, [64], [0, 256])
                cv2.normalize(hist, hist)

                if prev_hist is not None:
                    correlation = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                    if correlation < self.SCENE_THRESHOLD and (frame_idx - last_scene_frame) >= min_frame_gap:
                        scene_changes.append(frame_idx)
                        last_scene_frame = frame_idx

                prev_hist = hist

            logger.info(f"场景变化检测到 {len(scene_changes)} 个切换点")

            # ---- 第二步：均匀采样 ----
            uniform_interval_frames = int(self.UNIFORM_INTERVAL_SEC * fps)
            uniform_frames = list(range(0, max_frames, max(1, uniform_interval_frames)))

            # ---- 第三步：合并帧列表 ----
            # 首帧 + 尾帧 + 场景变化帧 + 均匀帧
            all_candidate_frames = set()
            all_candidate_frames.add(0)  # 首帧
            if max_frames > 1:
                all_candidate_frames.add(max_frames - 1)  # 尾帧
            all_candidate_frames.update(scene_changes)
            all_candidate_frames.update(uniform_frames)

            # 排序
            sorted_frames = sorted(all_candidate_frames)

            # ---- 第四步：控制帧数，智能选择 ----
            if len(sorted_frames) > self.MAX_KEYFRAMES:
                sorted_frames = self._select_best_frames(
                    sorted_frames, scene_changes, max_frames
                )

            # ---- 第五步：提取帧数据 ----
            keyframes = []
            for frame_idx in sorted_frames:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    continue

                # 编码为 JPEG
                encode_param = [cv2.IMWRITE_JPEG_QUALITY, self.FRAME_JPEG_QUALITY]
                success, buffer = cv2.imencode('.jpg', frame, encode_param)
                if not success:
                    continue

                frame_bytes = buffer.tobytes()
                timestamp = frame_idx / fps

                source = 'uniform'
                if frame_idx == 0:
                    source = 'first'
                elif frame_idx == max_frames - 1:
                    source = 'last'
                elif frame_idx in scene_changes:
                    source = 'scene_change'

                keyframes.append({
                    "frame_index": frame_idx,
                    "timestamp_sec": round(timestamp, 2),
                    "timestamp_str": self._format_duration(timestamp),
                    "frame_bytes": frame_bytes,
                    "frame_size": len(frame_bytes),
                    "source": source,
                })

            logger.info(
                f"关键帧提取完成：总帧数={total_frames}，"
                f"场景变化={len(scene_changes)}，最终选择={len(keyframes)}"
            )
            return keyframes

        finally:
            cap.release()

    def _select_best_frames(
        self, sorted_frames: List[int], scene_changes: List[int], total_frames: int
    ) -> List[int]:
        """
        在帧过多时智能选择最有价值的帧

        优先级：首帧 > 尾帧 > 场景变化帧 > 均匀采样帧
        """
        must_keep = set()
        must_keep.add(sorted_frames[0])   # 首帧
        must_keep.add(sorted_frames[-1])  # 尾帧

        # 优先保留场景变化帧
        sc_set = set(scene_changes)
        scene_frames = [f for f in sorted_frames if f in sc_set]

        # 如果场景变化帧已经超过预算，均匀抽样场景帧
        budget = self.MAX_KEYFRAMES - len(must_keep)
        if len(scene_frames) > budget:
            step = max(1, len(scene_frames) // budget)
            scene_frames = scene_frames[::step][:budget]

        must_keep.update(scene_frames)

        # 均匀帧填充剩余预算
        remaining_budget = self.MAX_KEYFRAMES - len(must_keep)
        if remaining_budget > 0:
            other_frames = [f for f in sorted_frames if f not in must_keep]
            if len(other_frames) > remaining_budget:
                step = max(1, len(other_frames) // remaining_budget)
                other_frames = other_frames[::step][:remaining_budget]
            must_keep.update(other_frames)

        return sorted(must_keep)[:self.MAX_KEYFRAMES]

    def _format_metadata(self, meta: Dict[str, Any]) -> str:
        """格式化视频元数据为可读文本"""
        return (
            f"视频信息：时长 {meta.get('duration_str', '未知')}，"
            f"分辨率 {meta.get('width', 0)}×{meta.get('height', 0)}，"
            f"帧率 {meta.get('fps', 0)} FPS，"
            f"编码 {meta.get('codec', '未知')}，"
            f"文件大小 {meta.get('file_size_mb', 0)} MB"
        )

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """将秒数格式化为 HH:MM:SS"""
        seconds = max(0, seconds)
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    @staticmethod
    def extract_audio_track(video_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        从视频中提取音频轨道（需要 ffmpeg）

        Args:
            video_path: 视频文件路径
            output_path: 音频输出路径，默认为临时文件

        Returns:
            音频文件路径，失败返回 None
        """
        import subprocess
        import shutil

        if not shutil.which("ffmpeg"):
            logger.warning("ffmpeg 不可用，无法提取音频")
            return None

        if output_path is None:
            output_path = os.path.join(
                tempfile.gettempdir(),
                f"wiki_video_audio_{os.path.basename(video_path)}.wav"
            )

        try:
            subprocess.run(
                [
                    "ffmpeg", "-i", video_path,
                    "-vn",              # 不要视频
                    "-acodec", "pcm_s16le",  # 16-bit PCM
                    "-ar", "16000",     # 16kHz 采样率（适合语音识别）
                    "-ac", "1",         # 单声道
                    "-y",               # 覆盖输出
                    output_path,
                ],
                capture_output=True,
                timeout=120,
                check=True,
            )
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.warning(f"音频提取失败: {e}")

        return None
