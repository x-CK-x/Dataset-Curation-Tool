import shutil
import os

from utils import helper_functions as help

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
                        1
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
                        False
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
                        False
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
                        False,
                    "model_extension":
                        "pth",
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
                        False
                },
            "urls":
                [
                    "https://huggingface.co/Thouph/experimental_efficientnetv2_m_8035/resolve/main/model_balanced.pth",
                    "https://huggingface.co/Thouph/experimental_efficientnetv2_m_8035/resolve/main/tags_8034.json"
                ],
            "pre-process":
                [
                    lambda: help.create_dirs(os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035"))
                ],
            "post-process": 
                [
                    lambda: rename_if_exists("experimental_efficientnetv2_m_8035", "model_balanced.pth", "model.pth"),
                    lambda: rename_if_exists("experimental_efficientnetv2_m_8035", "tags_8034.json", "tags.json"),
                    lambda: shutil.move(os.path.join(os.getcwd(), "model_balanced.pth"), os.path.join(os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035"), "model.pth")),
                    lambda: shutil.move(os.path.join(os.getcwd(), "tags_8034.json"), os.path.join(os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035"), "tags.json"))
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
            "tags_csv_format": False
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
            lambda: shutil.move(os.path.join(os.getcwd(), "tagger_tags.json"), os.path.join(os.path.join(os.getcwd(), "JTP_PILOT-e4-vit_so400m_patch14_siglip_384"), "tags.json"))
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
            "tags_csv_format": False
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
            lambda: shutil.move(os.path.join(os.getcwd(), "tagger_tags.json"), os.path.join(os.path.join(os.getcwd(), "JTP_PILOT2-2-e3-vit_so400m_patch14_siglip_384"), "tags.json"))
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
            "tags_csv_format": False
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
            lambda: shutil.move(os.path.join(os.getcwd(), "tagger_tags.json"), os.path.join(os.path.join(os.getcwd(), "JTP_PILOT2-e3-vit_so400m_patch14_siglip_384"), "tags.json"))
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


