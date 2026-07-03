from typing import List

import numpy as np
import torch
from dreifus.matrix import Pose, Intrinsics


def plucker_embedder(cam_2_world_poses: List[List[Pose]],
                     intrinsics: List[List[Intrinsics]],
                     height: int,
                     width: int,
                     device: torch.device,
                     offset: bool = True,
                     use_rppc: bool = False):
    """
    Parameters
    ----------
        image: [B, V, C, H, W]
        cameras: [B, V, 20]
        normalize: Whether to normalize the cross-product term

    Returns
    -------
        Plucker embedding [B, V, 6, H, W]
    """

    H = height
    W = width
    B = len(cam_2_world_poses)
    V = len(cam_2_world_poses[0])

    # c2w = cameras[:, :, :16]
    # fxfycxcy = cameras[:, :, 16:]
    # c2w = c2w.reshape(b * v, 4, 4)
    c2w = torch.tensor(np.stack([np.stack(cam_2_worlds) for cam_2_worlds in cam_2_world_poses]), dtype=torch.float32, device=device).reshape(B * V, 4, 4)
    fxfycxcy = torch.tensor(np.stack([np.stack(intr) for intr in intrinsics]), dtype=torch.float32, device=device).reshape(B * V, 3, 3)
    fxfycxcy = torch.stack([fxfycxcy[..., 0, 0], fxfycxcy[..., 1, 1], fxfycxcy[..., 0, 2], fxfycxcy[..., 1, 2]], dim=-1).reshape(B*V, 4)
    # fxfycxcy = fxfycxcy.reshape(b * v, 4)

    y, x = torch.meshgrid(torch.arange(H), torch.arange(W), indexing="ij")
    y, x = y.to(device), x.to(device)
    x = x[None, :, :].expand(B*V, -1, -1).reshape(B*V, -1) / (W - 1)
    y = y[None, :, :].expand(B*V, -1, -1).reshape(B*V, -1) / (H - 1)
    if offset:
        x = (x + 0.5 - fxfycxcy[:, 2:3]) / fxfycxcy[:, 0:1]
        y = (y + 0.5 - fxfycxcy[:, 3:4]) / fxfycxcy[:, 1:2]
    else:
        x = (x - fxfycxcy[:, 2:3]) / fxfycxcy[:, 0:1]
        y = (y - fxfycxcy[:, 3:4]) / fxfycxcy[:, 1:2]
    z = torch.ones_like(x)
    ray_d = torch.stack([x, y, z], dim=2)  # [b*v, h*w, 3]
    ray_d = torch.bmm(ray_d, c2w[:, :3, :3].transpose(1, 2))  # [b*v, h*w, 3]
    ray_d = ray_d / torch.norm(ray_d, dim=2, keepdim=True)  # [b*v, h*w, 3]
    ray_o = c2w[:, :3, 3][:, None, :].expand_as(ray_d)  # [b*v, h*w, 3]

    ray_o = ray_o.reshape(B, V, H, W, 3).permute(0, 1, 4, 2, 3)
    ray_d = ray_d.reshape(B, V, H, W, 3).permute(0, 1, 4, 2, 3)
    if use_rppc:
        # r = (o − (o · d)d, d), See DiffusionGS paper
        r_term = ray_o - (ray_o * ray_d).sum(dim=2, keepdim=True) * ray_d
        plucker = torch.cat([r_term, ray_d], dim=2)
    else:
        cross_term = torch.cross(ray_o, ray_d, dim=2)
        plucker = torch.cat([cross_term, ray_d], dim=2)
    return plucker