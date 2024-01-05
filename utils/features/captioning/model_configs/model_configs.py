import shutil
import os

from utils import helper_functions as help

# mapping
model_info_map = {
    "Z3D-E621-Convnext":
        {
            "info":
                {
                    "input_dims":
                        (448, 448),
                    "output_layer_size":
                        9525,
                    "onnx_format":
                        True,
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
                    os.rename(os.path.join(os.getcwd(), "Z3D-E621-Convnext", "Z3D-E621-Convnext.onnx"),
                                os.path.join(os.getcwd(), "Z3D-E621-Convnext", "model.onnx")),
                    os.rename(os.path.join(os.getcwd(), "Z3D-E621-Convnext", "tags-selected.csv"),
                                os.path.join(os.getcwd(), "Z3D-E621-Convnext", "tags.csv"))
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
                    "https://huggingface.co/Thouph/eva02-clip-vit-large-7704/blob/main/model.onnx",
                    "https://huggingface.co/Thouph/eva02-clip-vit-large-7704/blob/main/tags.json"
                ],
            "pre-process":
                [
                    help.create_dirs(os.path.join(os.getcwd(), "eva02-clip-vit-large-7704"))
                ],
            "post-process":
                [
                    shutil.move(os.path.join(os.getcwd(), "model.onnx"),
                                os.path.join(os.getcwd(), "eva02-clip-vit-large-7704", "model.onnx")),
                    shutil.move(os.path.join(os.getcwd(), "tags.json"),
                                os.path.join(os.getcwd(), "eva02-clip-vit-large-7704", "tags.json"))
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
                        False,
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
                    "https://huggingface.co/Thouph/eva02-vit-large-448-8046/blob/main/model.pth",
                    "https://huggingface.co/Thouph/eva02-vit-large-448-8046/blob/main/tags_8041.json"
                ],
            "pre-process":
                [
                    help.create_dirs(os.path.join(os.getcwd(), "eva02-vit-large-448-8046"))
                ],
            "post-process":
                [
                    shutil.move(os.path.join(os.getcwd(), "model.pth"),
                                os.path.join(os.getcwd(), "eva02-vit-large-448-8046", "model.pth")),
                    shutil.move(os.path.join(os.getcwd(), "tags_8041.json"),
                                os.path.join(os.getcwd(), "eva02-vit-large-448-8046", "tags.json"))
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
                    "https://huggingface.co/Thouph/experimental_efficientnetv2_m_8035/blob/main/model_balanced.pth",
                    "https://huggingface.co/Thouph/experimental_efficientnetv2_m_8035/blob/main/tags_8034.json"
                ],
            "pre-process":
                [
                    help.create_dirs(os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035"))
                ],
            "post-process":
                [
                    shutil.move(os.path.join(os.getcwd(), "model_balanced.pth"),
                                os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035", "model.pth")),
                    shutil.move(os.path.join(os.getcwd(), "tags_8034.json"),
                                os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035", "tags.json"))
                ]
        }
}







def download_caption_model(model_selection: str):
    help.verbose_print(f"DOWNLOADING asset:\t{model_info_map[model_selection]}")
    # pre-process
    for pre_op in model_info_map[model_selection]["pre-process"]:
        eval(pre_op)
    # urls
    for url in model_info_map[model_selection]["urls"]:
        help.download_url(url, url.split('/')[-1])
    # post-process
    for post_op in model_info_map[model_selection]["post-process"]:
        eval(post_op)

    # finally unzip the file
    help.unzip_all()
    help.delete_all_archives()
    help.verbose_print("Done")


