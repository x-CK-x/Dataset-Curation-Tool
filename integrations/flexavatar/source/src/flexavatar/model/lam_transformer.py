# Copyright (c) 2024-2025, The Alibaba 3DAIGC Team Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from functools import partial
from typing import Any, Dict, Optional

import torch
import torch.nn as nn
from diffusers.models.transformers.transformer_sd3 import SD3SingleTransformerBlock
from diffusers.utils import is_torch_version


class TransformerDecoder(nn.Module):
    """
    Transformer blocks that process the input and optionally use condition and modulation.
    """

    def __init__(self,
                 block_type: str,
                 num_layers: int,
                 num_heads: int,
                 inner_dim: int,
                 cond_dim: int = None,
                 mod_dim: int = None,
                 gradient_checkpointing=False,
                 eps: float = 1e-6,
                 use_dual_attention: bool = False,
                 use_ada_ln: bool = False,
                 transform_keys: bool = False):
        super().__init__()
        self.gradient_checkpointing = gradient_checkpointing
        self.block_type = block_type
        if block_type == "sd3_cond":
            # dual_attention_layers = list(range(num_layers//2))
            dual_attention_layers = []
            self.layers = nn.ModuleList([
                self._block_fn(inner_dim, cond_dim, mod_dim)(
                    num_heads=num_heads,
                    eps=eps,
                    context_pre_only=not transform_keys and i == num_layers - 1,
                    use_dual_attention=use_dual_attention,  # True if i in dual_attention_layers else False,
                    use_ada_ln=use_ada_ln
                )
                for i in range(num_layers)
            ])
        else:
            self.layers = nn.ModuleList([
                self._block_fn(inner_dim, cond_dim, mod_dim)(
                    num_heads=num_heads,
                    eps=eps,
                )
                for _ in range(num_layers)
            ])

        self.norm = nn.LayerNorm(inner_dim, eps=eps)

        if self.block_type in ["cogvideo_cond", "sd3_cond"]:
            self.linear_cond_proj = nn.Linear(cond_dim, inner_dim)

    @property
    def block_type(self):
        return self._block_type

    @block_type.setter
    def block_type(self, block_type):
        assert block_type in ['basic', 'cond', 'mod', 'cond_mod', 'sd3_cond', 'cogvideo_cond'], \
            f"Unsupported block type: {block_type}"
        self._block_type = block_type

    def _block_fn(self, inner_dim, cond_dim, mod_dim):
        assert inner_dim is not None, f"inner_dim must always be specified"
        if self.block_type == 'basic':
            assert cond_dim is None and mod_dim is None, \
                f"Condition and modulation are not supported for BasicBlock"
            from .lam.block import BasicBlock
            # logger.debug(f"Using BasicBlock")
            return partial(BasicBlock, inner_dim=inner_dim)
        elif self.block_type == 'cond':
            assert cond_dim is not None, f"Condition dimension must be specified for ConditionBlock"
            assert mod_dim is None, f"Modulation dimension is not supported for ConditionBlock"
            from .lam.block import ConditionBlock
            # logger.debug(f"Using ConditionBlock")
            return partial(ConditionBlock, inner_dim=inner_dim, cond_dim=cond_dim)
        elif self.block_type == 'mod':
            # logger.error(f"modulation without condition is not implemented")
            raise NotImplementedError(f"modulation without condition is not implemented")
        elif self.block_type == 'cond_mod':
            assert cond_dim is not None and mod_dim is not None, \
                f"Condition and modulation dimensions must be specified for ConditionModulationBlock"
            from .lam.block import ConditionModulationBlock
            # logger.debug(f"Using ConditionModulationBlock")
            return partial(ConditionModulationBlock, inner_dim=inner_dim, cond_dim=cond_dim, mod_dim=mod_dim)
        elif self.block_type == 'cogvideo_cond':
            # logger.debug(f"Using CogVideoXBlock")
            from .lam.transformer_dit import CogVideoXBlock
            # assert inner_dim == cond_dim, f"inner_dim:{inner_dim}, cond_dim:{cond_dim}"
            return partial(CogVideoXBlock, dim=inner_dim, attention_bias=True)
        elif self.block_type == 'sd3_cond':
            # logger.debug(f"Using SD3JointTransformerBlock")
            SD3SingleTransformerBlock
            from flexavatar.model.lam_transformer_dit import SD3JointTransformerBlock
            return partial(SD3JointTransformerBlock, dim=inner_dim, qk_norm="rms_norm")
        else:
            raise ValueError(f"Unsupported block type during runtime: {self.block_type}")

    def assert_runtime_integrity(self, x: torch.Tensor, cond: torch.Tensor, mod: torch.Tensor):
        assert x is not None, f"Input tensor must be specified"
        if self.block_type == 'basic':
            assert cond is None and mod is None, \
                f"Condition and modulation are not supported for BasicBlock"
        elif 'cond' in self.block_type:
            assert cond is not None and mod is None, \
                f"Condition must be specified and modulation is not supported for ConditionBlock"
        elif self.block_type == 'mod':
            raise NotImplementedError(f"modulation without condition is not implemented")
        else:
            assert cond is not None and mod is not None, \
                f"Condition and modulation must be specified for ConditionModulationBlock"

    def forward_layer(self, layer: nn.Module, x: torch.Tensor, cond: torch.Tensor, mod: torch.Tensor):
        if self.block_type == 'basic':
            return layer(x)
        elif self.block_type == 'cond':
            return layer(x, cond)
        elif self.block_type == 'mod':
            return layer(x, mod)
        else:
            return layer(x, cond, mod)

    def forward(self, x: torch.Tensor, keys: torch.Tensor = None, condition: Optional[torch.Tensor] = None, mod: torch.Tensor = None, return_keys: bool = False):
        # assert condition is None, "denoising step condition is not implemented yet. Look into how SD3 does it!"

        # x: [N, L, D]
        # cond: [N, L_cond, D_cond] or None
        # mod: [N, D_mod] or None
        self.assert_runtime_integrity(x, keys, mod)

        if self.block_type in ["cogvideo_cond", "sd3_cond"]:
            # sd3_cond layer has [B, L, D]
            x = x.permute(1, 0, 2)
            if keys is not None:
                keys = keys.permute(1, 0, 2)

            keys = self.linear_cond_proj(keys)
            for layer in self.layers:
                if self.training and self.gradient_checkpointing:
                    def create_custom_forward(module):
                        def custom_forward(*inputs):
                            return module(*inputs)

                        return custom_forward

                    ckpt_kwargs: Dict[str, Any] = {"use_reentrant": False} if is_torch_version(">=", "1.11.0") else {}
                    x, keys = torch.utils.checkpoint.checkpoint(
                        create_custom_forward(layer),
                        x,
                        keys,
                        **ckpt_kwargs,
                    )
                else:
                    x, keys = layer(
                        hidden_states=x,
                        encoder_hidden_states=keys,
                        temb=condition[:, 0] if condition is not None and len(condition.shape) == 3 else condition,  # Note: Here, we are assuming there is only a single condition per batch
                        # image_rotary_emb=None,
                    )
            x = self.norm(x)
            x = x.permute(1, 0, 2)

            if return_keys and keys is not None:
                keys = self.norm(keys)
                keys = keys.permute(1, 0, 2)
        else:
            for layer in self.layers:
                x = self.forward_layer(layer, x, keys, mod)
            x = self.norm(x)

        if return_keys:
            return x, keys
        else:
            return x


