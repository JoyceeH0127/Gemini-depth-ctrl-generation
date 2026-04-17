import os
import numpy as np
import trimesh
import cv2
import json
from glob import glob


# --------------------------------------
# 1. 路径配置
# --------------------------------------
MESH_PATH = "D:\\dataset\\dataset\\Gibson\\Hiteman\\mesh_z_up.obj"
JSON_DIR  = "D:\\dataset\\dataset\\Gibson\\Hiteman\\pano\\points"
OUT_DIR   = "D:\\dataset\\dataset\\Gibson\\Hiteman\\pano\\depth_vis"

os.makedirs(OUT_DIR, exist_ok=True)


# --------------------------------------
# 2. 加载 mesh & ray intersector（只做一次）
# --------------------------------------
mesh = trimesh.load(MESH_PATH, process=False)
ray_intersector = trimesh.ray.ray_pyembree.RayMeshIntersector(mesh)


# --------------------------------------
# 3. 全景分辨率
# --------------------------------------
H = 1024
W = 2048


# --------------------------------------
# 4. 预计算球面方向（相机坐标系，只算一次）
# --------------------------------------
ys = np.linspace(0, H - 1, H)
xs = np.linspace(0, W - 1, W)
xs, ys = np.meshgrid(xs, ys)

yaw = np.pi - ((xs / W) * 2 * np.pi - np.pi)
pitch = np.pi / 2 - (ys / H) * np.pi

dirs_cam = np.stack([
    np.cos(pitch) * np.sin(yaw),
    np.sin(pitch),
    np.cos(pitch) * np.cos(yaw)
], axis=-1)

dirs_cam = dirs_cam.reshape(-1, 3).astype(np.float32)


# --------------------------------------
# 5. 遍历 JSON 文件
# --------------------------------------
json_files = sorted(glob(os.path.join(JSON_DIR, "*.json")))

print(f"Found {len(json_files)} json files")

for json_path in json_files:
    base_name = os.path.splitext(os.path.basename(json_path))[0]
    out_png = os.path.join(OUT_DIR, base_name + ".png")

    print(f"▶ Processing {base_name}")

    # ------------------------------
    # 5.1 读取 camera pose
    # ------------------------------
    with open(json_path, "r") as f:
        json_data = json.load(f)

    camera_rt = np.array(json_data[1]["camera_rt_matrix"], dtype=np.float32)
    R_c2w = camera_rt[:3, :3]
    t_c2w = camera_rt[:3, 3]

    # ------------------------------
    # 5.2 方向转世界坐标
    # ------------------------------
    dirs_world = (R_c2w @ dirs_cam.T).T
    dirs_world /= np.linalg.norm(dirs_world, axis=1, keepdims=True)

    origins = np.repeat(t_c2w[None, :], dirs_world.shape[0], axis=0)

    # ------------------------------
    # 5.3 Ray casting
    # ------------------------------
    locations, index_ray, _ = ray_intersector.intersects_location(
        origins, dirs_world, multiple_hits=False
    )

    depth_flat = np.zeros(origins.shape[0], dtype=np.float32)
    hit_vec = locations - origins[index_ray]
    depth_flat[index_ray] = np.linalg.norm(hit_vec, axis=1)

    depth = depth_flat.reshape(H, W)

    # ------------------------------
    # 5.4 可视化并保存
    # ------------------------------
    vis = depth.copy()
    vis[vis == 0] = np.nan
    if np.all(np.isnan(vis)):
        print(f"⚠️ No hit for {base_name}")
        continue

    vis = vis / np.nanmax(vis)
    vis = (vis * 255).astype(np.uint8)

    cv2.imwrite(out_png, vis)

print("✅ All panoramic depth maps rendered")
