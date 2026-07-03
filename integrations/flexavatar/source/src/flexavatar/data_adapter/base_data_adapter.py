from abc import ABC, abstractmethod
from dataclasses import replace
from typing import Tuple, List, Union, Dict

import numpy as np
from dreifus.camera import PoseType
from dreifus.matrix import Pose, Intrinsics
from dreifus.vector import Vec3
from tqdm.contrib.concurrent import thread_map

from flexavatar.config.dataset_config import SampleMetadata


class BaseDataAdapter(ABC):

    @abstractmethod
    def load_image(self, sample_metadata: SampleMetadata) -> np.ndarray:
        pass

    @abstractmethod
    def load_mask(self, sample_metadata: SampleMetadata) -> np.ndarray:
        pass

    @abstractmethod
    def load_head_pose(self, sample_metadata: SampleMetadata) -> Tuple[Pose, float]:
        pass

    @abstractmethod
    def load_camera_params(self, sample_metadata: SampleMetadata) -> Tuple[Pose, Intrinsics]:
        pass

    @abstractmethod
    def load_expression_code(self, sample_metadata: SampleMetadata) -> np.ndarray:
        pass

    @abstractmethod
    def list_cameras(self, sample_metadata: SampleMetadata) -> List[Union[str, int]]:
        pass

    @abstractmethod
    def list_cameras_left(self, sample_metadata: SampleMetadata) -> List[Union[str, int]]:
        pass

    @abstractmethod
    def list_cameras_right(self, sample_metadata: SampleMetadata) -> List[Union[str, int]]:
        pass

    @abstractmethod
    def list_cameras_eval(self, sample_metadata: SampleMetadata)-> List[Union[str, int]]:
        pass

    def list_back_head_cameras(self) -> List[str]:
        return []

    @abstractmethod
    def list_timesteps(self, sample_metadata: SampleMetadata) -> List[int]:
        pass

    @abstractmethod
    def apply_color_correction(self, image: np.ndarray, camera: Union[str, int]) -> np.ndarray:
        pass

    def get_closest_camera(self, sample_metadata: SampleMetadata, cam_position: Vec3) -> Tuple[Union[str, int], Pose, Intrinsics]:
        cameras = self.list_cameras(sample_metadata)
        model_to_world_no_scale, head_scale = self.load_head_pose(sample_metadata)

        def _load_cameras(camera):
            sample_metadata_camera = replace(sample_metadata, serial=camera)
            pose, intrinsics = self.load_camera_params(sample_metadata_camera)
            pose = Pose(
                model_to_world_no_scale.invert().numpy() @ pose,
                pose_type=PoseType.CAM_2_WORLD)
            pose.set_translation(head_scale * pose.get_translation())

            return pose, intrinsics

        poses_and_intrinsics = thread_map(_load_cameras, cameras)
        all_poses, all_intrinsics = zip(*poses_and_intrinsics)

        # for camera in cameras:
        #     sample_metadata_camera = replace(sample_metadata, serial=camera)
        #     pose, intrinsics = self.load_camera_params(sample_metadata_camera)
        #     pose = Pose(
        #         model_to_world_no_scale.invert().numpy() @ pose,
        #         pose_type=PoseType.CAM_2_WORLD)
        #     pose.set_translation(head_scale * pose.get_translation())
        #
        #     all_poses.append(pose)
        #     all_intrinsics.append(intrinsics)

        camera_positions = np.stack([pose.get_translation() for pose in all_poses])
        closest_idx = np.argmin(np.linalg.norm(cam_position[None] - camera_positions, axis=1))
        closest_camera = cameras[closest_idx]
        closest_pose = all_poses[closest_idx]
        closest_intrinsics = all_intrinsics[closest_idx]

        return closest_camera, closest_pose, closest_intrinsics
