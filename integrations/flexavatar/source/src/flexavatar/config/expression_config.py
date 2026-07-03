from dataclasses import dataclass
from typing import Literal

import numpy as np
from elias.config import Config

ExpressionCodeType = Literal['flame', 'voodooxp']

@dataclass
class ExpressionCodeConfig(Config):
    expression_code_type: ExpressionCodeType = 'flame'
    use_eyes: bool = True
    use_eyelids: bool = True
    use_jaw: bool = True
    use_neck: bool = True
    use_head_pose: bool = False

    def get_dim(self) -> int:
        dim = 100
        if self.use_eyes:
            dim += 12
        if self.use_eyelids:
            dim += 2
        if self.use_neck:
            dim += 6
        if self.use_jaw:
            dim += 6
        if self.use_head_pose:
            dim += 9
        return dim

    def from_pixel3dmm_tracking(self, tracking) -> np.ndarray:
        expression_code_parts = [tracking['flame']['exp']]
        if self.use_eyes:
            expression_code_parts.append(tracking['flame']['eyes'])
        if self.use_eyelids:
            expression_code_parts.append(tracking['flame']['eyelids'])
        if self.use_neck:
            expression_code_parts.append(tracking['flame']['neck'])
        if self.use_jaw:
            expression_code_parts.append(tracking['flame']['jaw'])
        if self.use_head_pose:
            expression_code_parts.append(tracking['flame']['R'])
            expression_code_parts.append(tracking['flame']['t'])
        expression_code = np.concatenate(expression_code_parts, axis=1)[0]
        return expression_code
