#!/usr/bin/env python3
"""简单的视频读取脚本"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.processors.video_processor import VideoProcessor

def main(video_path):
    print(f"正在处理视频: {video_path}")

    vp = VideoProcessor()

    # 提取元数据
    print("\n=== 视频元数据 ===")
    try:
        meta = vp._extract_video_metadata(video_path)
        print(vp._format_metadata(meta))
    except Exception as e:
        print(f"元数据提取失败: {e}")

    # 提取关键帧
    print("\n=== 提取关键帧 ===")
    try:
        keyframes = vp.extract_keyframes(video_path)
        print(f"成功提取 {len(keyframes)} 个关键帧:")
        for kf in keyframes:
            print(f"  - [{kf['timestamp_str']}] {kf['source']} - {kf['frame_size']} 字节")

        # 保存关键帧到临时文件
        import tempfile
        import os
        temp_dir = tempfile.mkdtemp(prefix="video_frames_")
        print(f"\n关键帧将保存到: {temp_dir}")

        for i, kf in enumerate(keyframes):
            frame_path = os.path.join(temp_dir, f"frame_{i:02d}_{kf['timestamp_str'].replace(':', '-')}.jpg")
            with open(frame_path, 'wb') as f:
                f.write(kf['frame_bytes'])
            print(f"  保存: {frame_path}")

        print(f"\n完成！关键帧保存在: {temp_dir}")

    except Exception as e:
        print(f"关键帧提取失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python read_video.py <视频文件路径>")
        sys.exit(1)
    main(sys.argv[1])
