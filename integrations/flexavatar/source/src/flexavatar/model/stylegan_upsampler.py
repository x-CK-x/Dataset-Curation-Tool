from dataclasses import dataclass
from typing import Optional

import numpy as np
import torch
from elias.config import Config
from stylegan_generators.stylegan2 import SynthesisBlock
from torch import nn

from flexavatar.model.stylegan_pixelshuffle import PixelShuffleSynthesisBlock


@dataclass
class StyleGANUpsamplerConfig(Config):
    input_res: int
    output_res: int
    input_channels: int
    output_channels: int
    channel_base: int = 32768
    channel_max: int = 512
    w_dim: int = 512
    use_noise: bool = True
    initialize_with_image: bool = False


class StyleGANUpsampler(nn.Module):
    def __init__(self, config: StyleGANUpsamplerConfig):
        super().__init__()

        self._config = config

        img_resolution_log2_start = int(np.log2(config.input_res)) + 1
        img_resolution_log2 = int(np.log2(config.output_res))
        self.block_resolutions = [2 ** i for i in range(img_resolution_log2_start, img_resolution_log2 + 1)]
        channels_dict = {res: min(config.channel_base // res, config.channel_max) for res in self.block_resolutions}
        channels_dict[config.input_res] = config.input_channels

        self.blocks = []
        for res in self.block_resolutions:
            in_channels = channels_dict[res // 2]
            out_channels = channels_dict[res]
            is_last = (res == config.output_res)
            block = SynthesisBlock(in_channels, out_channels, w_dim=config.w_dim, resolution=res,
                                   img_channels=config.output_channels, is_last=is_last,
                                   use_noise=config.use_noise)

            self.blocks.append(block)

        self.blocks = nn.ModuleList(self.blocks)

    def forward(self,
                x: torch.Tensor,
                ws: Optional[torch.Tensor] = None,
                force_fp32: bool = False,
                fused_modconv: bool = None,
                update_emas: bool = False,
                noise_mode: str = 'random',
                gain: float = 1) -> torch.Tensor:
        if ws is None:
            ws = torch.zeros((x.shape[0], self._config.w_dim), dtype=torch.float32, device=x.device)

        all_ws = []
        for block in self.blocks:
            all_ws.append(ws[:, None].repeat(1, block.num_conv + block.num_torgb, 1))  # TODO: ws are always 0!

        if self._config.initialize_with_image:
            img = x
        else:
            img = None

        for block, cur_ws in zip(self.blocks, all_ws):
            x, img = block(x, img, cur_ws,
                           force_fp32=force_fp32,
                           fused_modconv=fused_modconv,
                           update_emas=update_emas,
                           noise_mode=noise_mode,
                           gain=gain)

        return img


class StyleGANPixelShuffleUpsampler(nn.Module):
    def __init__(self, config: StyleGANUpsamplerConfig):
        super().__init__()

        self._config = config

        img_resolution_log2_start = int(np.log2(config.input_res)) + 1
        img_resolution_log2 = int(np.log2(config.output_res))
        self.block_resolutions = [2 ** i for i in range(img_resolution_log2_start, img_resolution_log2 + 1)]
        channels_dict = {res: min(config.channel_base // res, config.channel_max) for res in self.block_resolutions}
        channels_dict[config.input_res] = config.input_channels

        img_channels = channels_dict[self.block_resolutions[0] // 2]
        self.blocks = []
        for res in self.block_resolutions:
            in_channels = channels_dict[res // 2]
            out_channels = channels_dict[res]
            assert img_channels % 4 == 0, f"img_channels {img_channels} is not divisible by 4"
            img_channels = img_channels // 4

            is_last = (res == config.output_res)
            block = PixelShuffleSynthesisBlock(in_channels, out_channels, img_channels, w_dim=config.w_dim, resolution=res,
                                               is_last=is_last,
                                               use_noise=config.use_noise)

            self.blocks.append(block)


        self.blocks = nn.ModuleList(self.blocks)

    def forward(self,
                x: torch.Tensor,
                ws: Optional[torch.Tensor] = None,
                force_fp32: bool = False,
                fused_modconv: bool = None,
                update_emas: bool = False,
                noise_mode: str = 'random',
                gain: float = 1) -> torch.Tensor:
        if ws is None:
            ws = torch.zeros((x.shape[0], self._config.w_dim), dtype=torch.float32, device=x.device)

        all_ws = []
        for block in self.blocks:
            all_ws.append(ws[:, None].repeat(1, block.num_conv + block.num_torgb, 1))  # TODO: ws are always 0!

        if self._config.initialize_with_image:
            img = x
        else:
            img = None

        for block, cur_ws in zip(self.blocks, all_ws):
            x, img = block(x, img, cur_ws,
                           force_fp32=force_fp32,
                           fused_modconv=fused_modconv,
                           update_emas=update_emas,
                           noise_mode=noise_mode,
                           gain=gain)

        return img
