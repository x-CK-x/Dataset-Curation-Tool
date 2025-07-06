import gradio as gr
import os
import copy
import glob
import numpy as np
from PIL import Image
import torch

from utils import md_constants as md_, helper_functions as help
from utils.features.video_splitter import Video2Frames as vid2frames
from utils.features.captioning import autotag
from utils.features.video_splitter.Video2Audio import Video2Audio


class Custom_dataset_tab:
    def __init__(self, image_board, cwd, download_tab_manager, gallery_tab_manager, image_mode_choice_state, autotagmodel,
                 all_predicted_confidences, all_predicted_tags):
        self.image_board = image_board
        self.cwd = cwd
        self.image_mode_choice_state = image_mode_choice_state
        self.autotagmodel = autotagmodel
        self.all_predicted_confidences = all_predicted_confidences
        self.all_predicted_tags = all_predicted_tags

        self.download_tab_manager = download_tab_manager
        self.gallery_tab_manager = gallery_tab_manager
        self.image_editor_tab_manager = None

        self.auto_tag_models = []
        self.converter = Video2Audio()


    def generate_all_dirs(self):
        temp_path_list_dirs = []
        batch_dir_path = os.path.join(os.getcwd(), self.download_tab_manager.settings_json["batch_folder"])
        temp_path_list_dirs.append(batch_dir_path)
        downloaded_posts_dir_path = os.path.join(batch_dir_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
        temp_path_list_dirs.append(downloaded_posts_dir_path)
        temp_path_list_dirs.append(os.path.join(downloaded_posts_dir_path, self.download_tab_manager.settings_json["png_folder"]))
        temp_path_list_dirs.append(os.path.join(downloaded_posts_dir_path, self.download_tab_manager.settings_json["jpg_folder"]))
        temp_path_list_dirs.append(os.path.join(downloaded_posts_dir_path, self.download_tab_manager.settings_json["webm_folder"]))
        temp_path_list_dirs.append(os.path.join(downloaded_posts_dir_path, self.download_tab_manager.settings_json["gif_folder"]))
        temp_path_list_dirs.append(os.path.join(downloaded_posts_dir_path, self.download_tab_manager.settings_json["swf_folder"]))
        temp_path_list_dirs.append(os.path.join(batch_dir_path, self.download_tab_manager.settings_json["tag_count_list_folder"]))

        help.verbose_print(temp_path_list_dirs)

        # create all dirs
        help.make_all_dirs(temp_path_list_dirs)
        # check to create tags & category csv files
        tag_folder = os.path.join(batch_dir_path, self.download_tab_manager.settings_json["tag_count_list_folder"])
        # persist changes to csv dictionary files OR (CREATE NEW)
        help.write_tags_to_csv(self.gallery_tab_manager.artist_csv_dict, os.path.join(tag_folder, "artist.csv"))
        help.write_tags_to_csv(self.gallery_tab_manager.character_csv_dict, os.path.join(tag_folder, "character.csv"))
        help.write_tags_to_csv(self.gallery_tab_manager.species_csv_dict, os.path.join(tag_folder, "species.csv"))
        help.write_tags_to_csv(self.gallery_tab_manager.general_csv_dict, os.path.join(tag_folder, "general.csv"))
        help.write_tags_to_csv(self.gallery_tab_manager.meta_csv_dict, os.path.join(tag_folder, "meta.csv"))
        help.write_tags_to_csv(self.gallery_tab_manager.rating_csv_dict, os.path.join(tag_folder, "rating.csv"))
        help.write_tags_to_csv(self.gallery_tab_manager.tags_csv_dict, os.path.join(tag_folder, "tags.csv"))

    def refresh_model_list(self):
        if not "Z3D-E621-Convnext" in self.auto_tag_models \
                and os.path.exists(os.path.join(os.getcwd(), 'Z3D-E621-Convnext')) \
                and os.path.exists(os.path.join(os.getcwd(), 'Z3D-E621-Convnext', 'model.onnx')):
            self.auto_tag_models.append('Z3D-E621-Convnext')

        if not "eva02-clip-vit-large-7704" in self.auto_tag_models \
                and os.path.exists(os.path.join(os.getcwd(), "eva02-clip-vit-large-7704")) \
                and os.path.exists(os.path.join(os.getcwd(), "eva02-clip-vit-large-7704", "model.onnx")):
            self.auto_tag_models.append("eva02-clip-vit-large-7704")

        if not "eva02-vit-large-448-8046" in self.auto_tag_models \
                and os.path.exists(os.path.join(os.getcwd(), "eva02-vit-large-448-8046")) \
                and os.path.exists(os.path.join(os.getcwd(), "eva02-vit-large-448-8046", "model.pth")):
            self.auto_tag_models.append("eva02-vit-large-448-8046")

        if not "experimental_efficientnetv2_m_8035" in self.auto_tag_models \
                and os.path.exists(os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035")) \
                and os.path.exists(os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035", "model.pth")):
            self.auto_tag_models.append("experimental_efficientnetv2_m_8035")

        if not "PNG Info" in self.auto_tag_models:
            self.auto_tag_models.append("PNG Info")

        model_choice_dropdown = gr.update(choices=self.auto_tag_models)
        return model_choice_dropdown

    def load_images(self, images_path, image_mode_choice_state):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        image_mode_choice_state = ""

        help.verbose_print(f"images_path:\t{images_path}")

        if images_path:
            if isinstance(images_path, list) and len(images_path) > 1:
                names = []
                for path in images_path:
                    help.verbose_print(f"path:\t{path}")
                    help.verbose_print(f"path.name:\t{path.name}")
                    names.append(path.name)
                self.autotagmodel.set_data(train_data_dir=names, single_image=False)
                image_mode_choice_state = 'Batch'
            else:
                if isinstance(images_path, list):
                    images_path = images_path[0]
                help.verbose_print(f"images_path:\t{images_path}")
                help.verbose_print(f"images_path.name:\t{images_path.name}")

                self.autotagmodel.set_data(train_data_dir=images_path.name, single_image=True)
                image_mode_choice_state = 'Single'
        help.verbose_print(f"images loaded")
        return image_mode_choice_state

    def set_image_editor_manager(self, image_editor_tab_manager):
        self.image_editor_tab_manager = image_editor_tab_manager

    def prompt_string_builder(self, use_tag_opts_radio, any_selected_tags, threshold):
        use_tag_opts = ['Use All', 'Use All above Threshold', 'Manually Select']
        image_generated_tags_prompt_builder_textbox = gr.update(value="")

        if (self.all_predicted_tags is not None and self.all_predicted_confidences is not None) and \
                (len(self.all_predicted_tags) > 0 and len(self.all_predicted_confidences) > 0):
            if use_tag_opts_radio is not None and len(use_tag_opts_radio) > 0:
                if use_tag_opts_radio in use_tag_opts[1]:
                    temp_confids = None
                    temp_tags = None
                    if len(self.all_predicted_tags) > 0:
                        temp_confids = copy.deepcopy(self.all_predicted_confidences)
                        temp_tags = copy.deepcopy(self.all_predicted_tags)
                        keys = list(temp_confids.keys())
                        for key in keys:
                            if temp_confids[key] <= (float(threshold) / 100.0):
                                del temp_confids[key]
                                temp_tags.remove(key)
                    sorted_list = sorted(temp_tags, key=lambda tag: (self.download_tab_manager.settings_json["tag_order_format"].split(", ")).index(self.gallery_tab_manager.get_category_name(tag)))
                    image_generated_tags_prompt_builder_textbox.update(value=", ".join(sorted_list))
                elif use_tag_opts_radio in use_tag_opts[0]:
                    sorted_list = sorted(copy.deepcopy(self.all_predicted_tags), key=lambda tag: (self.download_tab_manager.settings_json["tag_order_format"].split(", ")).index(self.gallery_tab_manager.get_category_name(tag)))
                    image_generated_tags_prompt_builder_textbox.update( value=", ".join(sorted_list))
                elif use_tag_opts_radio in use_tag_opts[2]:
                    sorted_list = sorted(any_selected_tags, key=lambda tag: (self.download_tab_manager.settings_json["tag_order_format"].split(", ")).index(self.gallery_tab_manager.get_category_name(tag)))
                    image_generated_tags_prompt_builder_textbox.update(value=", ".join(sorted_list))
        return image_generated_tags_prompt_builder_textbox

    def save_custom_tags(self, image_mode_choice_state, image_with_tag_path_textbox, any_selected_tags,
                         include_invalid_tags_ckbx):
        self.download_tab_manager.is_csv_loaded = False

        self.generate_all_dirs()

        all_paths = self.autotagmodel.get_dataset().get_image_paths()
        if all_paths is not None:
            all_paths = [path for path in all_paths if not (".txt" in path)]

        images_path = all_paths
        if (image_with_tag_path_textbox is None or not len(image_with_tag_path_textbox) > 0 or (
                images_path is None or not len(images_path) > 0)):
            raise ValueError(
                "Cannot complete Operation without completing fields: (write tag options / use tag options / path to files / images_path)")

        if image_mode_choice_state.lower() == 'single':
            self.autotagmodel.save_tags(single_image=True, any_selected_tags=any_selected_tags,
                                   all_tags_ever_dict=self.gallery_tab_manager.all_tags_ever_dict,
                                        include_invalid_tags_ckbx=include_invalid_tags_ckbx)
        elif image_mode_choice_state.lower() == 'batch':
            self.autotagmodel.save_tags(single_image=False, any_selected_tags=any_selected_tags,
                                   all_tags_ever_dict=self.gallery_tab_manager.all_tags_ever_dict,
                                        include_invalid_tags_ckbx=include_invalid_tags_ckbx)

        image_confidence_values = {}
        image_generated_tags = []
        image_preview_pil = None
        image_generated_tags_prompt_builder_textbox = ""
        return gr.update(value=image_confidence_values), gr.update(choices=image_generated_tags), gr.update(
            value=image_preview_pil), gr.update(value=image_generated_tags_prompt_builder_textbox)

    def load_model(self, model_name, use_cpu, event_data: gr.SelectData):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()

        model_path = ""
        model_name = ""
        if "Z3D-E621-Convnext" in event_data.value:
            model_path = os.path.join(os.getcwd(), "Z3D-E621-Convnext")
            model_name = "model.onnx"
            self.autotagmodel.set_run_option("model")
            self.autotagmodel.load_model(model_dir=model_path, model_name=model_name, use_cpu=use_cpu)

        elif "eva02-clip-vit-large-7704" in (event_data.value).lower():
            model_path = os.path.join(os.getcwd(), "eva02-clip-vit-large-7704")
            model_name = "model.onnx"
            self.autotagmodel.set_run_option("model")
            self.autotagmodel.load_model(model_dir=model_path, model_name=model_name, use_cpu=use_cpu)

        elif "eva02-vit-large-448-8046" in (event_data.value).lower():
            model_path = os.path.join(os.getcwd(), "eva02-vit-large-448-8046")
            model_name = "model.pth"
            self.autotagmodel.set_run_option("model")
            self.autotagmodel.load_model(model_dir=model_path, model_name=model_name, use_cpu=use_cpu)

        elif "experimental_efficientnetv2_m_8035" in (event_data.value).lower():
            model_path = os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035")
            model_name = "model.pth"
            self.autotagmodel.set_run_option("model")
            self.autotagmodel.load_model(model_dir=model_path, model_name=model_name, use_cpu=use_cpu)

        elif "info" in (event_data.value).lower():
            self.autotagmodel.set_run_option("info")

        help.verbose_print(f"selected option is:\t{event_data.value}")
        help.verbose_print(f"selected loaded using cpu={use_cpu}")

    # def re_load_model(model_name, use_cpu):
    #     global self.autotagmodel
    #     if self.autotagmodel is None:
    #         folder_path = os.path.join(cwd, settings_json["batch_folder"])
    #         folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
    #         folder_path = os.path.join(folder_path, settings_json["png_folder"])
    #         tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
    #                                              settings_json["tag_count_list_folder"])
    #         self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
    #         help.check_requirements()
    #
    #     self.autotagmodel.load_model(model_name=model_name, use_cpu=use_cpu)
    #     help.verbose_print(f"model reloaded using cpu={use_cpu}")

    def set_threshold(self, threshold):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()

        temp_confids = None
        temp_tags = None
        if len(self.all_predicted_tags) > 0:
            temp_confids = copy.deepcopy(self.all_predicted_confidences)
            temp_tags = copy.deepcopy(self.all_predicted_tags)
            keys = list(temp_confids.keys())
            for key in keys:
                if temp_confids[key] <= (float(threshold) / 100.0):
                    del temp_confids[key]
                    temp_tags.remove(key)

        self.autotagmodel.set_threshold(thresh=threshold)
        help.verbose_print(f"new threshold set:\t{(float(threshold) / 100.0)}")
        return gr.update(value=temp_confids), gr.update(choices=temp_tags)

    def update_image_mode(self, image_mode_choice_dropdown, event_data: gr.SelectData):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        image_modes = ['Single', 'Batch']
        print(f"image_mode_choice_dropdown:\t{image_mode_choice_dropdown}")
        print(f"event_data:\t{event_data}")
        print(f"event_data.name:\t{event_data.name}")
        print(f"event_data.value:\t{event_data.value}")
        if (event_data.value).lower() == 'single':
            return gr.update(label=f"{image_modes[0]} Image Mode", file_count="single", interactive=True)
        elif (event_data.value).lower() == 'batch':
            return gr.update(label=f"{image_modes[0]} Image Mode", file_count="directory", interactive=True)

    def set_square_size(self, square_image_edit_slider):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        self.autotagmodel.set_image_size(crop_size=square_image_edit_slider)
        help.verbose_print(f"new crop/resize dim/s set")

    def set_preprocess_options(self, operations_dropdown):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        help.verbose_print(f"set crop or resize")
        if self.autotagmodel:
            self.autotagmodel.set_preprocess_options(operations_dropdown)

    def set_landscape_square_crop(self, landscape_crop_dropdown, event_data: gr.SelectData):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        help.verbose_print(f"set landscape crop")
        if self.autotagmodel:
            self.autotagmodel.set_landscape_square_crop(event_data.value)

    def set_portrait_square_crop(self, portrait_crop_dropdown, event_data: gr.SelectData):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        help.verbose_print(f"set portrait crop")
        if self.autotagmodel:
            self.autotagmodel.set_portrait_square_crop(event_data.value)

    def set_write_tag_opts(self, event_data: gr.SelectData):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        self.autotagmodel.set_write_tag_opts(event_data.value)
        help.verbose_print(f"set write opts:\t{event_data.value}")
        merge_tag_opts_dropdown = gr.update(visible="merge" in (event_data.value).lower())
        return merge_tag_opts_dropdown

    def set_merge_tag_opts(self, all_merge_opts, event_data: gr.SelectData):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        self.autotagmodel.set_merge_tag_opts(all_merge_opts)
        help.verbose_print(f"set merge opts:\t{all_merge_opts}")

    def set_use_tag_opts_radio(self, event_data: gr.SelectData):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        self.autotagmodel.set_use_tag_opts(event_data.value)
        help.verbose_print(f"set use opts:\t{event_data.value}")

    def set_image_with_tag_path_textbox(self, image_with_tag_path_textbox):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        help.verbose_print(f"setting path to data origin")
        self.autotagmodel.set_image_with_tag_path_textbox(image_with_tag_path_textbox)

        help.verbose_print(self.autotagmodel.image_with_tag_path_textbox)


    def set_copy_mode_ckbx(self, copy_mode_ckbx):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        self.autotagmodel.set_copy_mode_ckbx(copy_mode_ckbx)
        help.verbose_print(f"set copy")

    def interrogate_images(self, image_mode_choice_state, confidence_threshold_slider, category_filter_dropdown,
                           category_filter_batch_checkbox, gallery_images_batch, include_invalid_tags_ckbx):
        self.download_tab_manager.is_csv_loaded = False

        self.generate_all_dirs()

        folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
        tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                     self.download_tab_manager.settings_json["tag_count_list_folder"])

        if self.autotagmodel is None:
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        image_confidence_values = None
        image_generated_tags = None
        image_preview_pil = None
        help.verbose_print(f"image_mode_choice_state:\t{image_mode_choice_state}")

        if 'single' == image_mode_choice_state.lower():
            self.autotagmodel.interrogate(single_image=True, all_tags_ever_dict=self.gallery_tab_manager.all_tags_ever_dict,
                                     filter_in_categories=category_filter_dropdown,
                                     filter_in_checkbox=category_filter_batch_checkbox,
                                          include_invalid_tags_ckbx=include_invalid_tags_ckbx)
            image_confidence_values, image_generated_tags, image_preview_pil = self.autotagmodel.get_predictions(True)
        else:
            self.autotagmodel.interrogate(single_image=False, all_tags_ever_dict=self.gallery_tab_manager.all_tags_ever_dict,
                                     filter_in_categories=category_filter_dropdown,
                                     filter_in_checkbox=category_filter_batch_checkbox,
                                          include_invalid_tags_ckbx=include_invalid_tags_ckbx)
            _, _, _ = self.autotagmodel.get_predictions(False)

        if image_confidence_values is None and image_generated_tags is None and image_preview_pil is None:
            return gr.update(value={}), gr.update(choices=[]), gr.update(value=None), gr.update(value=None)

        self.all_predicted_confidences = image_confidence_values
        self.all_predicted_tags = image_generated_tags

        temp_confids = copy.deepcopy(self.all_predicted_confidences)
        temp_tags = copy.deepcopy(self.all_predicted_tags)
        help.verbose_print(f"getting results")
        help.verbose_print(f"Removing NON-E6 tags")

        keys = list(temp_confids.keys())
        for key in keys:
            if not key in self.gallery_tab_manager.all_tags_ever_dict or image_confidence_values[key] <= (
                    float(confidence_threshold_slider) / 100.0):
                del temp_confids[key]
                temp_tags.remove(key)

        if image_preview_pil is not None:
            print("UPDATING IMAGE PREVIEW")
            image_preview_pil = np.array(image_preview_pil)  # [0]
            image_preview_pil = image_preview_pil[:, :, ::-1]  # BGR -> RGB
            image_preview_pil = Image.fromarray(np.uint8(image_preview_pil))  # *255#cm.gist_earth()
            image_preview_pil = gr.update(value=image_preview_pil)
        else:
            image_preview_pil = gr.update()

        # force reload csvs and global image dictionaries
        self.gallery_tab_manager.force_reload_images_and_csvs()

        # reset batch image component from the gallery
        gallery_images_batch = gr.update(value=(None if (gallery_images_batch is not None and len(gallery_images_batch.value) > 0) else gallery_images_batch))

        sorted_list = sorted(temp_tags, key=lambda tag: self.download_tab_manager.settings_json["tag_order_format"].split(", ").index(self.gallery_tab_manager.get_category_name(tag)))

        return gr.update(value=temp_confids), gr.update(choices=sorted_list), image_preview_pil, gallery_images_batch

    # also creates an empty tag file for the image file if there isn't one already
    def save_custom_images(self, image_mode_choice_state, image_with_tag_path_textbox, copy_mode_ckbx, include_invalid_tags_ckbx):
        self.download_tab_manager.is_csv_loaded = False

        self.generate_all_dirs()

        all_paths = None
        try:
            all_paths = self.autotagmodel.get_dataset().get_image_paths()
        except AttributeError:
            help.verbose_print(f"ATTRIBUTE ERROR LOADING SAVING IMAGE!!!")
            all_paths = self.autotagmodel.get_image_paths()
                # glob.glob(os.path.join(image_with_tag_path_textbox, f"*.jpg")) + \
                #         glob.glob(os.path.join(image_with_tag_path_textbox, f"*.png")) + \
                #         glob.glob(os.path.join(image_with_tag_path_textbox, f"*.gif"))

        help.verbose_print(f"all image paths to save:\t{all_paths}")
        help.verbose_print(f"image_with_tag_path_textbox:\t{image_with_tag_path_textbox}")

        if copy_mode_ckbx and all_paths is None: # default save option
            all_paths = glob.glob(os.path.join(image_with_tag_path_textbox, f"*.jpg")) + \
                        glob.glob(os.path.join(image_with_tag_path_textbox, f"*.png")) + \
                        glob.glob(os.path.join(image_with_tag_path_textbox, f"*.gif"))

        if all_paths is not None:
            all_paths = [path for path in all_paths if not (".txt" in path)]

        images_path = all_paths
        if (image_with_tag_path_textbox is None or not len(image_with_tag_path_textbox) > 0 or (
                images_path is None or not len(images_path) > 0)):
            raise ValueError(
                "Cannot complete Operation without completing fields: (write tag options / use tag options / path to files / images_path)")

        temp = '\\' if help.is_windows() else '/'
        folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])

        help.verbose_print(f"image_mode_choice_state:\t{image_mode_choice_state}")
        pick_mode = image_mode_choice_state.lower() if image_mode_choice_state is not None else (
            'batch' if len(images_path) > 1 else 'single')

        new_single_image_file_comp = None
        temp_new_path_single_image = None
        if pick_mode == 'single':
            # save image if augmented other than resize opt
            images_path = images_path[0]
            name = (images_path).split(temp)[-1]
            new_single_image_file_comp = gr.update(value=os.path.join(image_with_tag_path_textbox, name))

            temp_full_image_path = os.path.join(image_with_tag_path_textbox, name)
            temp_new_path_single_image = self.autotagmodel.save_image(name=name, src=image_with_tag_path_textbox)
            if temp_new_path_single_image is not None:
                new_single_image_file_comp = gr.update(value=temp_new_path_single_image)
                # setting the new file path to point to the saved augmented image
                self.autotagmodel.set_data(train_data_dir=temp_new_path_single_image, single_image=True)
                self.autotagmodel.dataset.set_image_paths(images=[temp_new_path_single_image])
                help.verbose_print(f"self.autotagmodel.get_image_paths():\t{self.autotagmodel.get_image_paths()}")

        if copy_mode_ckbx:  # caches images for gallery tab & persists to disk where the others are located
            help.verbose_print(f"all_paths:\t{all_paths}")

            help.verbose_print(f"image_mode_choice_state:\t{image_mode_choice_state}")

            if pick_mode == 'single': ### this currently does not update the tag dictionaries csv files | only if they use the model will it do that
                images_path = images_path[0]
                name = (images_path).split(temp)[-1]

                help.verbose_print(f"image name:\t{name}")

                if temp_new_path_single_image is not None:
                    # get new file name
                    name = temp_new_path_single_image.split(temp)[-1]
                    help.copy_over_imgs(
                        src=temp_new_path_single_image,
                        dst=os.path.join(folder_path, name),
                        image_mode_choice_state='single'
                    )
                else:
                    help.copy_over_imgs(
                        src=os.path.join(image_with_tag_path_textbox, name),
                        dst=os.path.join(folder_path, name),
                        image_mode_choice_state='single'
                    )

            # else:
            #     help.copy_over_imgs(
            #         src=image_with_tag_path_textbox,
            #         dst=folder_path,
            #         image_mode_choice_state='batch'
            #     )
        image_confidence_values = {}
        image_generated_tags = []
        image_preview_pil = None
        image_generated_tags_prompt_builder_textbox = ""

        return gr.update(value=image_confidence_values), gr.update(choices=image_generated_tags), \
               gr.update(value=image_preview_pil), gr.update(value=image_generated_tags_prompt_builder_textbox), \
               new_single_image_file_comp

    def video_upload_path(self, video_input_button):
        return gr.update(value=video_input_button.name)

    def convert_video(self, video_input, video_output_dir):
        vid2frames.video_to_frames(video_input.name, video_output_dir)
        video_gallery = gr.update(
            value=glob.glob(os.path.join(video_output_dir, f"*.png")))  # unless the file was a SWF file
        return video_gallery

    def update_generated_tag_selection(self, tag_effects_dropdown: gr.SelectData, image_generated_tags, threshold,
                                       category_filter_dropdown):
        tag_effects_dropdown = tag_effects_dropdown.value
        temp_confids = None
        available_tags = None
        if len(self.all_predicted_tags) > 0:
            temp_confids = copy.deepcopy(self.all_predicted_confidences)
            available_tags = copy.deepcopy(self.all_predicted_tags)
            keys = list(temp_confids.keys())
            for key in keys:
                if temp_confids[key] <= (float(threshold) / 100.0):
                    del temp_confids[key]
                    available_tags.remove(key)

        selected_tags = image_generated_tags

        if tag_effects_dropdown is None or len(tag_effects_dropdown) == 0:
            return gr.update(choices=available_tags, value=selected_tags)
        else:
            if "(Category) Select Any" in tag_effects_dropdown:
                selected_tags = [tag for tag in available_tags if self.gallery_tab_manager.get_category_name(tag) in category_filter_dropdown]
                return gr.update(choices=available_tags, value=selected_tags)
            elif "(Category) Clear Any" in tag_effects_dropdown:
                selected_tags = [tag for tag in image_generated_tags if
                                 not self.gallery_tab_manager.get_category_name(tag) in category_filter_dropdown]
                return gr.update(choices=available_tags, value=selected_tags)
            elif "(Category) Invert Any" in tag_effects_dropdown:
                selected_tags = [tag for tag in available_tags if
                                 (not tag in image_generated_tags and self.gallery_tab_manager.get_category_name(
                                     tag) in category_filter_dropdown) or
                                 (tag in image_generated_tags and not self.gallery_tab_manager.get_category_name(
                                     tag) in category_filter_dropdown)]
                return gr.update(choices=available_tags, value=selected_tags)
            elif "Select All" in tag_effects_dropdown:
                selected_tags = [tag for tag in available_tags]
                return gr.update(choices=available_tags, value=selected_tags)
            elif "Clear All" in tag_effects_dropdown:
                selected_tags = []
                return gr.update(choices=available_tags, value=selected_tags)
            elif "Invert All" in tag_effects_dropdown:
                selected_tags = [tag for tag in available_tags if not tag in image_generated_tags]
                return gr.update(choices=available_tags, value=selected_tags)

    def unload_component(self, value=None):
        return gr.update(value=value)

    def remove_invalid_chars(self, directory_path):
        # for all files in the specified path
        # rename them without invalid characters i.e. "."
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                # Splitting the filename and its extension
                name, ext = os.path.splitext(file)

                # Check if the filename (without extension) contains more than one "."
                if name.count('.') > 0:
                    # Remove all "." from the filename
                    new_name = name.replace('.', '')
                    # Join the cleaned name and the extension with a "."
                    final_name = new_name + ext

                    # Creating the full path for both old and new filenames
                    old_file_path = os.path.join(root, file)
                    new_file_path = os.path.join(root, final_name)

                    counter = 0
                    while os.path.exists(new_file_path):
                        final_name = f"{new_name}_{counter}{ext}"
                        new_file_path = os.path.join(root, final_name)
                        counter += 1

                    # Renaming the file
                    os.rename(old_file_path, new_file_path)
                    print(f'Renamed: {old_file_path} -> {new_file_path}')

    def resolve_unknown_exts(self, path, ext):
        help.verbose_print(path)
        onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        onlyfiles = [f for f in onlyfiles if (not os.path.isdir(os.path.join(path, f)))]
        onlyfiles = [f for f in onlyfiles if f.rfind(".") == -1]
        for f in onlyfiles:
            temp_path = os.path.join(path, f)
            counter = 0
            if os.path.exists(f"{temp_path}.{ext}"):
                while os.path.exists(f"{temp_path}_{counter}.{ext}"):
                    counter += 1
                os.rename(temp_path, f"{temp_path}_{counter}.{ext}")
            else:
                os.rename(temp_path, f"{temp_path}.{ext}")
        help.verbose_print(onlyfiles)
        help.verbose_print("Complete!")

    def replace_text_in_tags(self, folder_path, text_to_replace, text_replacement):
        # Get all .txt files in the folder
        txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]

        for file_name in txt_files:
            with open(os.path.join(folder_path, file_name), 'r') as f:
                content = f.read()

            # Split content into tags
            tags = content.split(", ")

            # Replace the text in each tag if it contains the text_to_replace
            modified = False
            for i, tag in enumerate(tags):
                if text_to_replace in tag:
                    tags[i] = tag.replace(text_to_replace, text_replacement)
                    modified = True

            # If changes were made, write the modified content back to the file
            if modified:
                with open(os.path.join(folder_path, file_name), 'w') as f:
                    f.write(", ".join(tags))


    def set_zoom_slider(self, slider_value):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        if self.autotagmodel:
            self.autotagmodel.set_zoom_slider(slider_value)


    def make_menus_visible(self, operations_dropdown):
        crop_horizontal_menu = None
        crop_vertical_menu = None
        zoom_slider = None
        rotate_slider = None
        scale_slider = None
        dx_slider = None
        dy_slider = None
        brightness_slider = None
        contrast_slider = None
        saturation_slider = None
        noise_slider = None
        shear_slider = None
        if self.operation_choices[0].lower() in [opt.lower() for opt in operations_dropdown]: # crop
            crop_horizontal_menu = gr.update(visible=True)
            crop_vertical_menu = gr.update(visible=True)
        else:
            crop_horizontal_menu = gr.update(visible=False, value=None)
            crop_vertical_menu = gr.update(visible=False, value=None)
        if self.operation_choices[1].lower() in [opt.lower() for opt in operations_dropdown]: # zoom
            zoom_slider = gr.update(visible=True)
        else:
            zoom_slider = gr.update(visible=False)
        if self.operation_choices[3].lower() in [opt.lower() for opt in operations_dropdown]: # rotate
            rotate_slider = gr.update(visible=True)
        else:
            rotate_slider = gr.update(visible=False)
        if self.operation_choices[4].lower() in [opt.lower() for opt in operations_dropdown]: # scale
            scale_slider = gr.update(visible=True)
        else:
            scale_slider = gr.update(visible=False)
        if self.operation_choices[5].lower() in [opt.lower() for opt in operations_dropdown]: # translate
            dx_slider = gr.update(visible=True)
            dy_slider = gr.update(visible=True)
        else:
            dx_slider = gr.update(visible=False)
            dy_slider = gr.update(visible=False)
        if self.operation_choices[6].lower() in [opt.lower() for opt in operations_dropdown]: # brightness
            brightness_slider = gr.update(visible=True)
        else:
            brightness_slider = gr.update(visible=False)

        if self.operation_choices[7].lower() in [opt.lower() for opt in operations_dropdown]: # contrast
            contrast_slider = gr.update(visible=True)
        else:
            contrast_slider = gr.update(visible=False)
        if self.operation_choices[8].lower() in [opt.lower() for opt in operations_dropdown]: # saturate
            saturation_slider = gr.update(visible=True)
        else:
            saturation_slider = gr.update(visible=False)
        if self.operation_choices[9].lower() in [opt.lower() for opt in operations_dropdown]:# noise
            noise_slider = gr.update(visible=True)
        else:
            noise_slider = gr.update(visible=False)
        if self.operation_choices[10].lower() in [opt.lower() for opt in operations_dropdown]: # shear
            shear_slider = gr.update(visible=True)
        else:
            shear_slider = gr.update(visible=False)

        return crop_horizontal_menu, crop_vertical_menu, zoom_slider, rotate_slider, scale_slider, dx_slider, dy_slider, brightness_slider, contrast_slider, saturation_slider, noise_slider, shear_slider

    def set_rotate_slider(self, slider_value):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        if self.autotagmodel:
            self.autotagmodel.set_rotate_slider(slider_value)
    def set_scale_slider(self, slider_value):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        if self.autotagmodel:
            self.autotagmodel.set_scale_slider(slider_value)
    def set_dx_slider(self, slider_value):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        if self.autotagmodel:
            self.autotagmodel.set_dx_slider(slider_value)
    def set_dy_slider(self, slider_value):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        if self.autotagmodel:
            self.autotagmodel.set_dy_slider(slider_value)
    def set_brightness_slider(self, slider_value):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        if self.autotagmodel:
            self.autotagmodel.set_brightness_slider(slider_value)
    def set_contrast_slider(self, slider_value):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        if self.autotagmodel:
            self.autotagmodel.set_contrast_slider(slider_value)
    def set_saturation_slider(self, slider_value):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        if self.autotagmodel:
            self.autotagmodel.set_saturation_slider(slider_value)
    def set_noise_slider(self, slider_value):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        if self.autotagmodel:
            self.autotagmodel.set_noise_slider(slider_value)
    def set_shear_slider(self, slider_value):
        if self.autotagmodel is None:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["png_folder"])
            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])
            self.autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir, image_board=self.image_board)
            help.check_requirements()
        if self.autotagmodel:
            self.autotagmodel.set_shear_slider(slider_value)

    def are_gpus_present(self, selected: gr.SelectData):
        # Check if any GPU is available
        gpu_available = torch.cuda.is_available()
        help.verbose_print(f"Is GPU available:\t{gpu_available}")

        # Get the number of GPUs
        num_gpus = torch.cuda.device_count()
        help.verbose_print(f"Number of GPUs detected:\t{num_gpus}")
        return gr.update(value=(selected.value and gpu_available))

    def render_tab(self):
        with gr.Tab("Add Custom Dataset"):
            gr.Markdown(md_.custom)
            with gr.Row():
                dataset_gallery_path_textbox = gr.Textbox(label="Dataset Folder Path",
                                                          info="Folder with images and tag txt files",
                                                          interactive=True,
                                                          elem_id="dataset_gallery_path_textbox")
                load_dataset_gallery_button = gr.Button(value="Load Dataset to Gallery",
                                                      variant='secondary',
                                                      elem_id="load_dataset_gallery_button")
            image_modes = ['Single', 'Batch']
            self.auto_tag_models.append("PNG Info")

            if not "Z3D-E621-Convnext" in self.auto_tag_models and os.path.exists(
                    os.path.join(os.getcwd(), 'Z3D-E621-Convnext')) \
                    and os.path.exists(
                os.path.join(os.path.join(os.getcwd(), 'Z3D-E621-Convnext'), 'model.onnx')):
                self.auto_tag_models.append('Z3D-E621-Convnext')

            if not "eva02-clip-vit-large-7704" in self.auto_tag_models \
                    and os.path.exists(os.path.join(os.getcwd(), "eva02-clip-vit-large-7704")) \
                    and os.path.exists(os.path.join(os.getcwd(), "eva02-clip-vit-large-7704", "model.onnx")):
                self.auto_tag_models.append("eva02-clip-vit-large-7704")

            if not "eva02-vit-large-448-8046" in self.auto_tag_models \
                    and os.path.exists(os.path.join(os.getcwd(), "eva02-vit-large-448-8046")) \
                    and os.path.exists(os.path.join(os.getcwd(), "eva02-vit-large-448-8046", "model.pth")):
                self.auto_tag_models.append("eva02-vit-large-448-8046")

            if not "experimental_efficientnetv2_m_8035" in self.auto_tag_models \
                    and os.path.exists(os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035")) \
                    and os.path.exists(os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035", "model.pth")):
                self.auto_tag_models.append("experimental_efficientnetv2_m_8035")

            write_tag_opts = ['Overwrite', 'Merge', 'Pre-pend', 'Append']
            merge_tag_opts = ['Union', 'Intersection', 'New-Original', 'Original-New']
            use_tag_opts = ['Use All', 'Use All above Threshold', 'Manually Select']
            tag_selection_list = ["(Category) Select Any", "(Category) Clear Any", "(Category) Invert Any",
                                  "Select All", "Clear All", "Invert All"]
            tab_selection = ["Image Default Editor", "Image Crop Editor", "Image Sketch Editor",
                             "Image Color Sketch Editor"]
            with gr.Row():
                with gr.Column():
                    with gr.Accordion(label="Image Settings", visible=True, open=False):
                        with gr.Row():
                            with gr.Tab("Single"):
                                file_upload_button_single = gr.File(label=f"{image_modes[0]} Image Mode",
                                                                    file_count="single",
                                                                    interactive=True, file_types=["image"],
                                                                    visible=True, type="filepath")
                            with gr.Tab("Batch"):
                                file_upload_button_batch = gr.File(label=f"{image_modes[1]} Image Mode",
                                                                   file_count="directory",
                                                                   interactive=True, visible=True, type="filepath")
                            with gr.Tab("Non-Interact Batch"):
                                gallery_images_batch = gr.File(label=f"(Non-Interact) {image_modes[1]} Image Mode",
                                                               file_count="multiple",
                                                               interactive=False, visible=True, type="filepath")
                            with gr.Tab("Image Preview"):
                                with gr.Column():
                                    image_preview_pil = gr.Image(label=f"Image Preview", interactive=False,
                                                                 visible=True, type="pil", height=840)
                        with gr.Row():
                            send_img_from_autotag_dropdown = gr.Dropdown(label="Image to Tab Selector",
                                                                     choices=tab_selection)
                            self.ext_choices = ["png", "jpg", "gif", "webm", "webp", "mp3", "mp4", "jpeg", "swf", "mov", "tiff", "psd", "blend", "pdf", "txt", "zip", "rar"]
                            ext_selection = gr.Dropdown(info="Extension Type",
                                                        value=self.ext_choices[0],
                                                        choices=self.ext_choices,
                                                        interactive=True,
                                                        show_label=False)
                        with gr.Row():
                            send_img_from_autotag_button = gr.Button(value="Send Image to (Other) Tab", variant='primary')
                            remove_invalid_chars_button = gr.Button(value="Remove Bad Filename Chars",
                                                                variant='secondary') # info="Uses the path provided to resolve all files"
                            fix_files = gr.Button(value="Resolve File Extesions",
                                                  variant="secondary")

                    with gr.Accordion(label="Model Settings", visible=True, open=False):
                        with gr.Row():
                            with gr.Column(elem_id="trim_row_length"):
                                gpu_ckbx = gr.Checkbox(label="GPU", info="Use GPU", value=False)
                            with gr.Column(elem_id="trim_row_length"):
                                gr.Markdown("""Refresh""", elem_id="trim_markdown_length")
                                refresh_symbol = '\U0001f504'  # 🔄
                                refresh_models_btn = gr.Button(value=refresh_symbol, variant="variant",
                                                               elem_id="refresh_models_btn")
                            model_choice_dropdown = gr.Dropdown(choices=self.auto_tag_models, label="Model Selection")
                            # Dropdown menu for selecting operations
                            self.operation_choices = ["Crop", "Zoom", "Resize", "Rotate", "Scale", "Translation",
                                                      "Brightness", "Contrast", "Saturation", "Noise", "Shear", "Horizontal Flip", "Vertical Flip"]
                            operations_dropdown = gr.Dropdown(choices=self.operation_choices,
                                                              multiselect=True, label="Preprocess Options",
                                                              interactive=True, value=[])
                        with gr.Row():
                            landscape_crop_dropdown = gr.Dropdown(choices=['left', 'mid', 'right', None],
                                                                  label="Landscape Crop", info="Mandatory",
                                                                  visible=False)
                            portrait_crop_dropdown = gr.Dropdown(choices=['top', 'mid', 'bottom', None],
                                                                 label="Portrait Crop", info="Mandatory", visible=False)
                        with gr.Column():
                            # Slider for zoom value (assuming you want to zoom between 0.5x to 3x)
                            zoom_slider = gr.Slider(minimum=0.5, maximum=3.0, value=1.0, step=0.1,
                                                           label=f"{self.operation_choices[1]} Value", visible=False)
                            rotate_slider = gr.Slider(minimum=-180, maximum=180, step=1, value=0, visible=False, label=f"{self.operation_choices[3]} Value")  # Rotate angle
                            scale_slider = gr.Slider(minimum=0.5, maximum=2, step=0.05, value=1, visible=False, label=f"{self.operation_choices[4]} Value")  # Scale factor
                            dx_slider = gr.Slider(minimum=-100, maximum=100, step=1, value=0, visible=False, label=f"{self.operation_choices[5]}-X Value")  # dx for translation
                            dy_slider = gr.Slider(minimum=-100, maximum=100, step=1, value=0, visible=False, label=f"{self.operation_choices[5]}-Y Value")  # dy for translation
                            brightness_slider = gr.Slider(minimum=0.5, maximum=2, step=0.05, value=1, visible=False, label=f"{self.operation_choices[6]} Value")  # Brightness factor
                            contrast_slider = gr.Slider(minimum=0.5, maximum=2, step=0.05, value=1, visible=False, label=f"{self.operation_choices[7]} Value")  # Contrast factor
                            saturation_slider = gr.Slider(minimum=0.5, maximum=2, step=0.05, value=1, visible=False, label=f"{self.operation_choices[8]} Value")  # Saturation factor
                            noise_slider = gr.Slider(minimum=0, maximum=100, step=1, value=0, visible=False, label=f"{self.operation_choices[9]} Value")  # Noise level
                            shear_slider = gr.Slider(minimum=-0.5, maximum=0.5, step=0.05, value=0, visible=False, label=f"{self.operation_choices[10]} Value")  # Shear factor
                        with gr.Row():
                            confidence_threshold_slider = gr.Slider(minimum=0, maximum=100, step=1,
                                                                    label='Confidence Threshold', value=75,
                                                                    visible=True, interactive=True)
                        with gr.Row():
                            interrogate_button = gr.Button(value="Interrogate", variant='primary')
                        with gr.Row():
                            image_with_tag_path_textbox = gr.Textbox(label="Path to Image/Video Folder",
                                                                     info="Folder should contain both (tag/s & image/s) if no video",
                                                                     interactive=True)
                        with gr.Row():
                            with gr.Column(min_width=50, scale=1):
                                copy_mode_ckbx = gr.Checkbox(label="Copy", info="Copy To Tag Editor")
                            with gr.Column(min_width=50, scale=1):
                                include_invalid_tags_ckbx = gr.Checkbox(
                                    label="Keep Invalid",
                                    info="Include Invalid tag/s",
                                    value=True,
                                    interactive=False,
                                )
                        with gr.Row():
                            with gr.Column(min_width=50, scale=2):
                                save_custom_images_button = gr.Button(value="Save/Add Images", variant='primary')
                            with gr.Column(min_width=50, scale=2):
                                save_custom_tags_button = gr.Button(value="Save/Add Tags", variant='primary')
                        with gr.Row():
                            write_tag_opts_dropdown = gr.Dropdown(label="Write Tag Options", choices=write_tag_opts)
                            merge_tag_opts_dropdown = gr.Dropdown(label="Merge Tag Options", choices=merge_tag_opts, multiselect=True, visible=False, interactive=True)
                            use_tag_opts_radio = gr.Dropdown(label="Use Tag Options", choices=use_tag_opts)
                    with gr.Accordion(label="Tag/s Options", visible=True, open=False):
                        with gr.Row():
                            text_to_replace_textbox = gr.Textbox(label="Text to Replace", interactive=True)
                            replacement_text_textbox = gr.Textbox(label="Replacement Text", interactive=True)
                            replace_text_button = gr.Button(value="Replace Text", variant='primary') # info='Replaces all text in every tag in all .txt files in the path specified'
                        with gr.Column():
                            image_generated_tags_prompt_builder_textbox = gr.Textbox(label="Prompt String", value="",
                                                                                     visible=True, interactive=False)
                            image_generated_tags = gr.CheckboxGroup(label="Generated Tag/s", choices=[], visible=True,
                                                                    interactive=True)
                        with gr.Row():
                            with gr.Column(min_width=50, scale=3):
                                tag_effects_dropdown = gr.Dropdown(label="Tag Selector Effect/s",
                                                                   choices=tag_selection_list)
                            with gr.Column(min_width=50, scale=1):
                                category_filter_batch_checkbox = gr.Checkbox(label="Enable Filter on Batch Mode", info="auto-selects/applies category selection to batch")
                        with gr.Row():
                            category_filter_dropdown = gr.Dropdown(label="Filter by Category (Multi-Select Enabled)",
                                                                   choices=list(self.image_board.categories_map.values()),
                                                                   multiselect=True)
                with gr.Column():
                    with gr.Tab("Tag/s Preview"):
                        with gr.Accordion(label="Tag/s Probabilities", visible=True, open=False):
                            with gr.Column():
                                image_confidence_values = gr.Label(label="Tag/s Confidence/s", visible=True, value={})
                        #         gr.Accordion(label="SAM-HQ Bounding Box Crop", visible=True, open=False)
                        #         gr.Accordion(label="SAM-HQ Segmentation Crop", visible=True, open=False)
                        #         gr.Accordion(label="Upscale", visible=True, open=False)
                        #         gr.Accordion(label="Denoise/Unglaze", visible=True, open=False)
                        #         gr.Accordion(label="Duplication Detection", visible=True, open=False)
                    with gr.Tab("Video to Frames Splitter"):
                        with gr.Accordion("Video to Frames Splitter", visible=True, open=False):
                            gr.Markdown("""
                                It is also partially possible to extract \"SOME\" video fragments from swf files with this tool, 
                                but it will require (FFMPEG) AND it likely \"NOT\" work in the majority of cases unless the contained video 
                                in the swf file is encoded within a specific set of formats. (for usage with SWF files, proceed at your own risk!)

                                Most other video formats (not swf associated) should work. (It is \"NOT\" recommended to attempt converting with corrupted video files either!)
                            """)
                            with gr.Column():
                                video_input = gr.File()
                                video_input_button = gr.UploadButton(label="Click to Upload a Video",
                                                                     file_types=["file"], file_count="single")
                                video_clear_button = gr.ClearButton(value="Clear")
                                with gr.Row():
                                    video_output_dir = gr.Textbox(label="(Optional) Output Folder Path",
                                                                  value=os.getcwd())
                                    convert_video_button = gr.Button(value="Convert Video", variant='primary')
                        with gr.Accordion(label="Gallery Preview", visible=True, open=False):
                            with gr.Column():
                                video_frames_gallery = gr.Gallery(label=f"Video Frame/s Gallery", interactive=False,
                                                                  visible=True, columns=3, object_fit="contain",
                                                                  height=780)
                    with gr.Tab("Video to Audio Splitter"):
                        gr.Markdown("""
                            FFMPEG is required to run this feature!
                            (linux) can be installed as part of the run button via a pop-up window that will appear
                            (macos & windows) users are advised to go to the Official Website to download \'ffmpeg\': https://ffmpeg.org/download.html
                        """)
                        with gr.Column():
                            video2audio_input = gr.File()
                            video2audio_input_button = gr.UploadButton(label="Click to Upload a Video",
                                                                 file_types=["file"], file_count="single")
                            video2audio_clear_button = gr.ClearButton(value="Clear")
                            with gr.Row():
                                video2audio_output_dir = gr.Textbox(label="(Optional) Output Folder Path",
                                                              value=os.getcwd())
                                convert_video2audio_button = gr.Button(value="Convert Video", variant='primary')
                        with gr.Accordion(label="Audio Preview", visible=True, open=False):
                            with gr.Column():
                                audio_waveform = gr.Audio(label="Audio Data", type="filepath", sources=["upload"], value=None, interactive=False)
                    # with gr.Tab("UMAP Viewer"):
                    #     with gr.Column():
                    #         gr.Textbox(label="Testing", value="")
                    #         gr.Image(label=f"Image Preview", interactive=False, visible=True, type="pil", height=730)
                    # with gr.Tab("Grad Cam Viewer"):
                    #     with gr.Column():
                    #         gr.Textbox(label="Testing", value="")
                    #         gr.Image(label=f"Image Preview", interactive=False, visible=True, type="pil", height=730)

        self.file_upload_button_single = file_upload_button_single
        self.file_upload_button_batch = file_upload_button_batch
        self.gallery_images_batch = gallery_images_batch
        self.image_preview_pil = image_preview_pil
        self.send_img_from_autotag_dropdown = send_img_from_autotag_dropdown
        self.send_img_from_autotag_button = send_img_from_autotag_button
        self.gpu_ckbx = gpu_ckbx
        self.refresh_models_btn = refresh_models_btn
        self.model_choice_dropdown = model_choice_dropdown
        self.operations_dropdown = operations_dropdown
        self.zoom_slider = zoom_slider
        self.rotate_slider = rotate_slider
        self.scale_slider = scale_slider
        self.dx_slider = dx_slider
        self.dy_slider = dy_slider
        self.brightness_slider = brightness_slider
        self.contrast_slider = contrast_slider
        self.saturation_slider = saturation_slider
        self.noise_slider = noise_slider
        self.shear_slider = shear_slider
        self.landscape_crop_dropdown = landscape_crop_dropdown
        self.portrait_crop_dropdown = portrait_crop_dropdown
        self.confidence_threshold_slider = confidence_threshold_slider
        self.interrogate_button = interrogate_button
        self.image_with_tag_path_textbox = image_with_tag_path_textbox
        self.dataset_gallery_path_textbox = dataset_gallery_path_textbox
        self.load_dataset_gallery_button = load_dataset_gallery_button
        self.copy_mode_ckbx = copy_mode_ckbx
        self.save_custom_images_button = save_custom_images_button
        self.save_custom_tags_button = save_custom_tags_button
        self.write_tag_opts_dropdown = write_tag_opts_dropdown
        self.use_tag_opts_radio = use_tag_opts_radio
        self.image_generated_tags_prompt_builder_textbox = image_generated_tags_prompt_builder_textbox
        self.image_generated_tags = image_generated_tags
        self.tag_effects_dropdown = tag_effects_dropdown
        self.category_filter_batch_checkbox = category_filter_batch_checkbox
        self.category_filter_dropdown = category_filter_dropdown
        self.image_confidence_values = image_confidence_values
        self.video_input = video_input
        self.video_input_button = video_input_button
        self.video_clear_button = video_clear_button
        self.video_output_dir = video_output_dir
        self.convert_video_button = convert_video_button
        self.video_frames_gallery = video_frames_gallery
        self.remove_invalid_chars_button = remove_invalid_chars_button
        self.fix_files = fix_files
        self.ext_selection = ext_selection
        self.merge_tag_opts_dropdown = merge_tag_opts_dropdown
        self.video2audio_input = video2audio_input
        self.video2audio_input_button = video2audio_input_button
        self.video2audio_clear_button = video2audio_clear_button
        self.video2audio_output_dir = video2audio_output_dir
        self.convert_video2audio_button = convert_video2audio_button
        self.audio_waveform = audio_waveform
        self.include_invalid_tags_ckbx = include_invalid_tags_ckbx
        self.text_to_replace_textbox = text_to_replace_textbox
        self.replacement_text_textbox = replacement_text_textbox
        self.replace_text_button = replace_text_button

        return [
                self.file_upload_button_single,
                self.file_upload_button_batch,
                self.gallery_images_batch,
                self.image_preview_pil,
                self.send_img_from_autotag_dropdown,
                self.send_img_from_autotag_button,
                self.gpu_ckbx,
                self.refresh_models_btn,
                self.model_choice_dropdown,
                self.operations_dropdown,
                self.zoom_slider,
                self.rotate_slider,
                self.scale_slider,
                self.dx_slider,
                self.dy_slider,
                self.brightness_slider,
                self.contrast_slider,
                self.saturation_slider,
                self.noise_slider,
                self.shear_slider,
                self.landscape_crop_dropdown,
                self.portrait_crop_dropdown,
                self.confidence_threshold_slider,
                self.interrogate_button,
                self.dataset_gallery_path_textbox,
                self.image_with_tag_path_textbox,
                self.load_dataset_gallery_button,
                self.copy_mode_ckbx,
                self.save_custom_images_button,
                self.save_custom_tags_button,
                self.write_tag_opts_dropdown,
                self.use_tag_opts_radio,
                self.image_generated_tags_prompt_builder_textbox,
                self.image_generated_tags,
                self.tag_effects_dropdown,
                self.category_filter_batch_checkbox,
                self.category_filter_dropdown,
                self.image_confidence_values,
                self.video_input,
                self.video_input_button,
                self.video_clear_button,
                self.video_output_dir,
                self.convert_video_button,
                self.video_frames_gallery,
                self.auto_tag_models,
                self.remove_invalid_chars_button,
                self.fix_files,
                self.ext_selection,
                self.merge_tag_opts_dropdown,
                self.video2audio_input,
                self.video2audio_input_button,
                self.video2audio_clear_button,
                self.video2audio_output_dir,
                self.convert_video2audio_button,
                self.audio_waveform,
                self.include_invalid_tags_ckbx,
                self.text_to_replace_textbox,
                self.replacement_text_textbox,
                self.replace_text_button
                ]

    def get_event_listeners(self):
        # batch interrogate and batch interrogate non-interact need option for self.include_invalid_tags_ckbx
        # and saving tag/s & images need self.include_invalid_tags_ckbx
        # a warning message for user that images copied to tag editor which are invalid may get deleted in the editor or cause error/s; proceed at their own risk!


        self.replace_text_button.click(
            fn=self.replace_text_in_tags,
            inputs=[self.image_with_tag_path_textbox, self.text_to_replace_textbox, self.replacement_text_textbox],
            outputs=[]
        )

        self.video2audio_input_button.upload(
            fn=self.video_upload_path,
            inputs=[self.video2audio_input_button],
            outputs=[self.video2audio_input]
        )
        self.convert_video2audio_button.click(
            fn=self.converter.extract_audio,
            inputs=[self.video2audio_input, self.video2audio_output_dir],
            outputs=[self.audio_waveform]
        )
        self.video2audio_clear_button.add(components=[self.audio_waveform, self.video2audio_input])

        self.merge_tag_opts_dropdown.select(
            fn=self.set_merge_tag_opts,
            inputs=[self.merge_tag_opts_dropdown],
            outputs=[]
        )
        # square_image_edit_slider.change(fn=set_square_size, inputs=[square_image_edit_slider], outputs=[])
        self.write_tag_opts_dropdown.select(
            fn=self.set_write_tag_opts,
            inputs=[],
            outputs=[self.merge_tag_opts_dropdown]
        )
        self.fix_files.click(
            fn=self.resolve_unknown_exts,
            inputs=[self.image_with_tag_path_textbox, self.ext_selection],
            outputs=[]
        )
        self.remove_invalid_chars_button.click(
            fn=self.remove_invalid_chars,
            inputs=[self.image_with_tag_path_textbox],
            outputs=[]
        )
        self.tag_effects_dropdown.select(
            fn=self.update_generated_tag_selection,
            inputs=[self.image_generated_tags, self.confidence_threshold_slider, self.category_filter_dropdown],
            outputs=[self.image_generated_tags]
        )
        self.send_img_from_autotag_button.click(
            fn=self.image_editor_tab_manager.send_images_from_feature,
            inputs=[self.send_img_from_autotag_dropdown,
                    self.file_upload_button_single,
                    gr.State(0),
                    gr.State(None),
                    gr.State(False),
                    gr.State(None),
                    gr.State(None),
                    gr.State(None),
                    gr.State(None)
                    ],
            outputs=[self.file_upload_button_single,
                     self.image_editor_tab_manager.image_editor,
                     self.image_editor_tab_manager.image_editor_crop,
                     self.image_editor_tab_manager.image_editor_sketch,
                     self.image_editor_tab_manager.image_editor_color_sketch,
                     self.gallery_images_batch
                     ]
        ).then(
            fn=self.load_images,
            inputs=[self.file_upload_button_single, self.image_editor_tab_manager.image_mode_choice_state],
            outputs=[self.image_editor_tab_manager.image_mode_choice_state]
        )
        self.refresh_models_btn.click(
            fn=self.refresh_model_list,
            inputs=[],
            outputs=[self.model_choice_dropdown]
        )
        self.image_generated_tags.change(
            fn=self.prompt_string_builder,
            inputs=[self.use_tag_opts_radio, self.image_generated_tags, self.confidence_threshold_slider],
            outputs=[self.image_generated_tags_prompt_builder_textbox]
        )
        self.save_custom_tags_button.click(
            fn=self.save_custom_tags,
            inputs=[self.image_mode_choice_state, self.image_with_tag_path_textbox, self.image_generated_tags,
                    self.include_invalid_tags_ckbx],
            outputs=[self.image_confidence_values, self.image_generated_tags, self.image_preview_pil,
                     self.image_generated_tags_prompt_builder_textbox]
        )
        self.save_custom_images_button.click(
            fn=self.save_custom_images,
            inputs=[self.image_mode_choice_state, self.image_with_tag_path_textbox, self.copy_mode_ckbx,
                    self.include_invalid_tags_ckbx],
            outputs=[self.image_confidence_values, self.image_generated_tags, self.image_preview_pil,
                     self.image_generated_tags_prompt_builder_textbox, self.file_upload_button_single]
        )
        self.interrogate_button.click(
            fn=self.unload_component,
            inputs=None,
            outputs=[self.image_preview_pil]
        ).then(
            fn=self.unload_component,
            inputs=gr.State([]),
            outputs=self.image_generated_tags
        ).then(
            fn=self.unload_component,
            inputs=gr.State(""),
            outputs=self.image_generated_tags_prompt_builder_textbox
        ).then(
            fn=self.interrogate_images,
            inputs=[self.image_mode_choice_state, self.confidence_threshold_slider, self.category_filter_dropdown,
                    self.category_filter_batch_checkbox, self.gallery_images_batch, self.include_invalid_tags_ckbx],
            outputs=[self.image_confidence_values, self.image_generated_tags, self.image_preview_pil,
                     self.gallery_images_batch],
            show_progress=True
        ).then(
            fn=self.prompt_string_builder,
            inputs=[self.use_tag_opts_radio, self.image_generated_tags, self.confidence_threshold_slider],
            outputs=[self.image_generated_tags_prompt_builder_textbox]
        )
        self.operations_dropdown.change(
            fn=self.make_menus_visible,
            inputs=[self.operations_dropdown],
            outputs=[self.landscape_crop_dropdown, self.portrait_crop_dropdown, self.zoom_slider, self.rotate_slider,
                     self.scale_slider, self.dx_slider, self.dy_slider, self.brightness_slider, self.contrast_slider,
                     self.saturation_slider, self.noise_slider, self.shear_slider]
        )
        self.model_choice_dropdown.select(
            fn=self.load_model,
            inputs=[self.model_choice_dropdown, self.gpu_ckbx],
            outputs=[]
        )








        self.gpu_ckbx.select(
            fn=self.are_gpus_present,
            inputs=[],
            outputs=[self.gpu_ckbx]
        )#.then(fn=RELOAD_MODEL)
        # self.gpu_ckbx.change(fn=re_load_model, inputs=[model_choice_dropdown, gpu_ckbx], outputs=[])########################################### i will need to re-load the model if this occurs









        self.confidence_threshold_slider.change(
            fn=self.set_threshold,
            inputs=[self.confidence_threshold_slider],
            outputs=[self.image_confidence_values, self.image_generated_tags]
        ).then(
            fn=self.prompt_string_builder,
            inputs=[self.use_tag_opts_radio, self.image_generated_tags, self.confidence_threshold_slider],
            outputs=[self.image_generated_tags_prompt_builder_textbox]
        )
        self.file_upload_button_single.upload(
            fn=self.load_images,
            inputs=[self.file_upload_button_single, self.image_mode_choice_state],
            outputs=[self.image_mode_choice_state]
        )
        self.file_upload_button_batch.upload(
            fn=self.load_images,
            inputs=[self.file_upload_button_batch, self.image_mode_choice_state],
            outputs=[self.image_mode_choice_state]
        )
        self.operations_dropdown.change(
            fn=self.set_preprocess_options,
            inputs=[self.operations_dropdown],
            outputs=[]
        )
        self.zoom_slider.change(
            fn=self.set_zoom_slider,
            inputs=[self.zoom_slider],
            outputs=[]
        )
        self.rotate_slider.change(
            fn=self.set_rotate_slider,
            inputs=[self.rotate_slider],
            outputs=[]
        )
        self.scale_slider.change(
            fn=self.set_scale_slider,
            inputs=[self.scale_slider],
            outputs=[]
        )
        self.dx_slider.change(
            fn=self.set_dx_slider,
            inputs=[self.dx_slider],
            outputs=[]
        )
        self.dy_slider.change(
            fn=self.set_dy_slider,
            inputs=[self.dy_slider],
            outputs=[]
        )
        self.brightness_slider.change(
            fn=self.set_brightness_slider,
            inputs=[self.brightness_slider],
            outputs=[]
        )
        self.contrast_slider.change(
            fn=self.set_contrast_slider,
            inputs=[self.contrast_slider],
            outputs=[]
        )
        self.saturation_slider.change(
            fn=self.set_saturation_slider,
            inputs=[self.saturation_slider],
            outputs=[]
        )
        self.noise_slider.change(
            fn=self.set_noise_slider,
            inputs=[self.noise_slider],
            outputs=[]
        )
        self.shear_slider.change(
            fn=self.set_shear_slider,
            inputs=[self.shear_slider],
            outputs=[]
        )








        self.landscape_crop_dropdown.select(
            fn=self.set_landscape_square_crop,
            inputs=[self.landscape_crop_dropdown],
            outputs=[]
        )
        self.portrait_crop_dropdown.select(
            fn=self.set_portrait_square_crop,
            inputs=[self.portrait_crop_dropdown],
            outputs=[]
        )
        self.use_tag_opts_radio.select(
            fn=self.set_use_tag_opts_radio,
            inputs=[],
            outputs=[]
        ).then(
            fn=self.prompt_string_builder,
            inputs=[self.use_tag_opts_radio, self.image_generated_tags, self.confidence_threshold_slider],
            outputs=[self.image_generated_tags_prompt_builder_textbox]
        )
        self.image_with_tag_path_textbox.change(
            fn=self.set_image_with_tag_path_textbox,
            inputs=[self.image_with_tag_path_textbox],
            outputs=[]
        )
        self.load_dataset_gallery_button.click(
            fn=self.gallery_tab_manager.reset_gallery_component_only,
            inputs=None,
            outputs=[self.gallery_tab_manager.gallery_comp, self.gallery_tab_manager.total_image_counter]
        ).then(
            fn=self.gallery_tab_manager.load_external_dataset,
            inputs=[self.dataset_gallery_path_textbox],
            outputs=[self.gallery_tab_manager.gallery_comp, self.gallery_tab_manager.total_image_counter]
        )
        self.copy_mode_ckbx.change(
            fn=self.set_copy_mode_ckbx,
            inputs=[self.copy_mode_ckbx],
            outputs=[]
        )
        self.video_input_button.upload(
            fn=self.video_upload_path,
            inputs=[self.video_input_button],
            outputs=[self.video_input]
        )
        self.convert_video_button.click(
            fn=self.convert_video,
            inputs=[self.video_input, self.video_output_dir],
            outputs=[self.video_frames_gallery]
        )
        self.video_clear_button.add(components=[self.video_frames_gallery, self.video_input])
