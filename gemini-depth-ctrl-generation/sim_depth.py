import os
import pickle
import numpy as np
import lz4.frame
import cv2
from tqdm import tqdm


def load_depth_lz4(depth_path):
    """只使用 lz4 解压深度 pkl"""
    with open(depth_path, "rb") as f:
        obj = pickle.load(f)

    data = obj["data"]
    shape = tuple(obj["shape"])
    dtype = np.dtype(obj["dtype"])

    raw = lz4.frame.decompress(data)
    expected_bytes = np.prod(shape) * dtype.itemsize

    if len(raw) != expected_bytes:
        raise ValueError(
            f"❌ 解压尺寸不匹配: {depth_path}, "
            f"got={len(raw)}, expected={expected_bytes}"
        )

    depth = np.frombuffer(raw, dtype=dtype).reshape(shape)
    return depth


def depth_to_vis(depth, invalid_val=0.0):
    """
    深度 -> uint8 可视化图
    使用 percentile 归一化，避免极端值
    """
    depth = depth.astype(np.float32)

    # 去掉无效值
    mask = np.isfinite(depth) & (depth > invalid_val)
    if mask.sum() == 0:
        return np.zeros(depth.shape, dtype=np.uint8)

    vmin = np.percentile(depth[mask], 2)
    vmax = np.percentile(depth[mask], 98)

    depth_norm = np.clip((depth - vmin) / (vmax - vmin + 1e-6), 0, 1)
    depth_uint8 = (depth_norm * 255).astype(np.uint8)

    return depth_uint8


def process_depth_folder(
    input_dir,
    output_dir,
    ext=".pkl",
    use_colormap=True
):
    os.makedirs(output_dir, exist_ok=True)

    files = [
        f for f in os.listdir(input_dir)
        if f.endswith(".lz4")
    ]

    print(f"📦 找到 {len(files)} 个深度文件")

    for fname in tqdm(files):
        in_path = os.path.join(input_dir, fname)
        out_name = os.path.splitext(fname)[0] + ".png"
        out_path = os.path.join(output_dir, out_name)

        try:
            depth = load_depth_lz4(in_path)
            depth_vis = depth_to_vis(depth)

            if use_colormap:
                depth_vis = cv2.applyColorMap(
                    depth_vis, cv2.COLORMAP_JET
                )

            cv2.imwrite(out_path, depth_vis)

        except Exception as e:
            print(f"⚠️ 处理失败 {fname}: {e}")


def find_cube_depth_dirs(base_dir, prefix="Autel"):
    """在 base_dir 下查找所有 Autel* 子目录中的 CubeDepth"""
    cube_depth_dirs = []

    for name in os.listdir(base_dir):
        path = os.path.join(base_dir, name)
        if not os.path.isdir(path):
            continue
        if not name.startswith(prefix):
            continue

        for root, dirs, _files in os.walk(path):
            if "CubeDepth" in dirs:
                cube_depth_dirs.append(os.path.join(root, "CubeDepth"))

    return cube_depth_dirs


if __name__ == "__main__":
    base_dir = r"D:\depth_ctrl\sim_scenes\sdg_gemini\gemini_0127\output\sdg_erp"
    cube_depth_dirs = find_cube_depth_dirs(base_dir)

    print(f"📦 找到 {len(cube_depth_dirs)} 个 CubeDepth 目录")

    for depth_dir in cube_depth_dirs:
        output_vis_dir = depth_dir + "_vis"
        process_depth_folder(
            depth_dir,
            output_vis_dir,
            use_colormap=True  # False 则保存灰度图
        )
