#!/usr/bin/env python3
"""
分批上传 gfriends-org/content 到 GitHub 的 Content/ 目录（保持原结构）
用法：python upload_content_same_dir.py <content 目录路径> [每批文件数]
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from fnmatch import fnmatch

SUPPORTED_EXTENSIONS = ('*.jpg', '*.jpeg', '*.png', '*.webp', '*.gif', '*.bmp', '*.svg')
BATCH_SIZE_DEFAULT = 5000
TARGET_DIR = Path("Content")

def get_images(source_dir: Path) -> list[Path]:
    images = []
    for root, dirs, files in os.walk(source_dir):
        for f in files:
            if any(fnmatch(f.lower(), ext) for ext in SUPPORTED_EXTENSIONS):
                images.append(Path(root) / f)
    return sorted(images)

def get_uploaded_files() -> set[str]:
    if not TARGET_DIR.exists():
        return set()

    uploaded = set()
    for root, dirs, files in os.walk(TARGET_DIR):
        for f in files:
            if any(fnmatch(f.lower(), ext) for ext in SUPPORTED_EXTENSIONS):
                full_path = Path(root) / f
                rel_path = str(full_path.relative_to(TARGET_DIR))
                uploaded.add(rel_path)
    return uploaded

def upload_batch(images: list[Path], source_dir: Path, batch_num: int, uploaded_files: set[str]):
    count = 0
    skipped = 0

    for img in images:
        rel_path = img.relative_to(source_dir)
        rel_path_str = str(rel_path)

        if rel_path_str in uploaded_files:
            skipped += 1
            continue

        dest_path = TARGET_DIR / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(img, dest_path)
        count += 1

    if count == 0:
        print(f"  ⏭️  Batch {batch_num}: 该批次文件已全部上传，跳过\n")
        return 0

    print(f"  📦 新上传 {count} 个文件，跳过 {skipped} 个已上传")
    print(f"  🔧 git add Content/ ...")
    subprocess.run(["git", "add", "Content/"], check=True)

    print(f"  💾 git commit ...")
    commit_msg = f"Add Content batch {batch_num} ({count} files)"
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)

    print(f"  🚀 git push ...")
    subprocess.run(["git", "push", "origin", "main"], check=True)

    new_uploaded = get_uploaded_files()
    uploaded_files.update(new_uploaded)

    print(f"  ✅ Batch {batch_num} 完成！\n")
    return count

def main():
    if len(sys.argv) < 2:
        print("用法：python upload_content_same_dir.py <content 目录路径> [每批文件数]")
        print("示例：python upload_content_same_dir.py ../gfriends-org/content 5000")
        sys.exit(1)

    source_dir = Path(sys.argv[1]).resolve()
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else BATCH_SIZE_DEFAULT

    if not source_dir.exists():
        print(f"❌ 目录不存在：{source_dir}")
        sys.exit(1)

    print(f"📂 扫描目录：{source_dir}")
    images = get_images(source_dir)
    total = len(images)

    if total == 0:
        print("❌ 没有找到图片文件")
        sys.exit(1)

    print("🔍 检查已上传的文件...")
    uploaded_files = get_uploaded_files()
    already_uploaded = sum(1 for img in images if str(img.relative_to(source_dir)) in uploaded_files)
    remaining = total - already_uploaded

    print(f"📊 总共 {total} 张图片")
    print(f"📊 已上传 {already_uploaded} 张")
    print(f"📊 剩余 {remaining} 张待上传")

    if remaining == 0:
        print("\n🎉 所有文件已上传完成！")
        return

    total_batches = (remaining + batch_size - 1) // batch_size
    print(f"📊 每批 {batch_size} 张，共 {total_batches} 批\n")

    batch_num = 1
    remaining_images = [img for img in images if str(img.relative_to(source_dir)) not in uploaded_files]

    for i in range(0, len(remaining_images), batch_size):
        batch_images = remaining_images[i:i+batch_size]
        print("=" * 60)
        print(f"🚀 开始处理批次 {batch_num}/{total_batches}")
        print("=" * 60)

        upload_batch(batch_images, source_dir, batch_num, uploaded_files)
        batch_num += 1

    print("\n" + "=" * 60)
    print(f"🎉 全部完成！Content/ 目录共有 {len(get_uploaded_files())} 个文件")
    print("=" * 60)
    print("🌐 访问 URL: https://cdn.jsdelivr.net/gh/li-peifeng/gfriends@main/Content/子目录/图片名.jpg")

if __name__ == "__main__":
    main()
