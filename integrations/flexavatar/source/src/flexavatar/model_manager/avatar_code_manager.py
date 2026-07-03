from pathlib import Path

import numpy as np
import torch
from elias.util import ensure_directory_exists_for_file

from flexavatar.env import FLEXAVATAR_AVATAR_CODE_PATH


class AvatarCodeManager:
    def __init__(self, dataset_type: str = 'itw'):
        self._folder = f"{FLEXAVATAR_AVATAR_CODE_PATH}/{dataset_type}"

    def save_avatar_code(self, avatar_code: torch.Tensor, source_person: str):
        avatar_code_path = self.get_avatar_code_path(source_person)
        ensure_directory_exists_for_file(avatar_code_path)
        np.save(avatar_code_path, avatar_code.detach().cpu().numpy())

    def load_avatar_code(self, source_person: str) -> torch.Tensor:
        avatar_code = np.load(self.get_avatar_code_path(source_person))
        return torch.from_numpy(avatar_code).float()

    def has_avatar_code(self, source_person: str) -> bool:
        return Path(self.get_avatar_code_path(source_person)).exists()

    def get_avatar_code_path(self, source_person: str) -> str:
        return f"{self._folder}/avatar_code_{source_person}.npy"
