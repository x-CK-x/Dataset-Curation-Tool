import json
import shutil
import os
import onnx
import torch
import timm
import safetensors.torch
from torchvision.transforms import functional as F
import onnxruntime as ort
import numpy as np
from PIL import Image
import torch.nn as nn
from torchvision.transforms import functional as TF

from utils import helper_functions as help


# from .model_configs import model_info_map
# from .helper_file import rename_if_exists, etc.

#########################
#  A) Original custom ops
#########################

class Fit(nn.Module):
    def __init__(self, bounds=(384,384), interpolation=TF.InterpolationMode.LANCZOS, grow=True, pad=None):
        super().__init__()
        self.bounds = (bounds, bounds) if isinstance(bounds, int) else bounds
        self.interpolation = interpolation
        self.grow = grow
        self.pad = pad

    def forward(self, img: torch.Tensor) -> torch.Tensor:
        # This method originally used PIL. For ONNX, we'll handle it via shape logic.
        # BUT to exactly replicate the code, we might accept a PIL-like input. 
        # For simplicity, let's assume we already have a 4D tensor shape (B,4,H,W).
        # So we might skip some logic or do an approximate approach. 
        # Or we do a "dummy" placeholder to keep the dimension the same.
        # Because typical ONNX export doesn't handle dynamic resizing well.

        # We'll do nothing here if we want a fixed shape input:
        return img

class CompositeAlpha(nn.Module):
    def __init__(self, background=0.5):
        super().__init__()
        # background is single float or (r,g,b)
        # We'll store as a constant
        if isinstance(background, float):
            self.background = torch.tensor([background]*3, dtype=torch.float32).reshape(3,1,1)
        else:
            self.background = torch.tensor(background, dtype=torch.float32).reshape(3,1,1)

    def forward(self, img: torch.Tensor) -> torch.Tensor:
        # Expect shape (B,4,H,W)
        # If the channel is 3, skip
        if img.size(1) == 3:
            return img

        # Separate alpha
        alpha = img[:, 3:4]  # shape (B,1,H,W)
        rgb = img[:, :3]     # shape (B,3,H,W)

        # composite
        rgb = rgb * alpha + (1.0 - alpha) * self.background.to(img.device)
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
                        "post_load_replacements": {}
                    }
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
                        "post_load_replacements": {}
                    }
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
                        "post_load_replacements": {}
                    }
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
                        "tags_filename": "tags_8034.json",
                        "format": "json",
                        "skip_lines": 0,
                        "append_placeholder": "placeholder0",  # note we append "placeholder0"
                        # or post-load transformations
                    }
                },
            "urls":
                [
                    "https://huggingface.co/Thouph/experimental_efficientnetv2_m_8035/resolve/main/model.onnx",
                    "https://huggingface.co/Thouph/experimental_efficientnetv2_m_8035/resolve/main/tags_8034.json"
                ],
            "pre-process":
                [
                    lambda: help.create_dirs(os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035"))
                ],
            "post-process": 
                [
                    lambda: rename_if_exists("experimental_efficientnetv2_m_8035", "model.onnx", "model.onnx"),
                    lambda: rename_if_exists("experimental_efficientnetv2_m_8035", "tags_8034.json", "tags.json"),
                    lambda: shutil.move(os.path.join(os.getcwd(), "model_balanced.pth"), os.path.join(os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035"), "model.onnx")),
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
                "tags_filename": "tagger_tags.json",
                "format": "json",  # could be "csv" or "json"
                # Do we skip lines?
                "skip_lines": 0,
                # Because you might do something like "replace underscores" in the loaded tags
                "post_load_replacements": {
                    "_": " "
                }
            },
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
                "tags_filename": "tagger_tags.json",
                "format": "json",
                "skip_lines": 0,
                "post_load_replacements": {
                    "_": " "
                }
            },
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
                "tags_filename": "tagger_tags.json",
                "format": "json",
                "skip_lines": 0,
                "post_load_replacements": {
                    "_": " "
                }
            },
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





def load_tags_for_model(model_key: str):
    info = model_info_map[model_key]["info"]
    tags_info = info["tags_file_info"]
    folder_name = model_key # is the name of the folder

    tags_file = os.path.join(folder_name, tags_info["tags_filename"])
    format_type = tags_info.get("format", "json")
    skip_lines = tags_info.get("skip_lines", 0)
    replacements = tags_info.get("post_load_replacements", {})

    # Actually open/parse:
    if format_type == "json":
        with open(tags_file, "r") as f:
            tags = json.load(f)
        # if we have skip_lines in JSON, you'd skip reading the first lines
        # (unusual for JSON, but might happen)
    elif format_type == "csv":
        tags = []
        with open(tags_file, "r") as f:
            for _ in range(skip_lines):
                next(f)  # skip lines
            # parse CSV lines into a list
            for line in f:
                line = line.strip()
                if line:
                    tags.append(line.split(",")[0])
    else:
        tags = []

    # do replacements
    processed_tags = []
    for tag in tags:
        for old, new in replacements.items():
            tag = tag.replace(old, new)
        processed_tags.append(tag)

    return processed_tags




def preprocess_image_pil(img_path: str, model_key: str) -> np.ndarray:
    """
    Example that reads (H,W) from 'input_dims' and mean/std from model config.
    """
    info = model_info_map[model_key]["info"]
    target_size = info.get("input_dims", (384, 384))
    mean_val = np.array(info.get("mean_norm", [0.5, 0.5, 0.5]), dtype=np.float32)
    std_val = np.array(info.get("mean_std",  [0.5, 0.5, 0.5]), dtype=np.float32)

    img = Image.open(img_path).convert("RGB")
    img = img.resize(target_size, Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0

    arr = (arr - mean_val) / std_val
    arr = arr.transpose(2, 0, 1)
    return arr[np.newaxis, ...]  # shape (1,3,H,W)




def run_inference_onnx(
    model_key: str,
    image_paths: list[str] | str,
    use_gpu: bool = False,
    threshold: float = 0.3
):
    """
    Runs ONNX inference on single or multiple images.
    - If one image is provided, we return *all* predictions (tag->score).
    - If multiple images are provided, we apply a threshold and return only the tags above it.
    - 'use_gpu=True' attempts the CUDA execution provider. If not installed or fails,
      it falls back to CPU.
    - 'threshold' is used only in batch mode.
    """
    # 1) Model config
    info = model_info_map[model_key]["info"]
    folder = model_key # is the name of the folder
    model_path = os.path.join(folder, "model.onnx")

    input_dims = info.get("input_dims", (384, 384))
    output_layer_size = info.get("output_layer_size", 9083)

    # 2) Create an ONNXRuntime session (CPU or GPU)
    providers = ["CPUExecutionProvider"]
    if use_gpu:
        # Attempt GPU if onnxruntime-gpu is installed
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

    session = ort.InferenceSession(model_path, providers=providers)

    # 3) Load tags
    tags_list = load_tags_for_model(model_key)
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
        arr = preprocess_image_pil(path, input_dims)
        batch_arrays.append(arr)
    # Combine into shape (B, 3, H, W)
    input_array = np.concatenate(batch_arrays, axis=0)

    # 6) ONNX input/output
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    # 7) Run inference
    outputs = session.run([output_name], {input_name: input_array})[0]
    # outputs shape: (B, output_layer_size)
    # Optionally apply a Sigmoid if your model outputs raw logits
    # row_sigmoid = 1 / (1 + exp(-row))

    results = []
    for i, row in enumerate(outputs):
        # Suppose your model is raw logits, apply Sigmoid:
        row_sigmoid = 1.0 / (1.0 + np.exp(-row))

        if single_image:
            # Return ALL tags with their probabilities
            # E.g. a list or dictionary
            # user can apply threshold in the GUI
            # We pair (tag, score)
            all_tags = []
            for idx, score in enumerate(row_sigmoid):
                if idx < len(tags_list):
                    all_tags.append((tags_list[idx], float(score)))
                else:
                    # if mismatch
                    all_tags.append((f"Unknown_{idx}", float(score)))

            # Sort desc by score
            all_tags.sort(key=lambda x: x[1], reverse=True)
            results.append({
                "image_path": image_paths[i],
                "predictions": all_tags  # everything
            })
        else:
            # BATCH mode: we do threshold filtering
            indices = np.where(row_sigmoid > threshold)[0]
            predicted_tags = []
            for idx in indices:
                tag_name = tags_list[idx] if idx < len(tags_list) else f"Unknown_{idx}"
                predicted_tags.append((tag_name, float(row_sigmoid[idx])))

            predicted_tags.sort(key=lambda x: x[1], reverse=True)
            results.append({
                "image_path": image_paths[i],
                "predictions": predicted_tags
            })

    return results



