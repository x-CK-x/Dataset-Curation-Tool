import json
import shutil
import os
import onnx
import torch
import timm
import safetensors.torch
import onnxruntime as ort
import numpy as np
from PIL import Image
import torch.nn as nn
import torchvision.transforms as T
import torchvision.transforms.functional as TF
import pandas as pd

from utils import helper_functions as help


# from .model_configs import model_info_map
# from .helper_file import rename_if_exists, etc.

########################################
# Example utility: "Fit" transform like JTP uses
########################################
class FitTransform:
    """
    Re-implements the official JTP "Fit((384,384))" logic using Pillow & transforms.
    If 'pad' is not None, we will pad to the final size. 
    """
    def __init__(self, size, interpolation=T.InterpolationMode.LANCZOS, pad_val=None):
        self.size = size if isinstance(size, tuple) else (size, size)
        self.interpolation = interpolation
        self.pad_val = pad_val

    def __call__(self, img_pil):
        w, h = img_pil.size
        target_h, target_w = self.size

        # scale factor so we fit inside (target_h, target_w)
        scale = min(target_h / h, target_w / w)
        new_h = int(round(h * scale))
        new_w = int(round(w * scale))

        # resize
        img_pil = TF.resize(img_pil, (new_h, new_w), self.interpolation)

        # optionally pad to exact size
        if self.pad_val is not None:
            pad_h = target_h - new_h
            pad_w = target_w - new_w
            top = pad_h // 2
            bottom = pad_h - top
            left = pad_w // 2
            right = pad_w - left
            img_pil = TF.pad(img_pil, (left, top, right, bottom), self.pad_val)
        return img_pil

########################################
# Example utility: "CompositeAlpha"
########################################
class CompositeAlphaTransform:
    """
    If the image has 4 channels, alpha is merged onto a background (0.5).
    If 3 channels, no change.
    """
    def __init__(self, background=0.5, strip_alpha=True):
        # either float -> gray
        # or a 3-tuple -> color
        self.background = background
        self.strip_alpha = strip_alpha

    def __call__(self, tensor):
        # tensor shape: (4, H, W) or (3,H,W)
        if tensor.shape[0] == 3:
            return tensor
        # alpha composite:
        alpha = tensor[3:4, ...]
        rgb = tensor[:3, ...]
        rgb = rgb * alpha + (1.0 - alpha) * self.background
        return rgb

class GatedHead(nn.Module):
    def __init__(self, num_features: int, num_classes: int):
        super().__init__()
        self.num_classes = num_classes
        self.linear = nn.Linear(num_features, num_classes * 2)
        self.act = nn.Sigmoid()
        self.gate = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.linear(x)
        # first half gets act, second half gets gate
        # multiplied
        return self.act(x[:, :self.num_classes]) * self.gate(x[:, self.num_classes:])

###############################
# C) A small wrapper
###############################
class SiglipModelWrapper(nn.Module):
    """
    A wrapper that replicates:
      1) RGBA -> CompositeAlpha -> shape(1,3,384,384)
      2) Then calls the timm model
    """
    def __init__(self, base_model, transform_pipe):
        super().__init__()
        self.transform_pipe = transform_pipe
        self.base_model = base_model

    def forward(self, rgba_image: torch.Tensor) -> torch.Tensor:
        # 1) composite alpha
        rgb = self.transform_pipe(rgba_image)
        # 2) forward in model
        out = self.base_model(rgb)
        return out





def rename_if_exists(folder, old_filename, new_filename):
    old_path = os.path.join(os.getcwd(), folder, old_filename)
    new_path = os.path.join(os.getcwd(), folder, new_filename)
    if os.path.exists(old_path):
        shutil.move(old_path, new_path)
        print(f"Moved {old_path} -> {new_path}")
    else:
        print(f"No model file found at: {old_path}")


# mapping
model_info_map = {
    "Z3D-Convnext":
        {
            "info":
                {
                    "input_dims":
                        (448, 448),
                    "output_layer_size":
                        9525,
                    "onnx_format":
                        True,
                    "model_extension":
                        "onnx",
                    "confidence_threshold":
                        0.2,
                    "use_mean_norm":
                        False,
                    "use_extend_output_dims":
                        False,
                    "tags_csv_format":
                        True,
                    "use_column_number":
                        1,
                    # If you want "tags_file_info" for loading tags, you can do so.
                    # For example:
                    "tags_file_info": {
                        "tags_filename": "tags.csv",  # or "tags.json"
                        "format": "csv",             # if your Z3D model uses a CSV of tags
                        "skip_lines": 0,
                        # "post_load_replacements": {}
                    },
                    "transpose_input": False,  # if needed
                    # ADD new fields:
                    "expected_input_format": "NHWC",    # typically PyTorch-based ONNX uses NCHW
                    "expected_num_channels": 3,         # 3 for RGB
                    "strip_alpha": True                 # if any RGBA is loaded, strip alpha
                },
            "urls":
                [
                    "https://pixeldrain.com/api/file/iNMyyi2w"
                ],
            "pre-process":
                [

                ],
            "post-process":
                [
                    lambda: rename_if_exists("Z3D-Convnext", "Z3D-E621-Convnext.onnx", "model.onnx"),
                    lambda: rename_if_exists("Z3D-Convnext", "tags-selected.csv", "tags.csv"),
                    lambda: shutil.move(os.path.join(os.getcwd(), "Z3D-E621-Convnext"), os.path.join(os.getcwd(), "Z3D-Convnext")),
                    lambda: shutil.move(os.path.join(os.getcwd(), "model.onnx"), os.path.join(os.path.join(os.getcwd(), "Z3D-Convnext"), "model.onnx")),
                    lambda: shutil.move(os.path.join(os.getcwd(), "tags.json"), os.path.join(os.path.join(os.getcwd(), "Z3D-Convnext"), "tags.json"))
                ]
        },
    "eva02-clip-vit-large-7704":
        {
            "info":
                {
                    "input_dims":
                        (224, 224),
                    "output_layer_size":
                        7704,
                    "onnx_format":
                        True,
                    "model_extension":
                        "onnx",
                    "confidence_threshold":
                        0.3,
                    "use_mean_norm":
                        True,
                    "mean_norm":
                        [
                            0.48145466,
                            0.4578275,
                            0.40821073
                        ],
                    "mean_std":
                        [
                            0.26862954,
                            0.26130258,
                            0.27577711
                        ],
                    "use_extend_output_dims":
                        True,
                    "extend_output_dims":
                        [
                            "placeholder0",
                            "placeholder1",
                            "placeholder2"
                        ],
                    "extend_output_dims_pos":
                        [
                            -1, -1, -1
                        ],
                    "tags_csv_format":
                        False,
                    "tags_file_info": {
                        "tags_filename": "tags.json",
                        "format": "json",
                        "skip_lines": 0,
                        # "post_load_replacements": {}
                    },
                    "placeholder_info": {  # New key for placeholder management
                        "tags_format": "version_1",
                        "injection_method": "extend",
                        "placeholders": ["placeholder0", "placeholder1", "placeholder2"]
                    },
                    # New fields:
                    "expected_input_format": "NCHW",
                    "expected_num_channels": 3,
                    "strip_alpha": True,
                    "transpose_input": True,
                },
            "urls":
                [
                    "https://huggingface.co/Thouph/eva02-clip-vit-large-7704/resolve/main/model.onnx",
                    "https://huggingface.co/Thouph/eva02-clip-vit-large-7704/resolve/main/tags.json"
                ],
            "pre-process":
                [
                    lambda: help.create_dirs(os.path.join(os.getcwd(), "eva02-clip-vit-large-7704"))
                ],
            "post-process": 
                [
                    # rename model.onnx into the model folder
                    lambda: rename_if_exists("eva02-clip-vit-large-7704", "model.onnx", "model.onnx"),
                    # rename tags.json into the model folder
                    lambda: rename_if_exists("eva02-clip-vit-large-7704", "tags.json", "tags.json"),
                    lambda: shutil.move(os.path.join(os.getcwd(), "model.onnx"), os.path.join(os.path.join(os.getcwd(), "eva02-clip-vit-large-7704"), "model.onnx")),
                    lambda: shutil.move(os.path.join(os.getcwd(), "tags.json"), os.path.join(os.path.join(os.getcwd(), "eva02-clip-vit-large-7704"), "tags.json"))
                ]

        },
    "eva02-vit-large-448-8046":
        {
            "info":
                {
                    "input_dims":
                        (448, 448),
                    "output_layer_size":
                        8046,
                    "onnx_format":
                        True,
                    "model_extension":
                        "onnx",
                    "confidence_threshold":
                        0.3,
                    "use_mean_norm":
                        True,
                    "mean_norm":
                        [
                            0.48145466,
                            0.4578275,
                            0.40821073
                        ],
                    "mean_std":
                        [
                            0.26862954,
                            0.26130258,
                            0.27577711
                        ],
                    "use_extend_output_dims":
                        True,
                    "extend_output_dims":
                        [
                            "placeholder0",
                            "placeholder1",
                            "explicit",
                            "questionable",
                            "safe"
                        ],
                    "extend_output_dims_pos":
                        [
                            0, -1, -1, -1, -1
                        ],
                    "tags_csv_format":
                        False,
                    # If the tags are "tags_8041.json", you rename it to "tags.json"
                    "tags_file_info": {
                        "tags_filename": "tags.json",
                        "format": "json",
                        "skip_lines": 0,
                        # "post_load_replacements": {}
                    },
                    "placeholder_info": {  # New key for placeholder management
                        "tags_format": "version_1",
                        "injection_method": "insert_and_append",
                        "placeholders": ["placeholder0", "placeholder1", "explicit", "questionable", "safe"],
                        "insert_at": {"placeholder0": 0}  # Position to insert placeholders
                    },
                    # new fields
                    "expected_input_format": "NCHW",
                    "expected_num_channels": 3,
                    "strip_alpha": True,
                    "transpose_input": True,
                },
            "urls":
                [
                    "https://huggingface.co/Thouph/eva02-vit-large-448-8046/resolve/main/model.onnx",
                    "https://huggingface.co/Thouph/eva02-vit-large-448-8046/resolve/main/tags_8041.json"
                ],
            "pre-process":
                [
                    lambda: help.create_dirs(os.path.join(os.getcwd(), "eva02-vit-large-448-8046"))
                ],
            "post-process": 
                [
                    lambda: rename_if_exists("eva02-vit-large-448-8046", "model.onnx", "model.onnx"),
                    lambda: rename_if_exists("eva02-vit-large-448-8046", "tags_8041.json", "tags.json"),
                    lambda: shutil.move(os.path.join(os.getcwd(), "model.onnx"), os.path.join(os.path.join(os.getcwd(), "eva02-vit-large-448-8046"), "model.onnx")),
                    lambda: shutil.move(os.path.join(os.getcwd(), "tags_8041.json"), os.path.join(os.path.join(os.getcwd(), "eva02-vit-large-448-8046"), "tags.json"))
                ]
        },
    "experimental_efficientnetv2_m_8035":
        {
            "info":
                {
                    "input_dims":
                        (448, 448),
                    "output_layer_size":
                        8035,
                    "onnx_format":
                        True,
                    "model_extension":
                        "onnx",
                    "confidence_threshold":
                        0.3,
                    "use_mean_norm":
                        True,
                    "mean_norm":
                        [
                            0.485, 0.456, 0.406
                        ],
                    "mean_std":
                        [
                            0.229, 0.224, 0.225
                        ],
                    "use_extend_output_dims":
                        True,
                    "extend_output_dims":
                        [
                            "placeholder0"
                        ],
                    "extend_output_dims_pos":
                        [
                            -1
                        ],
                    "tags_csv_format":
                        False,
                    "convert_to_onnx_info": {
                        "architecture_type": "efficientnetv2_m",
                        "num_classes": 8035,     # or 8034 plus 1 placeholder
                        "image_size": 448,      # or 224, etc. your code used 512 but scaled?
                        "mean_norm": [0.485, 0.456, 0.406],
                        "std_norm":  [0.229, 0.224, 0.225],
                        # etc. as needed
                    },
                    "tags_file_info": {
                        "tags_filename": "tags.json",
                        "format": "json",
                        "skip_lines": 0,
                        "append_placeholder": "placeholder0",  # note we append "placeholder0"
                        # or post-load transformations
                    },
                    "placeholder_info": {  # New key for placeholder management
                        "tags_format": "version_1",
                        "injection_method": "append_and_sort",
                        "placeholders": ["placeholder0"]
                    },
                    # new fields
                    "expected_input_format": "NCHW",
                    "expected_num_channels": 3,
                    "strip_alpha": True,
                    "transpose_input": True,
                },
            "urls":
                [
                    "https://huggingface.co/Thouph/experimental_efficientnetv2_m_8035/resolve/main/model_balanced.onnx",
                    "https://huggingface.co/Thouph/experimental_efficientnetv2_m_8035/resolve/main/tags_8034.json"
                ],
            "pre-process":
                [
                    lambda: help.create_dirs(os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035"))
                ],
            "post-process": 
                [
                    lambda: rename_if_exists("experimental_efficientnetv2_m_8035", "model_balanced.onnx", "model.onnx"),
                    lambda: rename_if_exists("experimental_efficientnetv2_m_8035", "tags_8034.json", "tags.json"),
                    lambda: shutil.move(os.path.join(os.getcwd(), "model_balanced.onnx"), os.path.join(os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035"), "model.onnx")),
                    lambda: shutil.move(os.path.join(os.getcwd(), "tags_8034.json"), os.path.join(os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035"), "tags.json"))
                    # lambda: convert_to_onnx_if_needed("experimental_efficientnetv2_m_8035")
                ]
        },
    "JTP_PILOT-e4-vit_so400m_patch14_siglip_384": {
        "info": {
            "input_dims": (384, 384),  # update if needed
            "output_layer_size": 4000, # placeholder or actual # of classes
            "onnx_format": False,      # since these are safetensors (PyTorch)
            "model_extension": "safetensors",
            "confidence_threshold": 0.3,
            "use_mean_norm": False,
            "use_extend_output_dims": False,
            "tags_csv_format": False,
            "use_siglip_gated_head": True,  # <--- indicates we must use custom GatedHead logic
            # 1) Tells the post-process we can convert from safetensors → ONNX
            "convert_to_onnx_info": {
                "architecture_type": "vit_so400m_patch14_siglip_384.webli",
                "num_classes": 9083,
                "image_size": 384,
                # Additional code or flags if needed
                # e.g. "use_sigmoid_gate" = True
            },
            # 2) Tells how to parse the tags
            "tags_file_info": {
                # The raw file name we expect
                "tags_filename": "tags.json",
                "format": "json",  # could be "csv" or "json"
                # Do we skip lines?
                "skip_lines": 0,
                # Because you might do something like "replace underscores" in the loaded tags
                # "post_load_replacements": {
                #     "_": " "
                # }
            },
            "placeholder_info": {  # No placeholders for JTP_PILOT models
                "tags_format": "version_2",
                "injection_method": None,
                "placeholders": []
            },
            # new fields
            "expected_input_format": "NCHW",
            "expected_num_channels": 3,
            "strip_alpha": True,
            "transpose_input": True,
        },
        "urls": [
            # 1) The safetensors file
            "https://huggingface.co/spaces/RedRocket/JointTaggerProject-Inference-Beta/resolve/main/JTP_PILOT-e4-vit_so400m_patch14_siglip_384.safetensors",
            # 2) The universal tag file
            "https://huggingface.co/spaces/RedRocket/JointTaggerProject-Inference-Beta/resolve/main/tagger_tags.json"
        ],
        "pre-process": [
            # Create a new subfolder for the model & tags
            lambda: help.create_dirs(os.path.join(os.getcwd(), "JTP_PILOT-e4-vit_so400m_patch14_siglip_384"))
        ],
        "post-process": [
            # Move the safetensors file to model.safetensors
            lambda: rename_if_exists(
                folder="JTP_PILOT-e4-vit_so400m_patch14_siglip_384",
                old_filename="JTP_PILOT-e4-vit_so400m_patch14_siglip_384.safetensors",
                new_filename="model.safetensors"
            ),
            # Move the tagger_tags.json to tags.json
            # (the local filename might appear just as "tagger_tags.json" after download)
            lambda: rename_if_exists(
                folder="JTP_PILOT-e4-vit_so400m_patch14_siglip_384",
                old_filename="tagger_tags.json",
                new_filename="tags.json"
            ),
            lambda: shutil.move(os.path.join(os.getcwd(), "JTP_PILOT-e4-vit_so400m_patch14_siglip_384.safetensors"), os.path.join(os.path.join(os.getcwd(), "JTP_PILOT-e4-vit_so400m_patch14_siglip_384"), "model.safetensors")),
            lambda: shutil.move(os.path.join(os.getcwd(), "tagger_tags.json"), os.path.join(os.path.join(os.getcwd(), "JTP_PILOT-e4-vit_so400m_patch14_siglip_384"), "tags.json")),
            lambda: convert_to_onnx_if_needed("JTP_PILOT-e4-vit_so400m_patch14_siglip_384")
        ]
    },

    "JTP_PILOT2-2-e3-vit_so400m_patch14_siglip_384": {
        "info": {
            "input_dims": (384, 384),
            "output_layer_size": 4000,
            "onnx_format": False,
            "model_extension": "safetensors",
            "confidence_threshold": 0.3,
            "use_mean_norm": False,
            "use_extend_output_dims": False,
            "tags_csv_format": False,
            "use_siglip_gated_head": True,  # <--- indicates we must use custom GatedHead logic
            "convert_to_onnx_info": {
                "architecture_type": "vit_so400m_patch14_siglip_384.webli",
                "num_classes": 9083,
                "image_size": 384,
            },
            "tags_file_info": {
                "tags_filename": "tags.json",
                "format": "json",
                "skip_lines": 0,
                # "post_load_replacements": {
                #     "_": " "
                # }
            },
            "placeholder_info": {  # No placeholders for JTP_PILOT models
                "tags_format": "version_2",
                "injection_method": None,
                "placeholders": []
            },
            # new fields
            "expected_input_format": "NCHW",
            "expected_num_channels": 4,
            "strip_alpha": True,
            "transpose_input": True,
        },
        "urls": [
            "https://huggingface.co/spaces/RedRocket/JointTaggerProject-Inference-Beta/resolve/main/JTP_PILOT2-2-e3-vit_so400m_patch14_siglip_384.safetensors",
            "https://huggingface.co/spaces/RedRocket/JointTaggerProject-Inference-Beta/resolve/main/tagger_tags.json"
        ],
        "pre-process": [
            lambda: help.create_dirs(os.path.join(os.getcwd(), "JTP_PILOT2-2-e3-vit_so400m_patch14_siglip_384"))
        ],
        "post-process": [
            lambda: rename_if_exists(
                "JTP_PILOT2-2-e3-vit_so400m_patch14_siglip_384",
                "JTP_PILOT2-2-e3-vit_so400m_patch14_siglip_384.safetensors",
                "model.safetensors"
            ),
            lambda: rename_if_exists(
                "JTP_PILOT2-2-e3-vit_so400m_patch14_siglip_384",
                "tagger_tags.json",
                "tags.json"
            ),
            lambda: shutil.move(os.path.join(os.getcwd(), "JTP_PILOT2-2-e3-vit_so400m_patch14_siglip_384.safetensors"), os.path.join(os.path.join(os.getcwd(), "JTP_PILOT2-2-e3-vit_so400m_patch14_siglip_384"), "model.safetensors")),
            lambda: shutil.move(os.path.join(os.getcwd(), "tagger_tags.json"), os.path.join(os.path.join(os.getcwd(), "JTP_PILOT2-2-e3-vit_so400m_patch14_siglip_384"), "tags.json")),
            lambda: convert_siglip_model_to_onnx("JTP_PILOT2-2-e3-vit_so400m_patch14_siglip_384")
        ]
    },

    "JTP_PILOT2-e3-vit_so400m_patch14_siglip_384": {
        "info": {
            "input_dims": (384, 384),
            "output_layer_size": 4000,
            "onnx_format": False,
            "model_extension": "safetensors",
            "confidence_threshold": 0.3,
            "use_mean_norm": False,
            "use_extend_output_dims": False,
            "tags_csv_format": False,
            "use_siglip_gated_head": True,  # <--- indicates we must use custom GatedHead logic
            "convert_to_onnx_info": {
                "architecture_type": "vit_so400m_patch14_siglip_384.webli",
                "num_classes": 9083,
                "image_size": 384
            },
            "tags_file_info": {
                "tags_filename": "tags.json",
                "format": "json",
                "skip_lines": 0,
                # "post_load_replacements": {
                #     "_": " "
                # }
            },
            "placeholder_info": {  # No placeholders for JTP_PILOT models
                "tags_format": "version_2",
                "injection_method": None,
                "placeholders": []
            },
            # new fields
            "expected_input_format": "NCHW",
            "expected_num_channels": 4,
            "strip_alpha": True,
            "transpose_input": True,
        },
        "urls": [
            "https://huggingface.co/spaces/RedRocket/JointTaggerProject-Inference-Beta/resolve/main/JTP_PILOT2-e3-vit_so400m_patch14_siglip_384.safetensors",
            "https://huggingface.co/spaces/RedRocket/JointTaggerProject-Inference-Beta/resolve/main/tagger_tags.json"
        ],
        "pre-process": [
            lambda: help.create_dirs(os.path.join(os.getcwd(), "JTP_PILOT2-e3-vit_so400m_patch14_siglip_384"))
        ],
        "post-process": [
            lambda: rename_if_exists(
                "JTP_PILOT2-e3-vit_so400m_patch14_siglip_384",
                "JTP_PILOT2-e3-vit_so400m_patch14_siglip_384.safetensors",
                "model.safetensors"
            ),
            lambda: rename_if_exists(
                "JTP_PILOT2-e3-vit_so400m_patch14_siglip_384",
                "tagger_tags.json",
                "tags.json"
            ),
            lambda: shutil.move(os.path.join(os.getcwd(), "JTP_PILOT2-e3-vit_so400m_patch14_siglip_384.safetensors"), os.path.join(os.path.join(os.getcwd(), "JTP_PILOT2-e3-vit_so400m_patch14_siglip_384"), "model.safetensors")),
            lambda: shutil.move(os.path.join(os.getcwd(), "tagger_tags.json"), os.path.join(os.path.join(os.getcwd(), "JTP_PILOT2-e3-vit_so400m_patch14_siglip_384"), "tags.json")),
            lambda: convert_siglip_model_to_onnx("JTP_PILOT2-e3-vit_so400m_patch14_siglip_384")
        ]
    },
}

def download_caption_model(model_selection: str):
    help.verbose_print(f"DOWNLOADING asset:\t{model_info_map[model_selection]}")
    # pre-process
    for pre_op in model_info_map[model_selection]["pre-process"]:
        pre_op()
    # urls
    for url in model_info_map[model_selection]["urls"]:
        help.download_url(url, url.split('/')[-1])
    # post-process
    for post_op in model_info_map[model_selection]["post-process"]:
        post_op()  # call the function

    # finally unzip the file
    help.unzip_all()
    help.delete_all_archives()
    help.verbose_print("Done")

###############################
#  B) Conversion to ONNX method
###############################

def convert_siglip_model_to_onnx(model_key: str):
    info = model_info_map[model_key]["info"]
    folder = model_key # is the name of the folder
    safetensors_path = os.path.join(folder, "model.safetensors")

    # 1) Build the model in code
    #    The original inference code:
    arch_type = info["convert_to_onnx_info"]["architecture_type"]
    num_classes = info["convert_to_onnx_info"]["num_classes"]
    model = timm.create_model(
        arch_type,
        pretrained=False,
        num_classes=num_classes
    )
    # override the final head with GatedHead
    # the original code used: GatedHead(min(model.head.weight.shape), 9083)
    # so let's do:
    model.head = GatedHead(min(model.head.weight.shape), num_classes)

    # 2) Load the safetensors
    safetensors.torch.load_model(model, safetensors_path)
    model.eval()

    # 3) Create a small "wrapper" that includes alpha composite
    #    so that the ONNX input can be RGBA and we replicate the code
    #    but typically ONNX won't do dynamic resizing well; we'll assume (1,4,384,384).
    transform_pipeline = nn.Sequential(
        CompositeAlpha(0.5),  # merges alpha
        # optionally a center crop or something
    )
    # We'll define a "full" model that runs transform + forward pass
    full_model = SiglipModelWrapper(model, transform_pipeline)
    full_model.eval()

    # 4) Export to ONNX
    # Dummy input shape (1,4,384,384) for RGBA
    dummy_input = torch.randn(1, 4, 384, 384, dtype=torch.float32)
    onnx_path = os.path.join(folder, "model.onnx")

    torch.onnx.export(
        full_model,
        dummy_input,
        onnx_path,
        export_params=True,
        opset_version=16,
        do_constant_folding=True,
        input_names=["rgba_image"],
        output_names=["probits"]
    )

    print(f"[{model_key}] Successfully created ONNX at: {onnx_path}")

def convert_to_onnx_if_needed(model_key: str):
    """
    If a model is in .pth or .safetensors format,
    we load it via PyTorch, then export to ONNX if the user wants it.
    We rely on 'convert_to_onnx_info' in the config for creation logic.
    """
    info = model_info_map[model_key]["info"]
    folder_name = model_key # is the name of the folder
    extension = info["model_extension"]
    if extension == "onnx":
        print(f"[{model_key}] Already ONNX format. Skipping conversion.")
        return

    # The instructions for how to create the model
    convert_info = info["convert_to_onnx_info"]
    arch_type = convert_info.get("architecture_type", None)
    num_classes = convert_info.get("num_classes", None)
    image_size = convert_info.get("image_size", 384)

    # 1) Build or load the PyTorch model
    if extension == "safetensors":
        # example: timm-based approach
        # (If your code is different, adapt accordingly)
        model = timm.create_model(
            arch_type,
            pretrained=False,
            num_classes=num_classes
        )
        # Suppose we have a special gating head, etc. in your code
        # Then load the safetensors:
        safetensors_file = os.path.join(folder_name, f"model.{extension}")
        safetensors.torch.load_model(model, safetensors_file)
        model.eval()

    elif extension == "pth":
        # For the pth file, e.g. "experimental_efficientnetv2_m_8035"
        model_file = os.path.join(folder_name, f"model.{extension}")
        model = torch.load(model_file, map_location="cpu")  # you might need a custom load
        model.eval()
    else:
        print(f"[{model_key}] Unknown extension: {extension}")
        return

    # 2) Export to ONNX
    # Create a dummy input
    dummy_input = torch.randn(1, 3, image_size, image_size, device="cpu")
    onnx_path = os.path.join(folder_name, "model.onnx")
    # adapt opset_version to your needs
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        export_params=True,
        opset_version=16,
        do_constant_folding=True
    )
    print(f"[{model_key}] Conversion to ONNX done! -> {onnx_path}")



def preprocess_image_pil(img_path: str, model_key: str) -> np.ndarray:
    """
    Preprocesses an image for inference based on the model's configuration.

    Args:
        img_path (str): Path to the input image.
        model_key (str): The key identifying the model in model_info_map.

    Returns:
        np.ndarray: Preprocessed image array ready for model input.
    """
    info = model_info_map[model_key]["info"]
    target_size = info.get("input_dims", (384, 384))
    mean_val = np.array(info.get("mean_norm", [0.5, 0.5, 0.5]), dtype=np.float32)
    std_val = np.array(info.get("mean_std", [0.5, 0.5, 0.5]), dtype=np.float32)

    img = Image.open(img_path).convert("RGB")
    img = img.resize(target_size, Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0

    arr = (arr - mean_val) / std_val
    arr = arr.transpose(2, 0, 1)
    return arr[np.newaxis, ...]  # shape (1,3,H,W)

def load_tags_for_model(model_key: str) -> pd.DataFrame:
    """
    Loads and parses tags for a given model based on its configuration in model_info_map.

    Args:
        model_key (str): The key identifying the model in model_info_map. This can be the model's
                         directory name or model_name.

    Returns:
        pd.DataFrame: A DataFrame containing the tags with columns ['id', 'name', 'category', 'post_count'].
    """
    info = model_info_map[model_key]["info"]
    tags_info = info.get("tags_file_info", {})
    placeholder_info = info.get("placeholder_info", {})
    folder_name = model_key  # Assuming the folder name matches the model_key

    tags_file = os.path.join(folder_name, tags_info.get("tags_filename", "tags.json"))
    format_type = tags_info.get("format", "json")
    skip_lines = tags_info.get("skip_lines", 0)
    replacements = tags_info.get("post_load_replacements", {})
    append_placeholder = tags_info.get("append_placeholder", None)

    processed_tags = []

    try:
        if format_type == "json":
            with open(tags_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                # Handle Version 1: List of strings with "id_name" format
                for idx, item in enumerate(data):
                    processed_tags.append({
                        'index': idx,
                        'name': item
                    })
            elif isinstance(data, dict):
                # Handle Version 2: Dictionary of name: id
                for name, tag_id in data.items():
                    processed_tags.append({
                        'index': tag_id,
                        'name': name
                    })
            else:
                raise ValueError("Unsupported JSON structure for tags.")

        elif format_type == "csv":
            # Handle CSV format
            df = pd.read_csv(tags_file, skiprows=skip_lines)
            required_columns = {'id', 'name'}
            if not required_columns.issubset(df.columns):
                missing = required_columns - set(df.columns)
                raise ValueError(f"CSV tags file is missing required columns: {missing}")

            counter = 0
            for _, row in df.iterrows():
                tag_id = row['id']
                name = row['name']

                processed_tags.append({
                    'index': counter,
                    'name': name
                })
                counter += 1

        else:
            raise ValueError(f"Unsupported tag format: {format_type}")

        # Handle placeholder injections based on configuration
        if placeholder_info.get("injection_method") and placeholder_info.get("placeholders"):
            placeholders = placeholder_info.get("placeholders", [])
            injection_method = placeholder_info.get("injection_method")

            if injection_method == "append_and_sort":
                # Append placeholders and sort
                for placeholder in placeholders:
                    processed_tags.append({
                        'index': len(processed_tags),  # Assign next available ID
                        'name': placeholder
                    })
                # Sort tags by name
                processed_tags = sorted(processed_tags, key=lambda x: x['name'])

            elif injection_method == "insert_and_append":
                # Insert placeholders at specific positions and append others
                insert_at = placeholder_info.get("insert_at", None)
                if insert_at is not None:
                    for idx, placeholder in enumerate(placeholders):
                        if placeholder in insert_at:
                            processed_tags.insert(insert_at[placeholder], {
                                'index': insert_at[placeholder],
                                'name': placeholder
                            })
                        else:
                            processed_tags.append({
                                'index': len(processed_tags),
                                'name': placeholder
                            })

            elif injection_method == "extend":
                # Extend the list with placeholders
                for placeholder in placeholders:
                    processed_tags.append({
                        'index': len(processed_tags),
                        'name': placeholder
                    })
            else:
                raise ValueError(f"Unsupported injection method: {injection_method}")

        # Convert to DataFrame for consistency
        df_tags = pd.DataFrame(processed_tags)

        # Ensure consistent data types
        df_tags = df_tags.astype({
            'index': 'int64',
            'name': 'object'
        })

        # Validate DataFrame integrity
        expected_columns = {'index', 'name'}
        if not expected_columns.issubset(df_tags.columns):
            missing = expected_columns - set(df_tags.columns)
            raise ValueError(f"Loaded tags DataFrame is missing columns: {missing}")

        # Verify that IDs are unique
        if not df_tags['name'].is_unique:
            duplicate_ids = df_tags['name'][df_tags['name'].duplicated()].unique()
            raise ValueError(f"Duplicate tag IDs found: {duplicate_ids}")

        return df_tags
    
    except FileNotFoundError:
        raise FileNotFoundError(f"Tags file not found: {tags_file}")
    except json.JSONDecodeError:
        raise ValueError(f"Error decoding JSON from tags file: {tags_file}")
    except pd.errors.EmptyDataError:
        raise ValueError(f"Tags CSV file is empty or malformed: {tags_file}")
    except Exception as e:
        raise RuntimeError(f"An error occurred while loading tags for model '{model_key}': {e}")

def run_inference_onnx(
    model_key: str,
    image_paths: list[str] | str,
    use_gpu: bool = False,
    threshold: float = 0.3
):
    """
    Runs ONNX inference on single or multiple images.
    - If one image is provided, returns ALL predictions (tag -> score).
    - If multiple images are provided, applies a threshold and returns only the tags above it.
    - 'use_gpu=True' attempts the CUDA execution provider. If not installed or fails,
      falls back to CPU.
    - 'threshold' is used only in batch mode.
    """
    # 1) Model config
    info = model_info_map[model_key]["info"]
    folder = model_key  # Assuming the folder name matches the model_key
    model_path = os.path.join(folder, "model.onnx")

    input_dims = info.get("input_dims", (384, 384))
    output_layer_size = info.get("output_layer_size", 9083)

    # 2) Create an ONNXRuntime session (CPU or GPU)
    providers = ["CPUExecutionProvider"]
    if use_gpu:
        # Attempt GPU if onnxruntime-gpu is installed
        try:
            if 'CUDAExecutionProvider' in ort.get_available_providers():
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            else:
                print("CUDAExecutionProvider not available. Using CPU.")
        except Exception as e:
            print(f"Failed to set GPU provider: {e}. Falling back to CPU.")

    session = ort.InferenceSession(model_path, providers=providers)

    # 3) Load tags
    df_tags = load_tags_for_model(model_key)
    # Sort tags by 'index' to align with y_pred_args indices
    df_tags_sorted = df_tags.sort_values('index').reset_index(drop=True)
    tags_list = df_tags_sorted['name'].tolist()
    if len(tags_list) < output_layer_size:
        print(
            f"Warning: tags_list has {len(tags_list)} tags, "
            f"but output_layer_size={output_layer_size}"
        )

    # 4) Convert single path to list
    single_image = False
    if isinstance(image_paths, str):
        image_paths = [image_paths]
        single_image = True
    elif len(image_paths) == 1:
        single_image = True

    # 5) Preprocess each image
    batch_arrays = []
    for path in image_paths:
        arr = preprocess_image_pil(path, model_key)  # Ensure preprocess_image_pil uses model_key
        batch_arrays.append(arr)
    # Combine into shape (B, 3, H, W)
    input_array = np.concatenate(batch_arrays, axis=0).astype(np.float32)

    # 6) ONNX input/output
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    # 7) Run inference
    outputs = session.run([output_name], {input_name: input_array})[0]
    # outputs shape: (B, output_layer_size)

    results = []
    for i, row in enumerate(outputs):
        # Apply Sigmoid if model outputs raw logits
        row_sigmoid = 1.0 / (1.0 + np.exp(-row))

        if single_image:
            # Return ALL tags with their probabilities
            all_tags = []
            for idx, score in enumerate(row_sigmoid):
                if idx < len(tags_list):
                    all_tags.append((tags_list[idx], float(score)))
                else:
                    # Handle mismatch by assigning 'Unknown'
                    all_tags.append((f"Unknown_{idx}", float(score)))

            # Sort descending by score
            all_tags.sort(key=lambda x: x[1], reverse=True)
            results.append({
                "image_path": image_paths[i],
                "predictions": all_tags  # All tags
            })
        else:
            # Batch mode: apply threshold
            indices = np.where(row_sigmoid > threshold)[0]
            predicted_tags = []
            for idx in indices:
                tag_name = tags_list[idx] if idx < len(tags_list) else f"Unknown_{idx}"
                predicted_tags.append((tag_name, float(row_sigmoid[idx])))

            # Sort descending by score
            predicted_tags.sort(key=lambda x: x[1], reverse=True)
            results.append({
                "image_path": image_paths[i],
                "predictions": predicted_tags
            })

    return results

def get_model_key(model_identifier: str) -> str:
    """
    Determines the model key based on the provided identifier, which can be a directory path or model name.

    Args:
        model_identifier (str): The directory path containing the model.onnx or the model name.

    Returns:
        str: The model key corresponding to the model_info_map.
    """
    if os.path.isdir(model_identifier):
        return os.path.basename(os.path.normpath(model_identifier))
    else:
        # Assume it's a model name
        return model_identifier

########################################
# The main function
########################################

def apply_official_preprocess(pil_image, model_key):########### try the pil_image edits here for the two models that have dims == 4
    """
    Creates a pipeline that matches the official code for each model_key.

    Returns a NumPy array shaped (C,H,W) in float32
    (or (4,H,W) if your model truly wants RGBA).
    """

    temp_arr = np.array(pil_image)
    print("Before tensor to NumPy:", temp_arr.shape)

    from utils.features.captioning.model_configs import tag_model_config as mc
    info = mc.model_info_map[model_key]["info"]

    # Decide which official pipeline to do, based on the “official code”
    if "JTP_PILOT" in model_key:
        # The official code for JTP does:
        # 1) Convert RGBA
        # 2) Fit(384,384)
        # 3) toTensor()
        # 4) CompositeAlpha(0.5)
        # 5) Normalize( mean=0.5, std=0.5 )
        # 6) CenterCrop(384,384)
        # then shape => (3,384,384).
        # 
        # But if your ONNX wants 4 channels, you skip composite. 
        # Here is the official pipeline version that merges alpha:
        if "-e4-" in model_key:
            background_val = 0.5  # from official code
            transform_jtp = T.Compose([
                T.Lambda(lambda im: im.convert("RGB")),  # ensure RGBA
                FitTransform((384, 384), interpolation=T.InterpolationMode.LANCZOS, pad_val=None),  # same logic
                T.ToTensor(),  # => shape(4,H,W) in [0..1]
                T.Lambda(lambda t: CompositeAlphaTransform(background_val, True)(t)),  # merges alpha => shape(3,H,W)
                T.Normalize(mean=[0.5,0.5,0.5], std=[0.5,0.5,0.5]),
                T.CenterCrop((384, 384))  # final shape => (3,384,384)
            ])
            tensor = transform_jtp(pil_image)  # shape(3,384,384)
            arr = tensor.cpu().numpy().astype(np.float32)
            print("-E4- models After tensor to NumPy:", arr.shape)

            return arr  # (3,384,384)
        else: # both the e3 models
            background_val = 0.5  # from official code
            transform_jtp = T.Compose([
                T.Lambda(lambda im: im.convert("RGBA")),  # ensure RGBA
                FitTransform((384, 384), interpolation=T.InterpolationMode.LANCZOS, pad_val=None),  # same logic
                T.ToTensor(),  # => shape(4,H,W) in [0..1]
                T.Lambda(lambda t: CompositeAlphaTransform(background_val, False)(t)),  # merges alpha => shape(4,H,W)
                T.Normalize(mean=[0.5,0.5,0.5], std=[0.5,0.5,0.5]),
                T.CenterCrop((384, 384))  # final shape => (3,384,384)
            ])
            tensor = transform_jtp(pil_image)  # shape(3,384,384)
            arr = tensor.cpu().numpy().astype(np.float32)
            print("-E3- models After tensor to NumPy:", arr.shape)

            return arr  # (3,384,384)
        """
        if mc.model_info_map[model_key]["info"]["expected_num_channels"] == 4:########################## they are not batches here so EXPECT ISSUES BECAUSE IT'S JUST ONE IMAGE AT A TIME BEING PROCESSED IN THIS FUNCTION!!!!!!!!
            alpha_channel = np.ones((pil_image.shape[0], 1, pil_image.shape[2], pil_image.shape[3]),
                        dtype=pil_image.dtype)
            # Concatenate the alpha channel to the original array along the channel axis
            pil_image = np.concatenate([pil_image, alpha_channel], axis=1)
        """

    elif model_key == "eva02-clip-vit-large-7704":
        # official code:
        # 1) Resize(224,224) => toTensor => Normalize( mean=..., std=... )
        transform_eva02_224 = T.Compose([
            T.Resize((224,224), interpolation=T.InterpolationMode.BICUBIC),
            T.ToTensor(),
            T.Normalize(mean=[0.48145466, 0.4578275, 0.40821073],
                        std=[0.26862954, 0.26130258, 0.27577711])
        ])
        tensor = transform_eva02_224(pil_image.convert("RGB"))################################################
        arr = tensor.cpu().numpy().astype(np.float32)
        print("After tensor to NumPy:", arr.shape)

        return arr  # shape(3,224,224)

    elif model_key == "eva02-vit-large-448-8046":
        # official code:
        # 1) Resize(448,448) => toTensor => Normalize( same mean/std ) => shape(3,448,448)
        transform_eva02_448 = T.Compose([
            T.Resize((448,448), interpolation=T.InterpolationMode.BICUBIC),
            T.ToTensor(),
            T.Normalize(mean=[0.48145466, 0.4578275, 0.40821073],
                        std=[0.26862954, 0.26130258, 0.27577711])
        ])
        tensor = transform_eva02_448(pil_image.convert("RGB"))
        arr = tensor.cpu().numpy().astype(np.float32)
        print("After tensor to NumPy:", arr.shape)

        return arr

    elif model_key == "experimental_efficientnetv2_m_8035":
        # official code:
        # basically => .ToTensor, .Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])
        # plus some fancy resizing. But you had:
        #   "img.thumbnail(...)"
        # We can approximate with a standard T.Resize to (448,448).
        transform_eff = T.Compose([
            T.ToTensor(),
            T.Normalize(mean=[0.485,0.456,0.406],
                        std=[0.229,0.224,0.225])
        ])
        # or do your custom "thumbnail" code here if you want to replicate exactly
        # e.g. compute aspect ratio, do some sqrt logic, etc.
        # for simplicity:
        pil_image = pil_image.convert("RGB")
        # do "pil_image.thumbnail((448,448))" or a standard "resize"
        pil_image = T.Resize((448,448))(pil_image)
        tensor = transform_eff(pil_image)
        arr = tensor.cpu().numpy().astype(np.float32)
        print("After tensor to NumPy:", arr.shape)

        return arr
    elif model_key == "Z3D-Convnext":
        # fallback if not recognized:
        # maybe do a simple "Resize((224,224)) => ToTensor()"?
        # or read from config["input_dims"], config["use_mean_norm"], etc.
        size = info.get("input_dims", (448,448))
        use_mean_norm = info.get("use_mean_norm", False)
        mean = info.get("mean_norm", [0.5, 0.5, 0.5])
        std = info.get("mean_std", [0.5, 0.5, 0.5])
        transform_fallback = [T.Resize(size)]
        transform_fallback.append(T.ToTensor())
        if use_mean_norm:
            transform_fallback.append(T.Normalize(mean=mean, std=std))
        pipeline = T.Compose(transform_fallback)
        tensor = pipeline(pil_image.convert("RGB"))
        # tensor = tensor.permute(0, 2, 3, 1)
        arr = tensor.cpu().numpy().astype(np.float32)
        # tensor = np.transpose(tensor, (0, 2, 3, 1))
        print("After tensor to NumPy:", arr.shape)

        return arr
    else:
        # fallback if not recognized:
        # maybe do a simple "Resize((224,224)) => ToTensor()"?
        # or read from config["input_dims"], config["use_mean_norm"], etc.
        size = info.get("input_dims", (224,224))
        use_mean_norm = info.get("use_mean_norm", False)
        mean = info.get("mean_norm", [0.5, 0.5, 0.5])
        std = info.get("mean_std", [0.5, 0.5, 0.5])
        transform_fallback = [T.Resize(size)]
        transform_fallback.append(T.ToTensor())
        if use_mean_norm:
            transform_fallback.append(T.Normalize(mean=mean, std=std))
        pipeline = T.Compose(transform_fallback)
        tensor = pipeline(pil_image.convert("RGB"))
        arr = tensor.cpu().numpy().astype(np.float32)
        print("After tensor to NumPy:", arr.shape)

        return arr
    


    
