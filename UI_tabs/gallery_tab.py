import gradio as gr
import os
import copy
import datetime
import glob

from utils import js_constants as js_, md_constants as md_, helper_functions as help


class Gallery_tab:
    def __init__(self, file_extn_list, image_board, cwd, multi_select_ckbx_state, only_selected_state_object,
                 images_selected_state, image_mode_choice_state,
                 previous_search_state_text, current_search_state_placement_tuple, relevant_search_categories,
                 initial_add_state, initial_add_state_tag, relevant_add_categories, images_tuple_points,
                 download_tab_manager, auto_complete_config_name, all_tags_ever_dict, all_images_dict,
                 selected_image_dict, artist_csv_dict, character_csv_dict, species_csv_dict, general_csv_dict,
                 meta_csv_dict, rating_csv_dict, tags_csv_dict, image_creation_times, is_csv_loaded
    ):
        self.file_extn_list = file_extn_list
        self.image_board = image_board
        self.cwd = cwd
        self.multi_select_ckbx_state = multi_select_ckbx_state
        self.only_selected_state_object = only_selected_state_object
        self.images_selected_state = images_selected_state
        self.image_mode_choice_state = image_mode_choice_state
        self.previous_search_state_text = previous_search_state_text
        self.current_search_state_placement_tuple = current_search_state_placement_tuple
        self.relevant_search_categories = relevant_search_categories
        self.initial_add_state = initial_add_state
        self.initial_add_state_tag = initial_add_state_tag
        self.relevant_add_categories = relevant_add_categories
        self.images_tuple_points = images_tuple_points
        self.auto_complete_config_name = auto_complete_config_name
        self.all_tags_ever_dict = all_tags_ever_dict
        self.all_images_dict = all_images_dict
        self.selected_image_dict = selected_image_dict
        self.artist_csv_dict = artist_csv_dict
        self.character_csv_dict = character_csv_dict
        self.species_csv_dict = species_csv_dict
        self.general_csv_dict = general_csv_dict
        self.meta_csv_dict = meta_csv_dict
        self.rating_csv_dict = rating_csv_dict
        self.tags_csv_dict = tags_csv_dict
        self.image_creation_times = image_creation_times



        self.advanced_settings_tab_manager = None
        self.download_tab_manager = download_tab_manager
        self.image_editor_tab_manager = None
        self.tag_ideas = None




    def set_tag_ideas(self, tag_ideas):
        self.tag_ideas = tag_ideas

    def set_advanced_settings_tab_manager(self, advanced_settings_tab_manager):
        self.advanced_settings_tab_manager = advanced_settings_tab_manager

    def set_image_editor_tab_manager(self, image_editor_tab_manager):
        self.image_editor_tab_manager = image_editor_tab_manager

    def set_custom_dataset_tab_manager(self, custom_dataset_tab_manager):
        self.custom_dataset_tab_manager = custom_dataset_tab_manager











    def get_saved_image_count(self):
        total_img_count = 0
        img_count_list = []
        for key in ['png', 'jpg', 'gif']:
            img_count_list.append(len(list(self.download_tab_manager.auto_complete_config[key].keys())))
            total_img_count += img_count_list[-1]
        img_count_list.append(total_img_count)
        return img_count_list

    def add_current_images(self):
        temp = list(self.all_images_dict.keys())
        if "searched" in temp:
            temp.remove("searched")
        for ext in temp:
            for image in list(self.all_images_dict[ext].keys()):
                if not image in self.download_tab_manager.auto_complete_config[ext]:
                    self.download_tab_manager.auto_complete_config[ext][image] = []

    def reload_selected_image_dict(self, ext, img_name):
        # help.verbose_print(f"self.all_images_dict:\t{self.all_images_dict}")
        # help.verbose_print(f"self.all_images_dict[ext]:\t{self.all_images_dict[ext]}")

        # self.selected_image_dict  # id -> {categories: tag/s}, type -> string
        if img_name:
            img_tag_list = copy.deepcopy(self.all_images_dict[ext][img_name])

            help.verbose_print(f"img_tag_list:\t\t{img_tag_list}")
            # determine the category of each tag (TAGS WITHOUT A CATEGORY ARE NOT DISPLAYED)
            temp_tag_dict = {}
            temp_list = [[], [], [], [], [], []]
            for tag in img_tag_list:
                if tag in self.all_tags_ever_dict:
                    if self.image_board.categories_map[self.all_tags_ever_dict[tag][0]] == 'artist':
                        temp_list[0].append(tag)
                    if self.image_board.categories_map[self.all_tags_ever_dict[tag][0]] == 'character':
                        temp_list[1].append(tag)
                    if self.image_board.categories_map[self.all_tags_ever_dict[tag][0]] == 'species':
                        temp_list[2].append(tag)
                    if self.image_board.categories_map[self.all_tags_ever_dict[tag][0]] == 'general':
                        temp_list[3].append(tag)
                    if self.image_board.categories_map[self.all_tags_ever_dict[tag][0]] == 'meta':
                        temp_list[4].append(tag)
                    if self.image_board.categories_map[self.all_tags_ever_dict[tag][0]] == 'rating':
                        temp_list[5].append(tag)
                else:
                    help.verbose_print(f"tag:\t{tag}\tnot in self.all_tags_ever_dict")
                    if tag in self.artist_csv_dict:  # artist
                        temp_list[0].append(tag)
                    if tag in self.character_csv_dict:  # character
                        temp_list[1].append(tag)
                    if tag in self.species_csv_dict:  # species
                        temp_list[2].append(tag)
                    if tag in self.general_csv_dict:  # general
                        temp_list[3].append(tag)
                    if tag in self.meta_csv_dict:  # meta
                        temp_list[4].append(tag)
                    if tag in self.rating_csv_dict:  # rating
                        temp_list[5].append(tag)

            temp_tag_dict["artist"] = temp_list[0]
            temp_tag_dict["character"] = temp_list[1]
            temp_tag_dict["species"] = temp_list[2]
            temp_tag_dict["general"] = temp_list[3]
            temp_tag_dict["meta"] = temp_list[4]
            temp_tag_dict["rating"] = temp_list[5]

            self.selected_image_dict = {}
            self.selected_image_dict[img_name] = copy.deepcopy(temp_tag_dict)
            self.selected_image_dict["type"] = ext
            help.verbose_print(f"self.selected_image_dict:\t\t{self.selected_image_dict}")
        else:
            self.selected_image_dict = None

    ### Update gellery component
    def update_search_gallery(self, sort_images, sort_option):
        temp = '\\' if help.is_windows() else '/'
        folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
        images = []
        for ext in list(self.all_images_dict["searched"].keys()):
            search_path = os.path.join(folder_path, self.download_tab_manager.settings_json[f"{ext}_folder"])
            for img_id in list(self.all_images_dict["searched"][ext].keys()):
                images.append(os.path.join(search_path, f"{img_id}.{ext}"))

        if sort_images and len(sort_option) > 0 and len(list(self.image_creation_times.keys())) > 0:
            # parse to img_id -> to get the year
            if sort_option == "new-to-old":
                images = sorted(images, key=lambda x: self.image_creation_times.get(((x.split(temp)[-1]).split(".")[0]),
                                                                               float('-inf')), reverse=True)
            elif sort_option == "old-to-new":
                images = sorted(images, key=lambda x: self.image_creation_times.get(((x.split(temp)[-1]).split(".")[0]),
                                                                               float('-inf')))
        # help.verbose_print(f"images:\t{images}")
        return images

    def initialize_posts_timekeeper(self):
        start_year_temp = int(self.download_tab_manager.settings_json["min_year"])
        end_year_temp = datetime.date.today().year
        help.verbose_print(f"start_year_temp:\t{start_year_temp}")
        help.verbose_print(f"end_year_temp:\t{end_year_temp}")
        years_to_check_list = list(range(start_year_temp, (end_year_temp + 1), 1))
        help.verbose_print(f"years_to_check_list:\t{years_to_check_list}")

        if len(list(self.image_creation_times.keys())) == 0:
            temp_keys_all_images_dict = list(self.all_images_dict.keys())
            if "searched" in temp_keys_all_images_dict:
                temp_keys_all_images_dict.remove("searched")
            for ext in temp_keys_all_images_dict:
                for img_id in list(self.all_images_dict[ext].keys()):
                    for year in years_to_check_list:
                        if str(year) in self.all_images_dict[ext][img_id]:
                            self.image_creation_times[img_id] = year
                            break
        help.verbose_print(f"self.image_creation_times:\t{self.image_creation_times}")

    def is_csv_dict_empty(self, stats_load_file):
        tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                     self.download_tab_manager.settings_json["tag_count_list_folder"])
        if "artist" in stats_load_file:
            value = len(list(self.artist_csv_dict.keys()))
            if (value == 0):
                self.artist_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "artist.csv"))
            return [copy.deepcopy(self.artist_csv_dict), value]
        elif "character" in stats_load_file:
            value = len(list(self.character_csv_dict.keys()))
            if (value == 0):
                self.character_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "character.csv"))
            return [copy.deepcopy(self.character_csv_dict), value]
        elif "species" in stats_load_file:
            value = len(list(self.species_csv_dict.keys()))
            if (value == 0):
                self.species_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "species.csv"))
            return [copy.deepcopy(self.species_csv_dict), value]
        elif "general" in stats_load_file:
            value = len(list(self.general_csv_dict.keys()))
            if (value == 0):
                self.general_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "general.csv"))
            return [copy.deepcopy(self.general_csv_dict), value]
        elif "meta" in stats_load_file:
            value = len(list(self.meta_csv_dict.keys()))
            if (value == 0):
                self.meta_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "meta.csv"))
            return [copy.deepcopy(self.meta_csv_dict), value]
        elif "rating" in stats_load_file:
            value = len(list(self.rating_csv_dict.keys()))
            if (value == 0):
                self.rating_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "rating.csv"))
            return [copy.deepcopy(self.rating_csv_dict), value]
        elif "tags" in stats_load_file:
            value = len(list(self.tags_csv_dict.keys()))
            if (value == 0):
                self.tags_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "tags.csv"))
            return [copy.deepcopy(self.tags_csv_dict), value]

    def load_images_and_csvs(self):
        if (not self.download_tab_manager.is_csv_loaded) or (not self.all_images_dict or len(self.all_images_dict.keys()) == 0):

            batch_path_check = os.path.exists(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]))
            help.verbose_print(f"batch_path_check:\t{batch_path_check}")

            tag_count_path_check = os.path.exists(os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                         self.download_tab_manager.settings_json["tag_count_list_folder"]))
            help.verbose_print(f"tag_count_path_check:\t{tag_count_path_check}")

            artists_path_check = os.path.exists(os.path.join(os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                         self.download_tab_manager.settings_json["tag_count_list_folder"]), "artist.csv"))

            help.verbose_print(f"artists_path_check:\t{artists_path_check}")

            if batch_path_check and tag_count_path_check and artists_path_check:
                help.verbose_print(f"os.path.join(self.cwd, self.download_tab_manager.settings_json['batch_folder']):\t{os.path.join(self.cwd, self.download_tab_manager.settings_json['batch_folder'])}")
                full_path_downloads = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                                   self.download_tab_manager.settings_json["downloaded_posts_folder"])
                help.verbose_print(f"full_path_downloads:\t{full_path_downloads}")
                help.verbose_print(f"os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f'png_folder']):\t{os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f'png_folder'])}")
                help.verbose_print(f"os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f'jpg_folder']):\t{os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f'jpg_folder'])}")
                help.verbose_print(f"os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f'gif_folder']):\t{os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f'gif_folder'])}")
                tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                             self.download_tab_manager.settings_json["tag_count_list_folder"])
                help.verbose_print(f"tag_count_dir:\t{tag_count_dir}")
                help.verbose_print(f"os.path.join(tag_count_dir, 'artist.csv'):\t{os.path.join(tag_count_dir, 'artist.csv')}")



                # clear searched dict
                if "searched" in self.all_images_dict:
                    del self.all_images_dict["searched"]
                    self.all_images_dict["searched"] = {}

                # reset
                self.all_images_dict = {}

                if not self.all_images_dict or len(self.all_images_dict.keys()) == 0:
                    self.all_images_dict = help.merge_dict(os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"png_folder"]),
                                                      os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"jpg_folder"]),
                                                      os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"gif_folder"]))

                # populate the timekeeping dictionary
                self.initialize_posts_timekeeper()

                self.download_tab_manager.is_csv_loaded = True
                self.artist_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "artist.csv"))
                self.character_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "character.csv"))
                self.species_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "species.csv"))
                self.general_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "general.csv"))
                self.meta_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "meta.csv"))
                self.rating_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "rating.csv"))
                self.tags_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "tags.csv"))

    def force_reload_images_and_csvs(self):
        # clear searched dict
        if "searched" in self.all_images_dict:
            del self.all_images_dict["searched"]
            self.all_images_dict["searched"] = {}

        full_path_downloads = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                           self.download_tab_manager.settings_json["downloaded_posts_folder"])
        if not self.all_images_dict or len(self.all_images_dict.keys()) == 0:
            self.all_images_dict = help.merge_dict(os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"png_folder"]),
                                              os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"jpg_folder"]),
                                              os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"gif_folder"]))

        # populate the timekeeping dictionary
        self.initialize_posts_timekeeper()

        tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                     self.download_tab_manager.settings_json["tag_count_list_folder"])
        self.download_tab_manager.is_csv_loaded = True
        self.artist_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "artist.csv"))
        self.character_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "character.csv"))
        self.species_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "species.csv"))
        self.general_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "general.csv"))
        self.meta_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "meta.csv"))
        self.rating_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "rating.csv"))
        self.tags_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "tags.csv"))

    ### Search a set of images
    def filter_images_by_tags(self, input_tags, allowed_image_types):
        # clear searched dict
        del self.all_images_dict["searched"]
        self.all_images_dict["searched"] = {}
        # remove possible checked searched flag
        if "searched" in allowed_image_types:
            allowed_image_types.remove("searched")

        input_tags_list = input_tags.split(" ")  # [tag.strip() for tag in input_tags.split(',')]
        positive_tags = [str(tag) for tag in input_tags_list if not tag.startswith('-')]
        negative_tags = [str(tag[1:]) for tag in input_tags_list if tag.startswith('-')]

        if allowed_image_types is None:
            allowed_image_types = self.all_images_dict.keys()

        filtered_images = {ext: {} for ext in allowed_image_types}

        for ext, images in self.all_images_dict.items():
            if ext in allowed_image_types:
                for image_id, tags in images.items():
                    if all(tag in tags for tag in positive_tags) and not any(tag in tags for tag in negative_tags):
                        filtered_images[str(ext)][str(image_id)] = tags
        self.all_images_dict["searched"] = copy.deepcopy(filtered_images)
        help.verbose_print(f"===============================")

    def search_tags(self, tag_search_textbox, global_search_opts, sort_images, sort_option):
        # update SEARCHED in global dictionary
        self.filter_images_by_tags(tag_search_textbox, global_search_opts)
        # return updated gallery
        images = self.update_search_gallery(sort_images, sort_option)
        return gr.update(value=images, visible=True)

    def add_to_csv_dictionaries(self, string_category, tag, count=1):
        self.artist_csv_dict, self.character_csv_dict, self.species_csv_dict, \
        self.general_csv_dict, self.meta_csv_dict, self.rating_csv_dict, \
        self.tags_csv_dict = help.update_all_csv_dictionaries(copy.deepcopy(self.artist_csv_dict),
                                                         copy.deepcopy(self.character_csv_dict),
                                                         copy.deepcopy(self.species_csv_dict),
                                                         copy.deepcopy(self.general_csv_dict),
                                                         copy.deepcopy(self.meta_csv_dict), copy.deepcopy(self.rating_csv_dict),
                                                         copy.deepcopy(self.tags_csv_dict),
                                                         string_category, tag, "+", count)

    def remove_to_csv_dictionaries(self, string_category, tag, count=1):
        self.artist_csv_dict, self.character_csv_dict, self.species_csv_dict, \
        self.general_csv_dict, self.meta_csv_dict, self.rating_csv_dict, \
        self.tags_csv_dict = help.update_all_csv_dictionaries(copy.deepcopy(self.artist_csv_dict),
                                                         copy.deepcopy(self.character_csv_dict),
                                                         copy.deepcopy(self.species_csv_dict),
                                                         copy.deepcopy(self.general_csv_dict),
                                                         copy.deepcopy(self.meta_csv_dict), copy.deepcopy(self.rating_csv_dict),
                                                         copy.deepcopy(self.tags_csv_dict),
                                                         string_category, tag, "-", count)

    def get_insert_last_tags_name(self, string_category, ext, img_id, new_tag):
        del self.selected_image_dict

        # reload the categories for the self.selected_image_dict
        self.reload_selected_image_dict(ext, img_id)

        # temporarily remove the new tag if it is added already
        if new_tag in self.selected_image_dict[img_id][string_category]:
            index = (self.selected_image_dict[img_id][string_category]).index(new_tag)
            del self.selected_image_dict[img_id][string_category][index]

        # list of orderings
        temp_category_list = [self.selected_image_dict[img_id]["artist"], self.selected_image_dict[img_id]["character"],
                              self.selected_image_dict[img_id]["species"], self.selected_image_dict[img_id]["general"],
                              self.selected_image_dict[img_id]["meta"], self.selected_image_dict[img_id]["rating"]]
        category_order_dict = {"artist": 0, "character": 1, "species": 2, "general": 3, "meta": 4, "rating": 5}

        # determine the initial dictionary number
        current_dict_num = category_order_dict[string_category]

        # collect tag name which came before the new tag
        temp_tag_name = None
        # while category is empty check the previous one
        while (current_dict_num >= 0):
            if len(temp_category_list[current_dict_num]) > 0:
                # get name at end of category list
                temp_tag_name = temp_category_list[current_dict_num][-1]
                # break
                break
            current_dict_num -= 1

        # re-add new tag if not present
        if not new_tag in self.selected_image_dict[img_id][string_category]:
            self.selected_image_dict[img_id][string_category].append(new_tag)
        return temp_tag_name

    # this method only effects ONE category at a time
    # self.selected_image_dict has the form:
    #     id -> {categories: [tags]}
    #     type -> ext
    def add_tag_changes(self, tag_string, apply_to_all_type_select_checkboxgroup, img_id, multi_select_ckbx_state,
                        only_selected_state_object, images_selected_state, state_of_suggestion, is_textbox):
        img_id = str(img_id)

        # help.verbose_print(f"$$$$$$$$$ tag_string:\t{tag_string}")
        # help.verbose_print(f"$$$$$$$$$ state_of_suggestion:\t{state_of_suggestion}")
        # help.verbose_print(f"$$$$$$$$$ len(tag_string):\t{len(tag_string)}")

        tag_list = []

        # this if statement will have more logic to prevent the two tags present case
        if tag_string is None or len(tag_string) == 0:  # or self.selected_image_dict is not None

            new_state_of_suggestion_tag = "" if is_textbox else state_of_suggestion
            new_state_of_suggestion_textbox = gr.update(value=new_state_of_suggestion_tag)

            # find type of selected image
            temp_ext = None
            temp_all_images_dict_keys = list(self.all_images_dict.keys())
            if "searched" in temp_all_images_dict_keys:
                temp_all_images_dict_keys.remove("searched")
            for each_key in temp_all_images_dict_keys:
                if img_id in list(self.all_images_dict[each_key]):
                    temp_ext = each_key
                    break

            img_artist_tag_checkbox_group = None
            img_character_tag_checkbox_group = None
            img_species_tag_checkbox_group = None
            img_general_tag_checkbox_group = None
            img_meta_tag_checkbox_group = None
            img_rating_tag_checkbox_group = None
            if self.selected_image_dict is not None:
                # reload the categories for the self.selected_image_dict
                self.reload_selected_image_dict(temp_ext, img_id)

                img_artist_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['artist'], value=[])
                img_character_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['character'], value=[])
                img_species_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['species'], value=[])
                img_general_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['general'], value=[])
                img_meta_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['meta'], value=[])
                img_rating_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['rating'], value=[])
            else:
                img_artist_tag_checkbox_group = gr.update(choices=[], value=[])
                img_character_tag_checkbox_group = gr.update(choices=[], value=[])
                img_species_tag_checkbox_group = gr.update(choices=[], value=[])
                img_general_tag_checkbox_group = gr.update(choices=[], value=[])
                img_meta_tag_checkbox_group = gr.update(choices=[], value=[])
                img_rating_tag_checkbox_group = gr.update(choices=[], value=[])

            return img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group, \
                   img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group, \
                   new_state_of_suggestion_tag, new_state_of_suggestion_textbox

        tag_list.append(tag_string)

        # help.verbose_print(f">>>>>>>>>>>> tag_list:\t{tag_list}")

        new_state_of_suggestion_tag = "" if is_textbox else state_of_suggestion
        new_state_of_suggestion_textbox = gr.update(value=new_state_of_suggestion_tag)

        # find type of selected image
        temp_ext = None
        temp_all_images_dict_keys = list(self.all_images_dict.keys())
        if "searched" in temp_all_images_dict_keys:
            temp_all_images_dict_keys.remove("searched")
        for each_key in temp_all_images_dict_keys:
            if img_id in list(self.all_images_dict[each_key]):
                temp_ext = each_key
                break
        # reload the categories for the self.selected_image_dict
        if len(images_selected_state) == 0 and not multi_select_ckbx_state[0]:
            self.reload_selected_image_dict(temp_ext, img_id)

        # updates selected image ONLY when it ( IS ) specified AND its TYPE is specified for edits in "apply_to_all_type_select_checkboxgroup"
        if img_id and len(img_id) > 0 and self.selected_image_dict and (
                not apply_to_all_type_select_checkboxgroup or len(apply_to_all_type_select_checkboxgroup) == 0):
            # find image in searched : id
            if (self.selected_image_dict["type"] in list(self.all_images_dict['searched'].keys())) and (
                    img_id in list(self.all_images_dict["searched"][self.selected_image_dict["type"]].keys())):
                for tag in tag_list:
                    if not tag in self.all_images_dict["searched"][self.selected_image_dict["type"]][img_id]:
                        # get last tag in category
                        last_tag = self.get_insert_last_tags_name(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]],
                                                             self.selected_image_dict["type"], img_id,
                                                             tag)  # i.e. the tag before the new one
                        help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                        # get its index on the global list
                        glob_index = 0
                        if last_tag:
                            glob_index = (self.all_images_dict["searched"][self.selected_image_dict["type"]][img_id]).index(
                                last_tag)
                            glob_index += 1  # puts the pointer at end of category list
                        self.all_images_dict["searched"][self.selected_image_dict["type"]][img_id].insert(glob_index, tag)

                        glob_index = (self.all_images_dict[self.selected_image_dict["type"]][img_id]).index(last_tag)
                        self.all_images_dict[self.selected_image_dict["type"]][img_id].insert(glob_index, tag)

                        if not img_id in self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]]:
                            self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]][img_id] = []
                        self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]][img_id].append(['+', tag, (glob_index)])

                        # create or increment category table AND frequency table for (all) tags
                        self.add_to_csv_dictionaries(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]], tag)  # add
            elif img_id in list(self.all_images_dict[self.selected_image_dict["type"]].keys()):  # find image in ( TYPE ) : id
                for tag in tag_list:
                    if not tag in self.all_images_dict[self.selected_image_dict["type"]][img_id]:
                        # get last tag in category
                        last_tag = self.get_insert_last_tags_name(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]],
                                                             self.selected_image_dict["type"], img_id,
                                                             tag)  # i.e. the tag before the new one
                        help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                        # get its index on the global list
                        glob_index = 0
                        if last_tag:
                            glob_index = (self.all_images_dict[self.selected_image_dict["type"]][img_id]).index(last_tag)
                            glob_index += 1  # puts the pointer at end of category list
                        self.all_images_dict[self.selected_image_dict["type"]][img_id].insert(glob_index, tag)

                        if not img_id in self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]]:
                            self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]][img_id] = []
                        self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]][img_id].append(['+', tag, (glob_index)])

                        # create or increment category table AND frequency table for (all) tags
                        self.add_to_csv_dictionaries(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]], tag)  # add
        if len(apply_to_all_type_select_checkboxgroup) > 0:
            if "searched" in apply_to_all_type_select_checkboxgroup:  # edit searched and then all the instances of the respective types
                if multi_select_ckbx_state[0]:
                    ##### returns index -> [ext, img_id]
                    for index in images_selected_state:
                        ext, img_id = only_selected_state_object[index]
                        if ext in apply_to_all_type_select_checkboxgroup:
                            if img_id in list(self.all_images_dict["searched"][ext].keys()):
                                for tag in tag_list:
                                    if not tag in self.all_images_dict["searched"][ext][img_id]:  # add tag
                                        # get last tag in category
                                        last_tag = self.get_insert_last_tags_name(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]],
                                                                             ext, img_id,
                                                                             tag)  # i.e. the tag before the new one
                                        help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                                        # get its index on the global list
                                        glob_index = 0
                                        if last_tag:
                                            glob_index = (self.all_images_dict["searched"][ext][img_id]).index(last_tag)
                                            glob_index += 1  # puts the pointer at end of category list

                                        help.verbose_print(f"tag:\t\t{tag}")

                                        self.all_images_dict["searched"][ext][img_id].insert(glob_index, tag)

                                        self.all_images_dict[ext][img_id].insert(glob_index, tag)

                                        if not img_id in self.download_tab_manager.auto_complete_config[ext]:
                                            self.download_tab_manager.auto_complete_config[ext][img_id] = []
                                        self.download_tab_manager.auto_complete_config[ext][img_id].append(['+', tag, (glob_index)])

                                        # create or increment category table AND frequency table for (all) tags
                                        self.add_to_csv_dictionaries(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]], tag)  # add
                else:
                    for key_type in list(self.all_images_dict["searched"].keys()):
                        for img_id in list(self.all_images_dict["searched"][key_type].keys()):
                            for tag in tag_list:
                                if not tag in self.all_images_dict["searched"][key_type][img_id]:  # add tag
                                    # get last tag in category
                                    last_tag = self.get_insert_last_tags_name(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]],
                                                                         key_type, img_id,
                                                                         tag)  # i.e. the tag before the new one
                                    help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                                    # get its index on the global list
                                    glob_index = 0
                                    if last_tag:
                                        glob_index = (self.all_images_dict["searched"][key_type][img_id]).index(last_tag)
                                        glob_index += 1  # puts the pointer at end of category list

                                    help.verbose_print(f"tag:\t\t{tag}")

                                    self.all_images_dict["searched"][key_type][img_id].insert(glob_index, tag)

                                    self.all_images_dict[key_type][img_id].insert(glob_index, tag)

                                    if not img_id in self.download_tab_manager.auto_complete_config[key_type]:
                                        self.download_tab_manager.auto_complete_config[key_type][img_id] = []
                                    self.download_tab_manager.auto_complete_config[key_type][img_id].append(['+', tag, (glob_index)])

                                    # create or increment category table AND frequency table for (all) tags
                                    self.add_to_csv_dictionaries(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]], tag)  # add
            else:
                if multi_select_ckbx_state[0]:
                    ##### returns index -> [ext, img_id]
                    for index in images_selected_state:
                        ext, img_id = only_selected_state_object[index]
                        if ext in apply_to_all_type_select_checkboxgroup:
                            if img_id in list(self.all_images_dict[ext].keys()):
                                for tag in tag_list:
                                    if not tag in self.all_images_dict[ext][img_id]:
                                        # get last tag in category
                                        last_tag = self.get_insert_last_tags_name(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]],
                                                                             ext, img_id,
                                                                             tag)  # i.e. the tag before the new one
                                        help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                                        # get its index on the global list
                                        glob_index = 0
                                        if last_tag:
                                            glob_index = (self.all_images_dict[ext][img_id]).index(last_tag)
                                            glob_index += 1  # puts the pointer at end of category list

                                        self.all_images_dict[ext][img_id].insert(glob_index, tag)

                                        if not img_id in self.download_tab_manager.auto_complete_config[ext]:
                                            self.download_tab_manager.auto_complete_config[ext][img_id] = []
                                        self.download_tab_manager.auto_complete_config[ext][img_id].append(['+', tag, (glob_index)])

                                        if "searched" in self.all_images_dict and ext in self.all_images_dict[
                                            "searched"] and img_id in self.all_images_dict["searched"][ext]:
                                            self.all_images_dict["searched"][ext][img_id].insert(glob_index, tag)

                                        # create or increment category table AND frequency table for (all) tags
                                        self.add_to_csv_dictionaries(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]], tag)  # add
                else:
                    for key_type in apply_to_all_type_select_checkboxgroup:
                        for img_id in list(self.all_images_dict[key_type].keys()):
                            for tag in tag_list:
                                if not tag in self.all_images_dict[key_type][img_id]:
                                    # get last tag in category
                                    last_tag = self.get_insert_last_tags_name(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]],
                                                                         key_type, img_id,
                                                                         tag)  # i.e. the tag before the new one
                                    help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                                    # get its index on the global list
                                    glob_index = 0
                                    if last_tag:
                                        glob_index = (self.all_images_dict[key_type][img_id]).index(last_tag)
                                        glob_index += 1  # puts the pointer at end of category list

                                    self.all_images_dict[key_type][img_id].insert(glob_index, tag)

                                    if not img_id in self.download_tab_manager.auto_complete_config[key_type]:
                                        self.download_tab_manager.auto_complete_config[key_type][img_id] = []
                                    self.download_tab_manager.auto_complete_config[key_type][img_id].append(['+', tag, (glob_index)])

                                    if "searched" in self.all_images_dict and key_type in self.all_images_dict[
                                        "searched"] and img_id in self.all_images_dict["searched"][key_type]:
                                        self.all_images_dict["searched"][key_type][img_id].insert(glob_index, tag)

                                    # create or increment category table AND frequency table for (all) tags
                                    self.add_to_csv_dictionaries(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]], tag)  # add

        # find type of selected image
        temp_ext = None
        temp_all_images_dict_keys = list(self.all_images_dict.keys())
        if "searched" in temp_all_images_dict_keys:
            temp_all_images_dict_keys.remove("searched")
        for each_key in temp_all_images_dict_keys:
            if img_id in list(self.all_images_dict[each_key]):
                temp_ext = each_key
                break
        # reload the categories for the self.selected_image_dict
        self.reload_selected_image_dict(temp_ext, img_id)

        img_artist_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['artist'], value=[])
        img_character_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['character'], value=[])
        img_species_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['species'], value=[])
        img_general_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['general'], value=[])
        img_meta_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['meta'], value=[])
        img_rating_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['rating'], value=[])

        return img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group, \
               img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group, \
               new_state_of_suggestion_tag, new_state_of_suggestion_textbox

    def remove_tag_changes(self, category_tag_checkbox_group, apply_to_all_type_select_checkboxgroup, img_id,
                           multi_select_ckbx_state, only_selected_state_object, images_selected_state):

        img_artist_tag_checkbox_group = None
        img_character_tag_checkbox_group = None
        img_species_tag_checkbox_group = None
        img_general_tag_checkbox_group = None
        img_meta_tag_checkbox_group = None
        img_rating_tag_checkbox_group = None

        tag_list = category_tag_checkbox_group
        img_id = str(img_id)

        # find type of selected image
        temp_ext = None
        temp_all_images_dict_keys = list(self.all_images_dict.keys())
        if "searched" in temp_all_images_dict_keys:
            temp_all_images_dict_keys.remove("searched")
        for each_key in temp_all_images_dict_keys:
            if img_id in list(self.all_images_dict[each_key]):
                temp_ext = each_key
                break
        # reload the categories for the self.selected_image_dict
        if (len(images_selected_state) == 0 and not multi_select_ckbx_state[0]) and \
                (img_id is not None and len(img_id) > 0):
            self.reload_selected_image_dict(temp_ext, img_id)

        category_component = None
        # updates selected image ONLY when it ( IS ) specified AND its TYPE is specified for edits in "apply_to_all_type_select_checkboxgroup"
        if img_id and len(img_id) > 0 and self.selected_image_dict and self.selected_image_dict[
            "type"] in apply_to_all_type_select_checkboxgroup:
            # update info for selected image
            for tag in tag_list:
                if tag in self.selected_image_dict[img_id][self.image_board.categories_map[self.all_tags_ever_dict[tag][0]]]:
                    while tag in self.selected_image_dict[img_id][self.image_board.categories_map[self.all_tags_ever_dict[tag][0]]]:
                        self.selected_image_dict[img_id][self.image_board.categories_map[self.all_tags_ever_dict[tag][0]]].remove(tag)
            # update info for category components
            img_artist_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['artist'], value=[])
            img_character_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['character'], value=[])
            img_species_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['species'], value=[])
            img_general_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['general'], value=[])
            img_meta_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['meta'], value=[])
            img_rating_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['rating'], value=[])
            # help.verbose_print(
            #     f"self.selected_image_dict[img_id][string_category]:\t\t{self.selected_image_dict[img_id][string_category]}")
        elif img_id and len(img_id) > 0 and self.selected_image_dict and (
                not apply_to_all_type_select_checkboxgroup or len(apply_to_all_type_select_checkboxgroup) == 0):
            # update info for selected image
            for tag in tag_list:
                if tag in self.selected_image_dict[img_id][self.image_board.categories_map[self.all_tags_ever_dict[tag][0]]]:
                    while tag in self.selected_image_dict[img_id][self.image_board.categories_map[self.all_tags_ever_dict[tag][0]]]:
                        self.selected_image_dict[img_id][self.image_board.categories_map[self.all_tags_ever_dict[tag][0]]].remove(tag)
            # update info for category components
            img_artist_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['artist'], value=[])
            img_character_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['character'], value=[])
            img_species_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['species'], value=[])
            img_general_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['general'], value=[])
            img_meta_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['meta'], value=[])
            img_rating_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['rating'], value=[])
            # help.verbose_print(
            #     f"self.selected_image_dict[img_id][string_category]:\t\t{self.selected_image_dict[img_id][string_category]}")

            # find image in searched : id
            if (self.selected_image_dict["type"] in list(self.all_images_dict['searched'].keys())) and (
                    img_id in list(self.all_images_dict["searched"][self.selected_image_dict["type"]].keys())):
                for tag in tag_list:
                    if tag in self.all_images_dict["searched"][self.selected_image_dict["type"]][img_id]:
                        while tag in self.all_images_dict["searched"][self.selected_image_dict["type"]][img_id]:
                            self.all_images_dict["searched"][self.selected_image_dict["type"]][img_id].remove(tag)

                        while tag in self.all_images_dict[self.selected_image_dict["type"]][img_id]:
                            self.all_images_dict[self.selected_image_dict["type"]][img_id].remove(tag)

                            if not img_id in self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]]:
                                self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]][img_id] = []
                            self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]][img_id].append(['-', tag])

                        # create or increment category table AND frequency table for (all) tags
                        self.remove_to_csv_dictionaries(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]], tag)  # remove
            elif img_id in list(self.all_images_dict[self.selected_image_dict["type"]].keys()):  # find image in ( TYPE ) : id
                for tag in tag_list:
                    if tag in self.all_images_dict[self.selected_image_dict["type"]][img_id]:
                        while tag in self.all_images_dict[self.selected_image_dict["type"]][img_id]:
                            self.all_images_dict[self.selected_image_dict["type"]][img_id].remove(tag)

                            if not img_id in self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]]:
                                self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]][img_id] = []
                            self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]][img_id].append(['-', tag])

                        # create or increment category table AND frequency table for (all) tags
                        self.remove_to_csv_dictionaries(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]], tag)  # remove

        if len(apply_to_all_type_select_checkboxgroup) > 0:
            if "searched" in apply_to_all_type_select_checkboxgroup:  # edit searched and then all the instances of the respective types
                if multi_select_ckbx_state[0]:
                    ##### returns index -> [ext, img_id]
                    for index in images_selected_state:
                        ext, img_id = only_selected_state_object[index]
                        if ext in apply_to_all_type_select_checkboxgroup:
                            if img_id in list(self.all_images_dict["searched"][ext].keys()):
                                for tag in tag_list:
                                    if tag in self.all_images_dict["searched"][ext][img_id]:  # remove tag
                                        while tag in self.all_images_dict["searched"][ext][img_id]:
                                            self.all_images_dict["searched"][ext][img_id].remove(tag)

                                        while tag in self.all_images_dict[ext][img_id]:
                                            self.all_images_dict[ext][img_id].remove(tag)

                                            if not img_id in self.download_tab_manager.auto_complete_config[ext]:
                                                self.download_tab_manager.auto_complete_config[ext][img_id] = []
                                            self.download_tab_manager.auto_complete_config[ext][img_id].append(['-', tag])

                                        # create or increment category table AND frequency table for (all) tags
                                        self.remove_to_csv_dictionaries(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]],
                                                                   tag)  # remove
                else:
                    for key_type in list(self.all_images_dict["searched"].keys()):
                        for img_id in list(self.all_images_dict["searched"][key_type].keys()):
                            for tag in tag_list:
                                if tag in self.all_images_dict["searched"][key_type][img_id]:  # remove tag
                                    while tag in self.all_images_dict["searched"][key_type][img_id]:
                                        self.all_images_dict["searched"][key_type][img_id].remove(tag)

                                    while tag in self.all_images_dict[key_type][img_id]:
                                        self.all_images_dict[key_type][img_id].remove(tag)

                                        if not img_id in self.download_tab_manager.auto_complete_config[key_type]:
                                            self.download_tab_manager.auto_complete_config[key_type][img_id] = []
                                        self.download_tab_manager.auto_complete_config[key_type][img_id].append(['-', tag])

                                    # create or increment category table AND frequency table for (all) tags
                                    self.remove_to_csv_dictionaries(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]],
                                                               tag)  # remove
            else:
                if multi_select_ckbx_state[0]:
                    ##### returns index -> [ext, img_id]
                    for index in images_selected_state:
                        ext, img_id = only_selected_state_object[index]
                        if ext in apply_to_all_type_select_checkboxgroup:
                            if img_id in list(self.all_images_dict[ext].keys()):
                                for tag in tag_list:
                                    if tag in self.all_images_dict[ext][img_id]:
                                        while tag in self.all_images_dict[ext][img_id]:
                                            self.all_images_dict[ext][img_id].remove(tag)

                                            if not img_id in self.download_tab_manager.auto_complete_config[ext]:
                                                self.download_tab_manager.auto_complete_config[ext][img_id] = []
                                            self.download_tab_manager.auto_complete_config[ext][img_id].append(['-', tag])

                                        if "searched" in self.all_images_dict and ext in self.all_images_dict[
                                            "searched"] and img_id in self.all_images_dict["searched"][ext]:
                                            while tag in self.all_images_dict["searched"][ext][img_id]:
                                                self.all_images_dict["searched"][ext][img_id].remove(tag)

                                        # create or increment category table AND frequency table for (all) tags
                                        self.remove_to_csv_dictionaries(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]],
                                                                   tag)  # remove
                else:
                    for key_type in apply_to_all_type_select_checkboxgroup:
                        for img_id in list(self.all_images_dict[key_type].keys()):
                            for tag in tag_list:
                                if tag in self.all_images_dict[key_type][img_id]:
                                    while tag in self.all_images_dict[key_type][img_id]:
                                        self.all_images_dict[key_type][img_id].remove(tag)

                                        if not img_id in self.download_tab_manager.auto_complete_config[key_type]:
                                            self.download_tab_manager.auto_complete_config[key_type][img_id] = []
                                        self.download_tab_manager.auto_complete_config[key_type][img_id].append(['-', tag])

                                    if "searched" in self.all_images_dict and key_type in self.all_images_dict[
                                        "searched"] and img_id in self.all_images_dict["searched"][key_type]:
                                        while tag in self.all_images_dict["searched"][key_type][img_id]:
                                            self.all_images_dict["searched"][key_type][img_id].remove(tag)

                                    # create or increment category table AND frequency table for (all) tags
                                    self.remove_to_csv_dictionaries(self.image_board.categories_map[self.all_tags_ever_dict[tag][0]],
                                                               tag)  # remove

        return img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group, \
               img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group

    def remove_all(self, artist, character, species, general, meta, rating, apply_to_all_type_select_checkboxgroup,
                   img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state):
        self.remove_tag_changes(artist, apply_to_all_type_select_checkboxgroup,
                           img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state)
        self.remove_tag_changes(character, apply_to_all_type_select_checkboxgroup,
                           img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state)
        self.remove_tag_changes(species, apply_to_all_type_select_checkboxgroup,
                           img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state)
        self.remove_tag_changes(general, apply_to_all_type_select_checkboxgroup,
                           img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state)
        self.remove_tag_changes(meta, apply_to_all_type_select_checkboxgroup,
                           img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state)
        return self.remove_tag_changes(rating, apply_to_all_type_select_checkboxgroup,
                                  img_id_textbox, multi_select_ckbx_state, only_selected_state_object,
                                  images_selected_state)

    def get_category_name(self, tag):
        if tag in self.all_tags_ever_dict:
            return self.image_board.categories_map[self.all_tags_ever_dict[tag][0]]
        else:
            return None

    ### if "searched" is selected in apply_to_all_type_select_checkboxgroup, then all SEARCHED images will be deleted!
    def remove_images(self, apply_to_all_type_select_checkboxgroup, image_id, sort_images, sort_option,
                      multi_select_ckbx_state, only_selected_state_object, images_selected_state):
        image_id = str(image_id)

        if not "searched" in apply_to_all_type_select_checkboxgroup:
            if multi_select_ckbx_state[0] and len(apply_to_all_type_select_checkboxgroup) > 0:
                ##### returns index -> [ext, img_id]
                for index in images_selected_state:
                    ext, img_id = only_selected_state_object[index]
                    if ext in apply_to_all_type_select_checkboxgroup:
                        # iterate over all the tags for each image
                        for tag in self.all_images_dict[ext][img_id]:
                            category_key = self.get_category_name(tag)
                            if category_key:
                                # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
                                # edit csv dictionaries
                                self.remove_to_csv_dictionaries(category_key, tag)  # remove
                        del self.all_images_dict[ext][img_id]
                    del only_selected_state_object[index]
                images_selected_state = []
            elif multi_select_ckbx_state[0] and len(images_selected_state) == 1:
                ##### returns index -> [ext, img_id]
                for index in images_selected_state:
                    ext, img_id = only_selected_state_object[index]
                    # iterate over all the tags for each image
                    for tag in self.all_images_dict[ext][img_id]:
                        category_key = self.get_category_name(tag)
                        if category_key:
                            # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
                            # edit csv dictionaries
                            self.remove_to_csv_dictionaries(category_key, tag)  # remove
                    del self.all_images_dict[ext][img_id]
                    del only_selected_state_object[index]
                images_selected_state = []
            else:
                # remove single image ONLY
                if image_id and (self.selected_image_dict is not None):
                    image_type = self.selected_image_dict["type"]
                    if image_id in list(self.all_images_dict[image_type].keys()):
                        # remove tag count from csvs
                        category_keys = list(self.selected_image_dict[image_id].keys())
                        for category_key in category_keys:
                            for tag in self.selected_image_dict[image_id][category_key]:
                                # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
                                # edit csv dictionaries
                                self.remove_to_csv_dictionaries(category_key, tag)  # remove
                        # delete image from dictionary
                        del self.all_images_dict[self.selected_image_dict["type"]][image_id]
                    if (len(list(self.all_images_dict["searched"].keys())) > 0) and (
                            image_id in list(self.all_images_dict["searched"][self.selected_image_dict["type"]].keys())):
                        del self.all_images_dict["searched"][self.selected_image_dict["type"]][image_id]
        else:
            if multi_select_ckbx_state[0]:
                ##### returns index -> [ext, img_id]
                for index in images_selected_state:
                    ext, img_id = only_selected_state_object[index]
                    if ext in apply_to_all_type_select_checkboxgroup:
                        # delete searched images and use the global dictionary to update the CSVs before deleting those as well
                        del self.all_images_dict["searched"][ext][img_id]
                        # iterate over all the tags for each image
                        for tag in self.all_images_dict[ext][img_id]:
                            category_key = self.get_category_name(tag)
                            if category_key:
                                # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
                                # edit csv dictionaries
                                self.remove_to_csv_dictionaries(category_key, tag)  # remove
                        del self.all_images_dict[ext][img_id]
                    del only_selected_state_object[index]
                images_selected_state = []
            else:
                # remove all images that are "searched"
                for key_type in list(self.all_images_dict["searched"].keys()):
                    if key_type in apply_to_all_type_select_checkboxgroup:
                        for img_id in list(self.all_images_dict["searched"][key_type].keys()):
                            # delete searched images and use the global dictionary to update the CSVs before deleting those as well
                            del self.all_images_dict["searched"][key_type][img_id]
                            # iterate over all the tags for each image
                            for tag in self.all_images_dict[key_type][img_id]:
                                category_key = self.get_category_name(tag)
                                if category_key:
                                    # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
                                    # edit csv dictionaries
                                    self.remove_to_csv_dictionaries(category_key, tag)  # remove
                            del self.all_images_dict[key_type][img_id]

        category_comp1 = gr.update(choices=[], value=[])
        category_comp2 = gr.update(choices=[], value=[])
        category_comp3 = gr.update(choices=[], value=[])
        category_comp4 = gr.update(choices=[], value=[])
        category_comp5 = gr.update(choices=[], value=[])
        category_comp6 = gr.update(choices=[], value=[])

        # gallery update
        images = self.update_search_gallery(sort_images, sort_option)
        gallery = gr.update(value=images, visible=True)
        # textbox update
        id_box = gr.update(value="")
        return category_comp1, category_comp2, category_comp3, category_comp4, category_comp5, category_comp6, gallery, id_box, only_selected_state_object, images_selected_state

    def csv_persist_to_disk(self):
        tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                     self.download_tab_manager.settings_json["tag_count_list_folder"])
        # update csv stats files
        help.write_tags_to_csv(self.artist_csv_dict, os.path.join(tag_count_dir, "artist.csv"))
        help.write_tags_to_csv(self.character_csv_dict, os.path.join(tag_count_dir, "character.csv"))
        help.write_tags_to_csv(self.species_csv_dict, os.path.join(tag_count_dir, "species.csv"))
        help.write_tags_to_csv(self.general_csv_dict, os.path.join(tag_count_dir, "general.csv"))
        help.write_tags_to_csv(self.meta_csv_dict, os.path.join(tag_count_dir, "meta.csv"))
        help.write_tags_to_csv(self.rating_csv_dict, os.path.join(tag_count_dir, "rating.csv"))
        help.write_tags_to_csv(self.tags_csv_dict, os.path.join(tag_count_dir, "tags.csv"))

    def save_tag_changes(self):
        # do a full save of all tags
        full_path_downloads = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                           self.download_tab_manager.settings_json["downloaded_posts_folder"])
        if not self.all_images_dict or not "png" in self.all_images_dict:
            raise ValueError('radio button not pressed i.e. image type button')

        help.verbose_print(f"++++++++++++++++++++++++++")
        temp_list = list(self.all_images_dict.keys())
        help.verbose_print(f"temp_list:\t\t{temp_list}")
        # if NONE: save self (selected_image)
        # if temp_list

        if "searched" in temp_list:
            temp_list.remove("searched")
            help.verbose_print(f"removing searched key")
            help.verbose_print(f"temp_list:\t\t{temp_list}")
        for ext in temp_list:
            full_path_gallery_type = os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"{ext}_folder"])
            for img_id in list(self.all_images_dict[ext]):
                full_path = os.path.join(full_path_gallery_type, f"{img_id}.txt")
                temp_tag_string = ",".join(self.all_images_dict[ext][img_id])
                help.write_tags_to_text_file(temp_tag_string, full_path)  # update img txt file
        # persist csv changes
        self.csv_persist_to_disk()

        self.add_current_images()
        auto_config_path = os.path.join(self.cwd, "auto_configs")
        temp_config_path = os.path.join(auto_config_path, self.auto_complete_config_name)
        help.update_JSON(self.download_tab_manager.auto_complete_config, temp_config_path)
        # display stats
        png_cnt, jpg_cnt, gif_cnt, total_imgs = self.get_saved_image_count()
        help.verbose_print(f"total_imgs:\t{total_imgs}")
        help.verbose_print(f"png_cnt:\t{png_cnt}")
        help.verbose_print(f"jpg_cnt:\t{jpg_cnt}")
        help.verbose_print(f"gif_cnt:\t{gif_cnt}")
        help.verbose_print(f"SAVE COMPLETE")

    def save_image_changes(self):
        full_path_downloads = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                           self.download_tab_manager.settings_json["downloaded_posts_folder"])
        if not self.all_images_dict or not "png" in self.all_images_dict:
            raise ValueError('radio button not pressed i.e. image type button')
        help.verbose_print(f"++++++++++++++++++++++++++")
        temp_list = list(self.all_images_dict.keys())
        help.verbose_print(f"temp_list:\t\t{temp_list}")
        if "searched" in temp_list:
            temp_list.remove("searched")
            help.verbose_print(f"removing searched key")
            help.verbose_print(f"temp_list:\t\t{temp_list}")

        # persist csv changes
        self.csv_persist_to_disk()

        temp = '\\' if help.is_windows() else '/'
        for ext in temp_list:
            full_path_gallery_type = os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"{ext}_folder"])
            # type select
            images = [name.split(temp)[-1].split(".")[0] for name in glob.glob(os.path.join(full_path_gallery_type,
                                                                                            f"*.{ext}"))]  # getting the names of the files w.r.t. the directory
            for img_id in images:
                if not img_id in list(self.all_images_dict[ext]):
                    # delete img & txt files
                    os.remove(os.path.join(full_path_gallery_type, f"{img_id}.{ext}"))
                    os.remove(os.path.join(full_path_gallery_type, f"{img_id}.txt"))
                    if img_id in list(self.download_tab_manager.auto_complete_config[ext].keys()):
                        del self.download_tab_manager.auto_complete_config[ext][img_id]

        self.add_current_images()
        auto_config_path = os.path.join(self.cwd, "auto_configs")
        temp_config_path = os.path.join(auto_config_path, self.auto_complete_config_name)
        help.update_JSON(self.download_tab_manager.auto_complete_config, temp_config_path)
        # display stats
        png_cnt, jpg_cnt, gif_cnt, total_imgs = self.get_saved_image_count()
        help.verbose_print(f"total_imgs:\t{total_imgs}")
        help.verbose_print(f"png_cnt:\t{png_cnt}")
        help.verbose_print(f"jpg_cnt:\t{jpg_cnt}")
        help.verbose_print(f"gif_cnt:\t{gif_cnt}")
        help.verbose_print(f"SAVE COMPLETE")


    def load_images_handler(self, single_path, multiple_paths, image_mode_choice_state, is_batch):
        if is_batch:
            return self.custom_dataset_tab_manager.load_images(multiple_paths, image_mode_choice_state)
        else:
            return self.custom_dataset_tab_manager.load_images(single_path, image_mode_choice_state)

    def update_generated_gallery_tag_selection(self, tag_effects_dropdown: gr.SelectData, category_filter_dropdown, img_name,
                                               artist_comp_checkboxgroup, character_comp_checkboxgroup,
                                               species_comp_checkboxgroup,
                                               general_comp_checkboxgroup, meta_comp_checkboxgroup,
                                               rating_comp_checkboxgroup):
        tag_effects_dropdown = tag_effects_dropdown.value  # tag selection effect
        download_folder_type = None
        if img_name in self.all_images_dict["png"]:
            download_folder_type = "png"
        elif img_name in self.all_images_dict["jpg"]:
            download_folder_type = "jpg"
        else:
            download_folder_type = "gif"

        # load/re-load selected image
        self.reload_selected_image_dict(download_folder_type, img_name)

        all_available_tags = [[], [], [], [], [], []]
        all_available_tags[0] = self.selected_image_dict[img_name]["artist"]
        all_available_tags[1] = self.selected_image_dict[img_name]["character"]
        all_available_tags[2] = self.selected_image_dict[img_name]["species"]
        all_available_tags[3] = self.selected_image_dict[img_name]["general"]
        all_available_tags[4] = self.selected_image_dict[img_name]["meta"]
        all_available_tags[5] = self.selected_image_dict[img_name]["rating"]

        all_selected_tags = [[], [], [], [], [], []]
        all_selected_tags[0] = artist_comp_checkboxgroup
        all_selected_tags[1] = character_comp_checkboxgroup
        all_selected_tags[2] = species_comp_checkboxgroup
        all_selected_tags[3] = general_comp_checkboxgroup
        all_selected_tags[4] = meta_comp_checkboxgroup
        all_selected_tags[5] = rating_comp_checkboxgroup

        if tag_effects_dropdown is None or len(tag_effects_dropdown) == 0:
            return gr.update(choices=all_available_tags[0], value=all_selected_tags[0]), \
                   gr.update(choices=all_available_tags[1], value=all_selected_tags[1]), \
                   gr.update(choices=all_available_tags[2], value=all_selected_tags[2]), \
                   gr.update(choices=all_available_tags[3], value=all_selected_tags[3]), \
                   gr.update(choices=all_available_tags[4], value=all_selected_tags[4]), \
                   gr.update(choices=all_available_tags[5], value=all_selected_tags[5])
        else:
            for i in range(0, len(all_available_tags)):
                if "(Category) Select Any" in tag_effects_dropdown:
                    all_selected_tags[i] = [tag for tag in all_available_tags[i] if
                                            self.get_category_name(tag) in category_filter_dropdown]
                elif "(Category) Clear Any" in tag_effects_dropdown:
                    all_selected_tags[i] = [tag for tag in all_selected_tags[i] if
                                            not self.get_category_name(tag) in category_filter_dropdown]
                elif "(Category) Invert Any" in tag_effects_dropdown:
                    all_selected_tags[i] = [tag for tag in all_available_tags[i] if
                                            (not tag in all_selected_tags[i] and self.get_category_name(
                                                tag) in category_filter_dropdown) or
                                            (tag in all_selected_tags[i] and not self.get_category_name(
                                                tag) in category_filter_dropdown)]
                elif "Select All" in tag_effects_dropdown:
                    all_selected_tags[i] = [tag for tag in all_available_tags[i]]
                elif "Clear All" in tag_effects_dropdown:
                    all_selected_tags[i] = []
                elif "Invert All" in tag_effects_dropdown:
                    all_selected_tags[i] = [tag for tag in all_available_tags[i] if not tag in all_selected_tags[i]]
            return gr.update(choices=all_available_tags[0], value=all_selected_tags[0]), \
                   gr.update(choices=all_available_tags[1], value=all_selected_tags[1]), \
                   gr.update(choices=all_available_tags[2], value=all_selected_tags[2]), \
                   gr.update(choices=all_available_tags[3], value=all_selected_tags[3]), \
                   gr.update(choices=all_available_tags[4], value=all_selected_tags[4]), \
                   gr.update(choices=all_available_tags[5], value=all_selected_tags[5])





    def reset_selected_img(self, img_id_textbox):
        # reset selected_img
        self.selected_image_dict = None

        # reset img_id_textbox
        img_id_textbox = gr.update(value="")

        # reset all checkboxgroup components
        img_artist_tag_checkbox_group = gr.update(choices=[])
        img_character_tag_checkbox_group = gr.update(choices=[])
        img_species_tag_checkbox_group = gr.update(choices=[])
        img_general_tag_checkbox_group = gr.update(choices=[])
        img_meta_tag_checkbox_group = gr.update(choices=[])
        img_rating_tag_checkbox_group = gr.update(choices=[])
        return img_id_textbox, img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group, img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group

    def get_searched_image_total(self):
        total_img_count = 0
        temp_key_list = list(self.all_images_dict["searched"].keys())
        for key in temp_key_list:
            total_img_count += len(list(self.all_images_dict["searched"][key].keys()))
        return total_img_count

    def show_searched_gallery(self, folder_type_select, sort_images, sort_option):
        # type select
        if "searched" in self.all_images_dict and len(
                list(self.all_images_dict["searched"].keys())) > 0 and self.get_searched_image_total() > 0:
            images = self.update_search_gallery(sort_images, sort_option)
        else:
            help.verbose_print(f"in SHOW searched gallery")
            return self.show_gallery(folder_type_select, sort_images, sort_option)
        return gr.update(value=images, visible=True)

    def clear_categories(self):
        artist_comp_checkboxgroup = gr.update(choices=[])
        character_comp_checkboxgroup = gr.update(choices=[])
        species_comp_checkboxgroup = gr.update(choices=[])
        general_comp_checkboxgroup = gr.update(choices=[])
        meta_comp_checkboxgroup = gr.update(choices=[])
        rating_comp_checkboxgroup = gr.update(choices=[])
        return artist_comp_checkboxgroup, character_comp_checkboxgroup, species_comp_checkboxgroup, general_comp_checkboxgroup, \
               meta_comp_checkboxgroup, rating_comp_checkboxgroup, gr.update(value="")

    def set_ckbx_state(self, select_multiple_images_checkbox,
                       multi_select_ckbx_state):  # UI boolean component, JSON boolean component wrapped in a list
        multi_select_ckbx_state = [select_multiple_images_checkbox]
        return multi_select_ckbx_state

    ######
    # self.all_images_dict ->
    ### image_type -> {img_id, tags}
    ### searched -> {img_id, tags}
    ######
    def show_gallery(self, folder_type_select, sort_images, sort_option):
        help.verbose_print(f"self.download_tab_manager.is_csv_loaded:\t{self.download_tab_manager.is_csv_loaded}")

        images = []
        if folder_type_select is not None:
            help.verbose_print(f"folder_type_select:\t{folder_type_select}")
            temp = '\\' if help.is_windows() else '/'
            # clear searched dict
            if "searched" in self.all_images_dict:
                del self.all_images_dict["searched"]
                self.all_images_dict["searched"] = {}

            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json[f"{folder_type_select}_folder"])

            help.verbose_print(f"folder_path:\t{folder_path}")

            # type select : re-load images
            help.verbose_print(f"self.all_images_dict is None:\t{self.all_images_dict is None}")
            if not self.all_images_dict or len(self.all_images_dict.keys()) == 0 or \
                    (folder_type_select in self.all_images_dict.keys() and len(self.all_images_dict[folder_type_select].keys()) == 0) or \
                    not self.download_tab_manager.is_csv_loaded:
                images = glob.glob(os.path.join(folder_path, f"*.{folder_type_select}"))
                help.verbose_print(f"images:\t{images}")
            else: # render from existing dictionary
                for name in list(self.all_images_dict[folder_type_select].keys()):
                    images.append(os.path.join(folder_path, f"{str(name)}.{folder_type_select}"))

            if not self.download_tab_manager.is_csv_loaded:
                full_path_downloads = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                                   self.download_tab_manager.settings_json["downloaded_posts_folder"])

                tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                             self.download_tab_manager.settings_json["tag_count_list_folder"])


                if not self.all_images_dict or len(self.all_images_dict.keys()) == 0 or \
                    not self.download_tab_manager.is_csv_loaded:
                    self.all_images_dict = help.merge_dict(os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"png_folder"]),
                                                      os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"jpg_folder"]),
                                                      os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"gif_folder"]))

                # loading images
                self.add_current_images()

                # load ALL tags into relative categorical dictionaries
                self.download_tab_manager.is_csv_loaded = True
                self.artist_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "artist.csv"))
                self.character_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "character.csv"))
                self.species_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "species.csv"))
                self.general_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "general.csv"))
                self.meta_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "meta.csv"))
                self.rating_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "rating.csv"))
                self.tags_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "tags.csv"))





                # populate the timekeeping dictionary
                self.initialize_posts_timekeeper()

                # verbose_print(f"self.all_images_dict:\t\t{self.all_images_dict}")
                # help.verbose_print(f"list(self.all_images_dict[ext]):\t\t{list(self.all_images_dict[folder_type_select])}")

            if sort_images and len(sort_option) > 0 and len(list(self.image_creation_times.keys())) > 0:
                # parse to img_id -> to get the year
                if sort_option == "new-to-old":
                    images = sorted(images, key=lambda x: self.image_creation_times.get(((x.split(temp)[-1]).split(".")[0]),
                                                                                   float('-inf')),
                                    reverse=True)
                elif sort_option == "old-to-new":
                    images = sorted(images, key=lambda x: self.image_creation_times.get(((x.split(temp)[-1]).split(".")[0]),
                                                                                   float('-inf')))
            # help.verbose_print(f"images:\t{images}")
        return gr.update(value=images, visible=True)

    def extract_name_and_extention(self, gallery_comp_path):
        # help.verbose_print(f"gallery_comp_path:\t\t{gallery_comp_path}")
        temp = '\\' if help.is_windows() else '/'
        gallery_comp_path = gallery_comp_path.split(temp)[-1]  # name w/ extn
        download_folder_type = gallery_comp_path.split(".")[-1]  # get ext type
        # help.verbose_print(f"download_folder_type:\t\t{download_folder_type}")
        # help.verbose_print(f"----->\t\t{download_folder_type}_folder")
        gallery_comp_path = gallery_comp_path.replace(f".{download_folder_type}", ".txt")
        img_name = gallery_comp_path.split(f".txt")[0]
        img_name = str(img_name)
        return [download_folder_type, img_name]

    ### Select an image
    def get_img_tags(self, gallery_comp, select_multiple_images_checkbox, images_selected_state,
                     select_between_images_checkbox, images_tuple_points, event_data: gr.SelectData):
        # self.selected_image_dict  # id -> {categories: tag/s}, type -> string
        temp = '\\' if help.is_windows() else '/'
        help.verbose_print(f"event_data:\t{event_data}")
        help.verbose_print(f"event_data.index:\t{event_data.index}")
        help.verbose_print(f"gallery_comp[event_data.index]:\t{gallery_comp[event_data.index]}")
        help.verbose_print(f"full_path:\t{(gallery_comp[event_data.index])[0]}")
        help.verbose_print(f"image name:\t{(gallery_comp[event_data.index])[0].split(temp)[-1]}")

        img_name = None
        artist_comp_checkboxgroup = gr.update(choices=[])
        character_comp_checkboxgroup = gr.update(choices=[])
        species_comp_checkboxgroup = gr.update(choices=[])
        general_comp_checkboxgroup = gr.update(choices=[])
        meta_comp_checkboxgroup = gr.update(choices=[])
        rating_comp_checkboxgroup = gr.update(choices=[])

        if select_multiple_images_checkbox:
            if (event_data.index in images_selected_state):  # toggles images clicked
                images_selected_state.pop(images_selected_state.index(event_data.index))
            else:
                images_selected_state.append(event_data.index)

            if select_between_images_checkbox:  # select/unselect all in-between n-1 & n
                if len(images_tuple_points) < 1:
                    images_tuple_points.append(event_data.index)
                    help.verbose_print(f"images_tuple_points:\t{images_tuple_points}")
                else:
                    images_tuple_points.append(event_data.index)
                    images_tuple_points = sorted(images_tuple_points)  # small to large
                    help.verbose_print(f"images_tuple_points:\t{images_tuple_points}")
                    # temp removal
                    for point in images_tuple_points:
                        images_selected_state.pop(images_selected_state.index(point))
                    # toggle overlapping repectively
                    # a-b|b-a
                    set_a = set(images_selected_state)
                    set_b = set([x for x in range(images_tuple_points[0], images_tuple_points[1] + 1, 1)])
                    set_c = (set_a - set_b) | (set_b - set_a)
                    images_selected_state = list(set_c)
                    images_tuple_points = []

            help.verbose_print(f"images_selected_states:\t{images_selected_state}")
        else:
            images_selected_state = []
            download_folder_type, img_name = self.extract_name_and_extention((gallery_comp[event_data.index])[0])# requires full path; returns [ext, img_id]

            help.verbose_print(f"download_folder_type:\t{download_folder_type}")
            help.verbose_print(f"img_name:\t{img_name}")

            # if image name is not in the global dictionary --- then reload the gallery before loading the tags
            temp_all_images_dict_keys = list(self.all_images_dict.keys())
            if "searched" in temp_all_images_dict_keys:
                temp_all_images_dict_keys.remove("searched")

            ### POPULATE all categories for selected image
            if not self.all_images_dict:
                raise ValueError('radio button not pressed i.e. image type button')

            # load/re-load selected image
            self.reload_selected_image_dict(download_folder_type, img_name)

            artist_comp_checkboxgroup = gr.update(choices=self.selected_image_dict[img_name]["artist"])
            character_comp_checkboxgroup = gr.update(choices=self.selected_image_dict[img_name]["character"])
            species_comp_checkboxgroup = gr.update(choices=self.selected_image_dict[img_name]["species"])
            general_comp_checkboxgroup = gr.update(choices=self.selected_image_dict[img_name]["general"])
            meta_comp_checkboxgroup = gr.update(choices=self.selected_image_dict[img_name]["meta"])
            rating_comp_checkboxgroup = gr.update(choices=self.selected_image_dict[img_name]["rating"])

        only_selected_state_object = dict()
        for index in images_selected_state:
            only_selected_state_object[index] = self.extract_name_and_extention((gallery_comp[index])[0])  # returns index -> [ext, img_id]
        help.verbose_print(f"only_selected_state_object:\t{only_selected_state_object}")

        return gr.update(
            value=img_name), artist_comp_checkboxgroup, character_comp_checkboxgroup, species_comp_checkboxgroup, \
               general_comp_checkboxgroup, meta_comp_checkboxgroup, rating_comp_checkboxgroup, images_selected_state, only_selected_state_object, \
               images_tuple_points

    ######
    # self.all_images_dict ->
    ### image_type -> {img_id, tags}
    ### searched -> {img_id, tags}
    ######
    def force_reload_show_gallery(self, folder_type_select, sort_images, sort_option):
        help.verbose_print(f"folder_type_select:\t{folder_type_select}")
        temp = '\\' if help.is_windows() else '/'
        # clear searched dict
        if "searched" in self.all_images_dict:
            del self.all_images_dict["searched"]
            self.all_images_dict["searched"] = {}

        folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json[f"{folder_type_select}_folder"])

        help.verbose_print(f"folder_path:\t{folder_path}")

        # type select
        images = []
        if not self.all_images_dict or len(self.all_images_dict.keys()) == 0 or \
                    (folder_type_select in self.all_images_dict.keys() and len(self.all_images_dict[folder_type_select].keys()) == 0) or \
                    not self.download_tab_manager.is_csv_loaded:
            images = glob.glob(os.path.join(folder_path, f"*.{folder_type_select}"))
        else:
            for name in list(self.all_images_dict[folder_type_select].keys()):
                images.append(os.path.join(folder_path, f"{str(name)}.{folder_type_select}"))

        self.download_tab_manager.is_csv_loaded = False

        if not self.download_tab_manager.is_csv_loaded:
            full_path_downloads = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                               self.download_tab_manager.settings_json["downloaded_posts_folder"])

            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])

            if not self.all_images_dict or len(self.all_images_dict.keys()) == 0 or \
                    not self.download_tab_manager.is_csv_loaded:
                self.all_images_dict = help.merge_dict(os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"png_folder"]),
                                                  os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"jpg_folder"]),
                                                  os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"gif_folder"]))

            # loading images
            self.add_current_images()

            # load ALL tags into relative categorical dictionaries
            self.download_tab_manager.is_csv_loaded = True
            self.artist_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "artist.csv"))
            self.character_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "character.csv"))
            self.species_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "species.csv"))
            self.general_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "general.csv"))
            self.meta_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "meta.csv"))
            self.rating_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "rating.csv"))
            self.tags_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "tags.csv"))



            # populate the timekeeping dictionary
            self.initialize_posts_timekeeper()

            # verbose_print(f"self.all_images_dict:\t\t{self.all_images_dict}")
            # help.verbose_print(f"list(self.all_images_dict[ext]):\t\t{list(self.all_images_dict[folder_type_select])}")

        if sort_images and len(sort_option) > 0 and len(list(self.image_creation_times.keys())) > 0:
            # parse to img_id -> to get the year
            if sort_option == "new-to-old":
                images = sorted(images, key=lambda x: self.image_creation_times.get(((x.split(temp)[-1]).split(".")[0]),
                                                                               float('-inf')),
                                reverse=True)
            elif sort_option == "old-to-new":
                images = sorted(images, key=lambda x: self.image_creation_times.get(((x.split(temp)[-1]).split(".")[0]),
                                                                               float('-inf')))

        # help.verbose_print(f"images:\t{images}")
        return gr.update(value=images, visible=True)

    def reset_gallery_component_only(self):
        return gr.update(value=[], visible=True)

    def reset_gallery_manager(self):
        download_folder_type = gr.update(value=None)
        img_id_textbox = gr.update(value="")
        tag_search_textbox = gr.update(value="")
        tag_search_suggestion_dropdown = gr.update(value=None)
        apply_to_all_type_select_checkboxgroup = gr.update(value=[])
        select_multiple_images_checkbox = gr.update(value=False)
        select_between_images_checkbox = gr.update(value=False)
        apply_datetime_sort_ckbx = gr.update(value=False)
        apply_datetime_choice_menu = gr.update(value=None)
        send_img_from_gallery_dropdown = gr.update(value=None)
        batch_send_from_gallery_checkbox = gr.update(value=False)
        tag_add_textbox = gr.update(value="")
        tag_add_suggestion_dropdown = gr.update(value=None)
        category_filter_gallery_dropdown = gr.update(value=None)
        tag_effects_gallery_dropdown = gr.update(value=None)
        img_artist_tag_checkbox_group = gr.update(value=[])
        img_character_tag_checkbox_group = gr.update(value=[])
        img_species_tag_checkbox_group = gr.update(value=[])
        img_general_tag_checkbox_group = gr.update(value=[])
        img_meta_tag_checkbox_group = gr.update(value=[])
        img_rating_tag_checkbox_group = gr.update(value=[])
        gallery_comp = gr.update(value=None)

        self.multi_select_ckbx_state = gr.JSON([False], visible=False) # JSON boolean component wrapped in a list
        self.only_selected_state_object = gr.State(dict()) # state of image mappings represented by index -> [ext, img_id]
        self.images_selected_state = gr.JSON([], visible=False) # JSON list of image ids in the gallery
        self.images_tuple_points = gr.JSON([], visible=False) # JSON list of all images selected given by two points: a-b|b-a
        self.selected_image_dict = {}
        self.download_tab_manager.is_csv_loaded = False

        self.load_images_and_csvs()
        self.all_images_dict = {} # DONE TO ENSURE gallery loads images properly
        self.download_tab_manager.is_csv_loaded = False # DONE TO ENSURE gallery loads images properly

        return [
                download_folder_type,
                img_id_textbox,
                tag_search_textbox,
                tag_search_suggestion_dropdown,
                apply_to_all_type_select_checkboxgroup,
                select_multiple_images_checkbox,
                select_between_images_checkbox,
                apply_datetime_sort_ckbx,
                apply_datetime_choice_menu,
                send_img_from_gallery_dropdown,
                batch_send_from_gallery_checkbox,
                tag_add_textbox,
                tag_add_suggestion_dropdown,
                category_filter_gallery_dropdown,
                tag_effects_gallery_dropdown,
                img_artist_tag_checkbox_group,
                img_character_tag_checkbox_group,
                img_species_tag_checkbox_group,
                img_general_tag_checkbox_group,
                img_meta_tag_checkbox_group,
                img_rating_tag_checkbox_group,
                gallery_comp
                ]


    def remove_from_all(self, file_path, apply_to_all_type_select_checkboxgroup):
        # gather the tags
        all_tags = help.get_text_file_data(file_path, 1)
        all_tags = [x.rstrip('\n') for x in all_tags]
        help.verbose_print(f"all_tags:\t{all_tags}")

        # load the csvs if not already loaded and the image dictionaries
        self.load_images_and_csvs()

        all_keys_temp = list(self.all_images_dict.keys())
        search_flag = False
        all_keys_temp.remove("searched")
        if "searched" in apply_to_all_type_select_checkboxgroup:
            search_flag = True

        # update the csvs and global dictionaries
        searched_keys_temp = list(self.all_images_dict["searched"].keys())
        for tag in all_tags:
            category_key = self.get_category_name(tag)
            if category_key:
                # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
                # edit csv dictionaries
                self.remove_to_csv_dictionaries(category_key, tag)  # remove
            # update all the image text files
            searched_ids_list = list(self.all_images_dict["searched"].keys())
            for img_type in all_keys_temp:
                searched_img_id_keys_temp = None
                if img_type in searched_ids_list:
                    searched_img_id_keys_temp = list(self.all_images_dict["searched"][img_type].keys())
                else:
                    searched_img_id_keys_temp = list(self.all_images_dict[img_type].keys())

                for every_image in list(self.all_images_dict[img_type].keys()):
                    if tag in self.all_images_dict[img_type][every_image]:
                        while tag in self.all_images_dict[img_type][every_image]:
                            self.all_images_dict[img_type][every_image].remove(tag)
                            if search_flag and img_type in searched_keys_temp and every_image in searched_img_id_keys_temp:
                                if img_type in searched_ids_list:
                                    self.all_images_dict["searched"][img_type][every_image].remove(tag)

                            if not every_image in self.download_tab_manager.auto_complete_config[img_type]:
                                self.download_tab_manager.auto_complete_config[img_type][every_image] = []
                            self.download_tab_manager.auto_complete_config[img_type][every_image].append(['-', tag])
        # persist changes
        self.csv_persist_to_disk()
        full_path_downloads = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                           self.download_tab_manager.settings_json["downloaded_posts_folder"])

        for ext in all_keys_temp:
            for img_id in list(self.all_images_dict[ext].keys()):
                full_path_gallery_type = os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"{ext}_folder"])
                full_path = os.path.join(full_path_gallery_type, f"{img_id}.txt")
                temp_tag_string = ",".join(self.all_images_dict[ext][img_id])
                help.write_tags_to_text_file(temp_tag_string, full_path)  # update img txt file

        self.add_current_images()
        self.auto_config_path = os.path.join(self.cwd, "auto_configs")
        temp_config_path = os.path.join(self.auto_config_path, self.auto_complete_config_name)
        help.update_JSON(self.download_tab_manager.auto_complete_config, temp_config_path)

        help.verbose_print("Done")


    def replace_from_all(self, file_path, apply_to_all_type_select_checkboxgroup):
        # gather the (keyword, tag/s) pairs
        all_tags = help.get_text_file_data(file_path, 2)

        for i in range(0, len(all_tags)):
            all_tags[i][0] = all_tags[i][0].rstrip('\n')
            for j in range(0, len(all_tags[i][1])):
                all_tags[i][1][j] = all_tags[i][1][j].rstrip('\n')

        help.verbose_print(f"all_tags:\t{all_tags}")

        # load the csvs if not already loaded and the image dictionaries
        self.load_images_and_csvs()

        all_keys_temp = list(self.all_images_dict.keys())
        search_flag = False
        all_keys_temp.remove("searched")
        if "searched" in apply_to_all_type_select_checkboxgroup:
            search_flag = True

        # update the csvs
        searched_keys_temp = list(self.all_images_dict["searched"].keys())
        for tag, replacement_tags in all_tags:
            category_key = self.get_category_name(tag)
            if category_key:
                help.verbose_print(
                    f"category_key:\t{category_key}\tand\ttag:\t{tag}\tand\treplacement_tags:\t{replacement_tags}")
                # edit csv dictionaries
                self.remove_to_csv_dictionaries(category_key, tag)  # remove
            for replacement_tag in replacement_tags:
                category_key = self.get_category_name(replacement_tag)
                # "SKIP" (do not add into csvs) if None
                if category_key:
                    self.add_to_csv_dictionaries(category_key, replacement_tag)  # add
            # update all the image text files
            searched_ids_list = list(self.all_images_dict["searched"].keys())
            for img_type in all_keys_temp:
                searched_img_id_keys_temp = None
                if img_type in searched_ids_list:
                    searched_img_id_keys_temp = list(self.all_images_dict["searched"][img_type].keys())
                else:
                    searched_img_id_keys_temp = list(self.all_images_dict[img_type].keys())

                for every_image in list(self.all_images_dict[img_type].keys()):
                    if tag in self.all_images_dict[img_type][every_image]:
                        # get index of keyword
                        index = (self.all_images_dict[img_type][every_image]).index(tag)
                        self.all_images_dict[img_type][every_image].remove(tag)  ############ consider repeats present
                        if search_flag and img_type in searched_keys_temp and every_image in searched_img_id_keys_temp:
                            if img_type in searched_ids_list:
                                self.all_images_dict["searched"][img_type][every_image].remove(tag)

                        if not every_image in self.download_tab_manager.auto_complete_config[img_type]:
                            self.download_tab_manager.auto_complete_config[img_type][every_image] = []
                        self.download_tab_manager.auto_complete_config[img_type][every_image].append(['-', tag])

                        for i in range(0, len(replacement_tags)):
                            self.all_images_dict[img_type][every_image].insert((index + i), replacement_tags[i])
                            if search_flag and img_type in searched_keys_temp and every_image in searched_img_id_keys_temp:
                                if img_type in searched_ids_list:
                                    self.all_images_dict["searched"][img_type][every_image].insert((index + i),
                                                                                              replacement_tags[i])

                            if not every_image in self.download_tab_manager.auto_complete_config[img_type]:
                                self.download_tab_manager.auto_complete_config[img_type][every_image] = []
                            self.download_tab_manager.auto_complete_config[img_type][every_image].append(['+', replacement_tags[i], (index + i)])
        # persist changes
        self.csv_persist_to_disk()
        full_path_downloads = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                           self.download_tab_manager.settings_json["downloaded_posts_folder"])
        for ext in all_keys_temp:
            for img_id in list(self.all_images_dict[ext].keys()):
                full_path_gallery_type = os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"{ext}_folder"])
                full_path = os.path.join(full_path_gallery_type, f"{img_id}.txt")
                temp_tag_string = ",".join(self.all_images_dict[ext][img_id])
                help.write_tags_to_text_file(temp_tag_string, full_path)  # update img txt file

        self.add_current_images()
        self.auto_config_path = os.path.join(self.cwd, "auto_configs")
        temp_config_path = os.path.join(self.auto_config_path, self.auto_complete_config_name)
        help.update_JSON(self.download_tab_manager.auto_complete_config, temp_config_path)

        help.verbose_print("Done")

    def prepend_with_keyword(self, keyword_search_text, prepend_text, prepend_option, apply_to_all_type_select_checkboxgroup):
        if not prepend_text or prepend_text == "":
            raise ValueError('REPLACEMENT TEXT and/or TAG/S MUST BE SPECIFIED!\n'
                             'tags can be removed with the text file and/or manually in the preview gallery tab.')

        prepend_tags = (prepend_text.replace(" ", "")).split(",")

        # load the csvs if not already loaded and the image dictionaries
        self.load_images_and_csvs()

        all_keys_temp = list(self.all_images_dict.keys())
        search_flag = False
        all_keys_temp.remove("searched")
        if "searched" in apply_to_all_type_select_checkboxgroup:
            search_flag = True

        # update the csvs
        if keyword_search_text and not keyword_search_text == "":
            category_key = self.get_category_name(keyword_search_text)
            if category_key:
                help.verbose_print(
                    f"category_key:\t{category_key}\tand\tkeyword_search_text:\t{keyword_search_text}\tand\tprepend_tags:\t{prepend_tags}")
                # edit csv dictionaries
                # add_to_csv_dictionaries(category_key, keyword_search_text) # add
        for prepend_tag in prepend_tags:
            category_key = self.get_category_name(prepend_tag)
            # "SKIP" (do not add into csvs) if None
            if category_key:
                self.add_to_csv_dictionaries(category_key, prepend_tag)  # add
        # update all the image text files
        searched_keys_temp = list(self.all_images_dict["searched"].keys())
        for img_type in all_keys_temp:
            searched_img_id_keys_temp = list(self.all_images_dict["searched"][img_type].keys())
            for every_image in list(self.all_images_dict[img_type].keys()):
                if keyword_search_text and not keyword_search_text == "":
                    if keyword_search_text in self.all_images_dict[img_type][every_image]:
                        # get index of keyword
                        index = (self.all_images_dict[img_type][every_image]).index(keyword_search_text)
                        if prepend_option == "End":
                            index += 1
                        for i in range(0, len(prepend_tags)):
                            self.all_images_dict[img_type][every_image].insert((index + i), prepend_tags[i])
                            if search_flag and img_type in searched_keys_temp and every_image in searched_img_id_keys_temp:
                                self.all_images_dict["searched"][img_type][every_image].insert((index + i), prepend_tags[i])

                            if not every_image in self.download_tab_manager.auto_complete_config[img_type]:
                                self.download_tab_manager.auto_complete_config[img_type][every_image] = []
                            self.download_tab_manager.auto_complete_config[img_type][every_image].append(['+', prepend_tags[i], (index + i)])
                else:
                    if prepend_option == "Start":
                        for i in range(0, len(prepend_tags)):
                            self.all_images_dict[img_type][every_image].insert(i, prepend_tags[i])
                            if search_flag and img_type in searched_keys_temp and every_image in searched_img_id_keys_temp:
                                self.all_images_dict["searched"][img_type][every_image].insert(i, prepend_tags[i])

                            if not every_image in self.download_tab_manager.auto_complete_config[img_type]:
                                self.download_tab_manager.auto_complete_config[img_type][every_image] = []
                            self.download_tab_manager.auto_complete_config[img_type][every_image].append(['+', prepend_tags[i], (i)])
                    else:
                        for i in range(0, len(prepend_tags)):
                            self.all_images_dict[img_type][every_image].append(prepend_tags[i])
                            if search_flag and img_type in searched_keys_temp and every_image in searched_img_id_keys_temp:
                                self.all_images_dict["searched"][img_type][every_image].append(prepend_tags[i])

                            if not every_image in self.download_tab_manager.auto_complete_config[img_type]:
                                self.download_tab_manager.auto_complete_config[img_type][every_image] = []
                            self.download_tab_manager.auto_complete_config[img_type][every_image].append(
                                ['+', prepend_tags[i], (self.all_images_dict[img_type][every_image]) - 1])
        # persist changes
        self.csv_persist_to_disk()
        full_path_downloads = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                           self.download_tab_manager.settings_json["downloaded_posts_folder"])
        for ext in all_keys_temp:
            for img_id in list(self.all_images_dict[ext].keys()):
                full_path_gallery_type = os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"{ext}_folder"])
                full_path = os.path.join(full_path_gallery_type, f"{img_id}.txt")
                temp_tag_string = ",".join(self.all_images_dict[ext][img_id])
                help.write_tags_to_text_file(temp_tag_string, full_path)  # update img txt file

        self.add_current_images()
        self.auto_config_path = os.path.join(self.cwd, "auto_configs")
        temp_config_path = os.path.join(self.auto_config_path, self.auto_complete_config_name)
        help.update_JSON(self.download_tab_manager.auto_complete_config, temp_config_path)

        help.verbose_print("Done")









    def render_tab(self):
        with gr.Tab("Tag Editor & Image Gallery"):
            tab_selection = ["Auto-Tag Model", "Image Default Editor", "Image Crop Editor", "Image Sketch Editor",
                             "Image Color Sketch Editor"]
            tag_selection_list = ["(Category) Select Any", "(Category) Clear Any", "(Category) Invert Any",
                                  "Select All", "Clear All", "Invert All"]

            gr.Markdown(md_.preview)
            with gr.Row():
                with gr.Column():
                    with gr.Row():
                        with gr.Column(elem_id="trim_row_length"):
                            gr.Markdown("""Reload Gallery""", elem_id="trim_markdown_length")
                            refresh_symbol = '\U0001f504'  # 🔄
                            refresh_aspect_btn = gr.Button(value=refresh_symbol, variant="variant",
                                                           elem_id="refresh_aspect_btn")
                        download_folder_type = gr.Radio(choices=self.file_extn_list, label='Select Filename Type')
                        img_id_textbox = gr.Textbox(label="Image ID", interactive=False, lines=1, value="")
                    with gr.Accordion("Image Sort & Selection Options"):
                        with gr.Row():
                            with gr.Column(min_width=50, scale=3):
                                tag_search_textbox = gr.Textbox(
                                    label="Search Tags (E.G. tag1 -tag2 shows images with tag1 but without tag2)",
                                    lines=1, value="")
                            with gr.Column(min_width=50, scale=2):
                                tag_search_suggestion_dropdown = gr.Dropdown(label="Tag Suggestions", container=True,
                                                                             choices=[], interactive=True,
                                                                             elem_id="searchbar_dropdown")
                        with gr.Row():
                            with gr.Column(min_width=50, scale=3):
                                apply_to_all_type_select_checkboxgroup = gr.CheckboxGroup(
                                    choices=["png", "jpg", "gif", "searched"],
                                    label=f'Apply\'s to ALL of {["png", "jpg", "gif", "searched"]} type', value=[])
                            with gr.Column(min_width=50, scale=1):
                                select_multiple_images_checkbox = gr.Checkbox(label="Multi-Select", value=False,
                                                                              info="Click Image/s")
                            with gr.Column(min_width=50, scale=1):
                                select_between_images_checkbox = gr.Checkbox(label="Shift-Select", value=False,
                                                                             info="Selects All Between Two Images")
                        with gr.Row():
                            with gr.Column(min_width=50, scale=1):
                                apply_datetime_sort_ckbx = gr.Checkbox(label="Sort", value=False,
                                                                       info="Image/s by date")
                            with gr.Column(min_width=50, scale=4):
                                apply_datetime_choice_menu = gr.Dropdown(label="Sort Order",
                                                                         choices=["new-to-old", "old-to-new"], value=None,
                                                                         info="Image/s by date")
                        with gr.Row():
                            image_remove_button = gr.Button(value="Remove Selected Image/s", variant='primary')
                            image_save_ids_button = gr.Button(value="Save Image Changes", variant='primary')
                        with gr.Row():
                            with gr.Column(min_width=50, scale=2):
                                send_img_from_gallery_dropdown = gr.Dropdown(label="Image to Tab Selector",
                                                                             choices=tab_selection)
                            with gr.Column(min_width=50, scale=1):
                                batch_send_from_gallery_checkbox = gr.Checkbox(label="Send as Batch")
                            with gr.Column(min_width=50, scale=3):
                                send_img_from_gallery_button = gr.Button(value="Send Image to (Other) Tab",
                                                                         variant='primary')

                    with gr.Accordion("Tag Edit & Selection Options"):
                        with gr.Row():
                            with gr.Column(min_width=50, scale=1):
                                year_remove_button = gr.Button(value="(Global) Remove Year Tag/s", variant='secondary')
                            with gr.Column(min_width=50, scale=1):
                                tag_remove_button = gr.Button(value="Remove Selected Tag/s", variant='primary')
                            with gr.Column(min_width=50, scale=1):
                                tag_save_button = gr.Button(value="Save Tag Changes", variant='primary')
                        with gr.Row():
                            tag_add_textbox = gr.Textbox(label="Enter Tag/s here", lines=1, value="",
                                                         info="Press Enter/Space to ADD tag/s")
                            tag_add_suggestion_dropdown = gr.Dropdown(label="Tag Suggestions", container=True,
                                                                      choices=[], interactive=True,
                                                                      elem_id="add_tag_dropdown")
                        with gr.Row():
                            with gr.Column(min_width=50, scale=3):
                                category_filter_gallery_dropdown = gr.Dropdown(
                                    label="Filter by Category (Multi-Select Enabled)",
                                    choices=list(self.image_board.categories_map.values()), multiselect=True)
                            with gr.Column(min_width=50, scale=1):
                                tag_effects_gallery_dropdown = gr.Dropdown(label="Tag Selector Effect/s",
                                                                           choices=tag_selection_list, interactive=True)

                        img_artist_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Artist Tag/s', value=[])
                        img_character_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Character Tag/s',
                                                                            value=[])
                        img_species_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Species Tag/s', value=[])
                        img_general_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='General Tag/s', value=[])
                        img_meta_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Meta Tag/s', value=[])
                        img_rating_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Rating Tag/s', value=[])
                    with gr.Accordion("Advanced (Valid) Tag Options", open=False):
                        with gr.Row():
                            gr.Info(message="Uses file_type selection CheckBoxGroup at top of page to select which images are affected")
                        with gr.Row():
                            remove_tags_list = gr.Textbox(lines=1, label='Path to remove tags file',
                                                          value=self.download_tab_manager.settings_json["remove_tags_list"])
                            replace_tags_list = gr.Textbox(lines=1, label='Path to replace tags file',
                                                           value=self.download_tab_manager.settings_json["replace_tags_list"])
                        with gr.Row():
                            remove_now_button = gr.Button(value="Remove Now", variant='primary')
                            replace_now_button = gr.Button(value="Replace Now", variant='primary')
                        with gr.Row():
                            keyword_search_text = gr.Textbox(lines=1, label='Keyword/Tag to Search (Optional)')
                            prepend_text = gr.Textbox(lines=1, label='Text to Prepend')
                            prepend_option = gr.Radio(choices=["Start", "End"], label='Prepend/Append Text To:',
                                                      value="Start")
                        with gr.Row():
                            prepend_now_button = gr.Button(value="Prepend/Append Now", variant='primary')
                gallery_comp = gr.Gallery(visible=False, elem_id="gallery_id", object_fit="contain", interactive=True, columns=3, height=1356,
                         elem_classes="custom-gallery")

        self.refresh_aspect_btn = refresh_aspect_btn
        self.download_folder_type = download_folder_type
        self.img_id_textbox = img_id_textbox
        self.tag_search_textbox = tag_search_textbox
        self.tag_search_suggestion_dropdown = tag_search_suggestion_dropdown
        self.apply_to_all_type_select_checkboxgroup = apply_to_all_type_select_checkboxgroup
        self.select_multiple_images_checkbox = select_multiple_images_checkbox
        self.select_between_images_checkbox = select_between_images_checkbox
        self.apply_datetime_sort_ckbx = apply_datetime_sort_ckbx
        self.apply_datetime_choice_menu = apply_datetime_choice_menu
        self.image_remove_button = image_remove_button
        self.image_save_ids_button = image_save_ids_button
        self.send_img_from_gallery_dropdown = send_img_from_gallery_dropdown
        self.batch_send_from_gallery_checkbox = batch_send_from_gallery_checkbox
        self.send_img_from_gallery_button = send_img_from_gallery_button
        self.tag_remove_button = tag_remove_button
        self.tag_save_button = tag_save_button
        self.tag_add_textbox = tag_add_textbox
        self.tag_add_suggestion_dropdown = tag_add_suggestion_dropdown
        self.category_filter_gallery_dropdown = category_filter_gallery_dropdown
        self.tag_effects_gallery_dropdown = tag_effects_gallery_dropdown
        self.img_artist_tag_checkbox_group = img_artist_tag_checkbox_group
        self.img_character_tag_checkbox_group = img_character_tag_checkbox_group
        self.img_species_tag_checkbox_group = img_species_tag_checkbox_group
        self.img_general_tag_checkbox_group = img_general_tag_checkbox_group
        self.img_meta_tag_checkbox_group = img_meta_tag_checkbox_group
        self.img_rating_tag_checkbox_group = img_rating_tag_checkbox_group
        self.gallery_comp = gallery_comp
        self.year_remove_button = year_remove_button
        self.remove_tags_list = remove_tags_list
        self.replace_tags_list = replace_tags_list
        self.remove_now_button = remove_now_button
        self.replace_now_button = replace_now_button
        self.keyword_search_text = keyword_search_text
        self.prepend_text = prepend_text
        self.prepend_option = prepend_option
        self.prepend_now_button = prepend_now_button

        return [
                self.refresh_aspect_btn,
                self.download_folder_type,
                self.img_id_textbox,
                self.tag_search_textbox,
                self.tag_search_suggestion_dropdown,
                self.apply_to_all_type_select_checkboxgroup,
                self.select_multiple_images_checkbox,
                self.select_between_images_checkbox,
                self.apply_datetime_sort_ckbx,
                self.apply_datetime_choice_menu,
                self.image_remove_button,
                self.image_save_ids_button,
                self.send_img_from_gallery_dropdown,
                self.batch_send_from_gallery_checkbox,
                self.send_img_from_gallery_button,
                self.tag_remove_button,
                self.tag_save_button,
                self.tag_add_textbox,
                self.tag_add_suggestion_dropdown,
                self.category_filter_gallery_dropdown,
                self.tag_effects_gallery_dropdown,
                self.img_artist_tag_checkbox_group,
                self.img_character_tag_checkbox_group,
                self.img_species_tag_checkbox_group,
                self.img_general_tag_checkbox_group,
                self.img_meta_tag_checkbox_group,
                self.img_rating_tag_checkbox_group,
                self.gallery_comp,
                self.year_remove_button,
                self.remove_tags_list,
                self.replace_tags_list,
                self.remove_now_button,
                self.replace_now_button,
                self.keyword_search_text,
                self.prepend_text,
                self.prepend_option,
                self.prepend_now_button
                ]

    def get_event_listeners(self):
        self.year_remove_button.click(
            fn=self.remove_all,
            inputs=[
                self.img_artist_tag_checkbox_group,
                self.img_character_tag_checkbox_group,
                self.img_species_tag_checkbox_group,
                self.img_general_tag_checkbox_group,
                gr.State([str(year) for year in range(2000,2025,1)]),
                self.img_rating_tag_checkbox_group,
                gr.State(["png", "jpg", "gif"]),
                self.img_id_textbox,
                self.multi_select_ckbx_state,
                self.only_selected_state_object,
                self.images_selected_state
            ],
            outputs=[
                self.img_artist_tag_checkbox_group,
                self.img_character_tag_checkbox_group,
                self.img_species_tag_checkbox_group,
                self.img_general_tag_checkbox_group,
                self.img_meta_tag_checkbox_group,
                self.img_rating_tag_checkbox_group
            ]
        )
        self.send_img_from_gallery_button.click(
            fn=self.image_editor_tab_manager.send_images_from_feature,
            inputs=[self.send_img_from_gallery_dropdown,
                    self.gallery_comp,
                    gr.State(-1),
                    self.img_id_textbox,
                    self.batch_send_from_gallery_checkbox,
                    self.apply_to_all_type_select_checkboxgroup,
                    self.multi_select_ckbx_state,
                    self.only_selected_state_object,
                    self.images_selected_state
                    ],
            outputs=[self.custom_dataset_tab_manager.file_upload_button_single,
                     self.image_editor_tab_manager.image_editor,
                     self.image_editor_tab_manager.image_editor_crop,
                     self.image_editor_tab_manager.image_editor_sketch,
                     self.image_editor_tab_manager.image_editor_color_sketch,
                     self.custom_dataset_tab_manager.gallery_images_batch
                     ]
        ).then(
            fn=self.load_images_handler,
            inputs=[self.custom_dataset_tab_manager.file_upload_button_single, self.custom_dataset_tab_manager.gallery_images_batch, self.image_mode_choice_state,
                    self.batch_send_from_gallery_checkbox],
            outputs=[self.image_mode_choice_state]
        )
        self.tag_effects_gallery_dropdown.select(
            fn=self.update_generated_gallery_tag_selection,
            inputs=[self.category_filter_gallery_dropdown, self.img_id_textbox,
                   self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group, self.img_species_tag_checkbox_group,
                   self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group, self.img_rating_tag_checkbox_group],
            outputs=[self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group, self.img_species_tag_checkbox_group,
                   self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group, self.img_rating_tag_checkbox_group]
        )
        self.tag_search_textbox.change(
            fn=self.tag_ideas.suggest_search_tags,
            inputs=[self.tag_search_textbox, self.advanced_settings_tab_manager.total_suggestions_slider, self.previous_search_state_text],
            outputs=[self.tag_search_suggestion_dropdown, self.previous_search_state_text,
                    self.current_search_state_placement_tuple, self.relevant_search_categories]
        ).then(
            fn=None,
            inputs=[self.tag_search_suggestion_dropdown, self.relevant_search_categories],
            outputs=None,
            js=js_.js_set_colors_on_list_searchbar
        )
        self.tag_search_suggestion_dropdown.select(
            fn=self.tag_ideas.dropdown_search_handler,
            inputs=[self.tag_search_textbox, self.previous_search_state_text, self.current_search_state_placement_tuple],
            outputs=[self.tag_search_textbox, self.previous_search_state_text, self.current_search_state_placement_tuple,
                     self.tag_search_suggestion_dropdown]
        )
        self.tag_search_textbox.submit(
            fn=self.search_tags,
            inputs=[self.tag_search_textbox, self.apply_to_all_type_select_checkboxgroup, self.apply_datetime_sort_ckbx,
                    self.apply_datetime_choice_menu],
            outputs=[self.gallery_comp]).then(
            fn=self.reset_selected_img,
            inputs=[self.img_id_textbox],
            outputs=[self.img_id_textbox, self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group,
                     self.img_species_tag_checkbox_group, self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group,
                     self.img_rating_tag_checkbox_group]
        )
        self.tag_add_textbox.change(
            fn=self.tag_ideas.suggest_tags,
            inputs=[self.tag_add_textbox, self.initial_add_state, self.advanced_settings_tab_manager.total_suggestions_slider,
                    self.initial_add_state_tag],
            outputs=[self.tag_add_suggestion_dropdown, self.initial_add_state, self.initial_add_state_tag, self.relevant_add_categories]).then(
            fn=self.add_tag_changes,
            inputs=[self.initial_add_state_tag, self.apply_to_all_type_select_checkboxgroup, self.img_id_textbox,
                    self.multi_select_ckbx_state, self.only_selected_state_object, self.images_selected_state,
                    self.initial_add_state, gr.State(False)],
            outputs=[self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group,
                     self.img_species_tag_checkbox_group, self.img_general_tag_checkbox_group,
                     self.img_meta_tag_checkbox_group, self.img_rating_tag_checkbox_group, self.initial_add_state_tag,
                     self.tag_add_textbox]).then(
            fn=None,
            inputs=[self.tag_add_suggestion_dropdown, self.relevant_add_categories],
            outputs=None,
            js=js_.js_set_colors_on_list_add_tag
        )
        self.tag_add_textbox.submit(
             fn=self.add_tag_changes,
             inputs=[self.tag_add_textbox, self.apply_to_all_type_select_checkboxgroup, self.img_id_textbox, self.multi_select_ckbx_state,
                     self.only_selected_state_object, self.images_selected_state, self.initial_add_state, gr.State(True)],
             outputs=[self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group, self.img_species_tag_checkbox_group,
                      self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group, self.img_rating_tag_checkbox_group,
                      self.initial_add_state_tag, self.tag_add_textbox]
        )
        self.tag_add_suggestion_dropdown.select(
             fn=self.tag_ideas.dropdown_handler_add_tags,
             inputs=[self.apply_to_all_type_select_checkboxgroup, self.img_id_textbox, self.multi_select_ckbx_state,
                     self.only_selected_state_object, self.images_selected_state, self.initial_add_state],
             outputs=[self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group, self.img_species_tag_checkbox_group,
                      self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group, self.img_rating_tag_checkbox_group,
                      self.tag_add_textbox, self.tag_add_suggestion_dropdown, self.initial_add_state, self.initial_add_state_tag]
        )
        self.image_remove_button.click(
            fn=self.remove_images,
            inputs=[self.apply_to_all_type_select_checkboxgroup, self.img_id_textbox, self.apply_datetime_sort_ckbx,
                    self.apply_datetime_choice_menu, self.multi_select_ckbx_state, self.only_selected_state_object,
                    self.images_selected_state],
            outputs=[self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group, self.img_species_tag_checkbox_group,
                     self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group, self.img_rating_tag_checkbox_group,
                     self.gallery_comp, self.img_id_textbox, self.only_selected_state_object, self.images_selected_state]).then(
            fn=self.reset_gallery_component_only,
            inputs=[],
            outputs=[self.gallery_comp]).then(
            fn=self.show_searched_gallery,
            inputs=[self.download_folder_type, self.apply_datetime_sort_ckbx, self.apply_datetime_choice_menu],
            outputs=[self.gallery_comp]
        )
        self.image_save_ids_button.click(
            fn=self.save_image_changes,
            inputs=[],
            outputs=[]
        )
        self.tag_remove_button.click(
            fn=self.remove_all,
            inputs=[
                self.img_artist_tag_checkbox_group,
                self.img_character_tag_checkbox_group,
                self.img_species_tag_checkbox_group,
                self.img_general_tag_checkbox_group,
                self.img_meta_tag_checkbox_group,
                self.img_rating_tag_checkbox_group,
                self.apply_to_all_type_select_checkboxgroup,
                self.img_id_textbox,
                self.multi_select_ckbx_state,
                self.only_selected_state_object,
                self.images_selected_state
            ],
            outputs=[
                self.img_artist_tag_checkbox_group,
                self.img_character_tag_checkbox_group,
                self.img_species_tag_checkbox_group,
                self.img_general_tag_checkbox_group,
                self.img_meta_tag_checkbox_group,
                self.img_rating_tag_checkbox_group
            ]
        )
        self.tag_save_button.click(
            fn=self.save_tag_changes,
            inputs=[],
            outputs=[]).then(
            fn=self.reset_gallery_component_only,
            inputs=[],
            outputs=[self.gallery_comp]).then(
            fn=self.show_searched_gallery,
            inputs=[self.download_folder_type, self.apply_datetime_sort_ckbx, self.apply_datetime_choice_menu],
            outputs=[self.gallery_comp]).then(
            fn=self.clear_categories,
            inputs=[],
            outputs=[self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group, self.img_species_tag_checkbox_group,
                     self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group, self.img_rating_tag_checkbox_group,
                     self.img_id_textbox]
        )
        self.select_multiple_images_checkbox.change(
            fn=self.set_ckbx_state,
            inputs=[self.select_multiple_images_checkbox, self.multi_select_ckbx_state],
            outputs=[self.multi_select_ckbx_state]
        )
        self.download_folder_type.change(
            fn=self.show_gallery,
            inputs=[self.download_folder_type, self.apply_datetime_sort_ckbx, self.apply_datetime_choice_menu],
            outputs=[self.gallery_comp]).then(
            fn=self.reset_selected_img,
            inputs=[self.img_id_textbox],
            outputs=[self.img_id_textbox, self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group,
                     self.img_species_tag_checkbox_group, self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group,
                     self.img_rating_tag_checkbox_group]
        )
        # there is a networking "delay" bug for the below feature to work (do NOT click on the same image after selected) i.e. click on a different image before going back to that one
        self.gallery_comp.select(
            fn=self.get_img_tags,
            inputs=[self.gallery_comp, self.select_multiple_images_checkbox, self.images_selected_state,
                    self.select_between_images_checkbox, self.images_tuple_points],
            outputs=[self.img_id_textbox, self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group,
                     self.img_species_tag_checkbox_group, self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group,
                     self.img_rating_tag_checkbox_group, self.images_selected_state, self.only_selected_state_object,
                     self.images_tuple_points]).then(
            None,
            inputs=[self.images_selected_state, self.multi_select_ckbx_state],
            outputs=None,
            js=js_.js_do_everything
        )
        self.refresh_aspect_btn.click(
            fn=self.force_reload_show_gallery,
            inputs=[self.download_folder_type, self.apply_datetime_sort_ckbx, self.apply_datetime_choice_menu],
            outputs=[self.gallery_comp]
        )
        self.remove_now_button.click(
            fn=self.remove_from_all,
            inputs=[self.remove_tags_list, self.apply_to_all_type_select_checkboxgroup],
            outputs=[]
        )
        self.replace_now_button.click(
            fn=self.replace_from_all,
            inputs=[self.replace_tags_list, self.apply_to_all_type_select_checkboxgroup],
            outputs=[]
        )
        self.prepend_now_button.click(
            fn=self.prepend_with_keyword,
            inputs=[self.keyword_search_text, self.prepend_text, self.prepend_option, self.apply_to_all_type_select_checkboxgroup],
            outputs=[]
        )
