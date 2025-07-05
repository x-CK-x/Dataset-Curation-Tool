import gradio as gr
import os
import copy
import datetime
import glob

from utils import group_manager

from utils import js_constants as js_, md_constants as md_, helper_functions as help, image_tag_tools


class Gallery_tab:
    def __init__(self, file_extn_list, image_board, cwd, multi_select_ckbx_state, only_selected_state_object,
                 images_selected_state, image_mode_choice_state,
                 previous_search_state_text, current_search_state_placement_tuple, relevant_search_categories,
                 initial_add_state, initial_add_state_tag, relevant_add_categories, images_tuple_points,
                 download_tab_manager, auto_complete_config_name, all_tags_ever_dict, all_images_dict,
                 selected_image_dict, artist_csv_dict, character_csv_dict, species_csv_dict, general_csv_dict,
                 meta_csv_dict, rating_csv_dict, tags_csv_dict, image_creation_times, is_csv_loaded,
                 db_manager=None, download_id=None
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

        # supported media extensions
        self.image_formats = [
            "png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp", "heic"
        ]
        self.video_formats = [
            "webm", "mp4", "mkv", "avi", "mov", "flv", "gifv", "swf"
        ]
        self.current_media_mode = "images"

        self.db_manager = db_manager
        self.download_id = download_id



        self.advanced_settings_tab_manager = None
        self.download_tab_manager = download_tab_manager
        self.image_editor_tab_manager = None
        self.tag_ideas = None

        # map of (ext, img_id) -> absolute path for images loaded from the
        # database. Used when gallery paths don't follow the default folder
        # structure.
        self.search_image_paths = {}

        # stores the currently displayed gallery image paths to avoid passing
        # filepaths through gradio inputs
        self.gallery_state = gr.State([])

        # mapping of group name -> list of [ext, img_id]
        self.groups_config_path = os.path.join(self.cwd, "groups.json")
        self.groups_state = gr.State(group_manager.load_groups_file(self.groups_config_path))

        # buffers holding tags transferred/removed during compare operations
        self.transfer_buffer = []  # tags to add when applying to other images
        self.remove_buffer = []    # tags to remove when applying to other images

        # buffers holding tags transferred/removed during compare operations
        self.transfer_buffer = []  # tags to add when applying to other images
        self.remove_buffer = []    # tags to remove when applying to other images

        # buffers holding tags transferred/removed during compare operations
        self.transfer_buffer = []  # tags to add when applying to other images
        self.remove_buffer = []    # tags to remove when applying to other images

        # buffers holding tags transferred/removed during compare operations
        self.transfer_buffer = []  # tags to add when applying to other images
        self.remove_buffer = []    # tags to remove when applying to other images

        # buffers holding tags transferred/removed during compare operations
        self.transfer_buffer = []  # tags to add when applying to other images
        self.remove_buffer = []    # tags to remove when applying to other images

        # optional path to a user provided dataset loaded via the
        # custom dataset tab. When this is set, the gallery should only
        # display images from this directory.
        self.custom_dataset_dir = None
        self.custom_dataset_loaded = False




    def set_tag_ideas(self, tag_ideas):
        self.tag_ideas = tag_ideas

    def set_advanced_settings_tab_manager(self, advanced_settings_tab_manager):
        self.advanced_settings_tab_manager = advanced_settings_tab_manager

    def set_image_editor_tab_manager(self, image_editor_tab_manager):
        self.image_editor_tab_manager = image_editor_tab_manager

    def set_custom_dataset_tab_manager(self, custom_dataset_tab_manager):
        self.custom_dataset_tab_manager = custom_dataset_tab_manager

    def set_download_id(self, download_id):
        self.download_id = download_id

    def persist_images_to_db(self, full_path_downloads):
        """Persist loaded images to the global database."""
        if not hasattr(self, "db_manager") or self.db_manager is None:
            return
        for ext, images in self.all_images_dict.items():
            if ext == "searched":
                continue
            folder = self.download_tab_manager.settings_json[f"{ext}_folder"]
            for img_id, tags in images.items():
                file_path = os.path.join(full_path_downloads, folder, f"{img_id}.{ext}")
                self.db_manager.add_file(
                    self.download_id,
                    post_tags=','.join(tags),
                    post_created_at=None,
                    downloaded_at=datetime.datetime.utcnow().isoformat(),
                    cdn_url=None,
                    local_path=file_path,
                    tag_local_path=None,
                    tag_cdn_url=None,
                )











    def get_saved_image_count(self):
        total_img_count = 0
        img_count_list = []
        for key in ['png', 'jpg', 'gif']:
            img_count_list.append(len(list(self.download_tab_manager.auto_complete_config[key].keys())))
            total_img_count += img_count_list[-1]
        img_count_list.append(total_img_count)
        return img_count_list

    def get_total_image_count(self):
        """Return total number of images currently loaded."""
        total = 0
        for ext, images in self.all_images_dict.items():
            if ext == 'searched':
                continue
            total += len(images)
        return total

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
            if ext not in self.all_images_dict or img_name not in self.all_images_dict.get(ext, {}):
                folder = self.download_tab_manager.settings_json.get(f"{ext}_folder", "")
                base = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"],
                                   self.download_tab_manager.settings_json["downloaded_posts_folder"], folder)
                tag_file = os.path.join(base, f"{img_name}.txt")
                img_tag_list = help.parse_single_all_tags(tag_file) if os.path.exists(tag_file) else []
            else:
                img_tag_list = copy.deepcopy(self.all_images_dict[ext][img_name])

            help.verbose_print(f"img_tag_list:\t\t{img_tag_list}")
            # determine the category of each tag (TAGS WITHOUT A CATEGORY ARE NOT DISPLAYED)
            temp_tag_dict = {}
            temp_list = [[], [], [], [], [], [], []]  # artist, character, species, invalid, general, meta, rating
            for tag in img_tag_list:
                category = self.get_category_name(tag)
                if category == 'artist':
                    temp_list[0].append(tag)
                elif category == 'character':
                    temp_list[1].append(tag)
                elif category == 'species':
                    temp_list[2].append(tag)
                elif category == 'general':
                    temp_list[4].append(tag)
                elif category == 'meta':
                    temp_list[5].append(tag)
                elif category == 'rating':
                    temp_list[6].append(tag)
                else:
                    temp_list[3].append(tag)
            
            temp_tag_dict["artist"] = temp_list[0]
            temp_tag_dict["character"] = temp_list[1]
            temp_tag_dict["species"] = temp_list[2]
            temp_tag_dict["invalid"] = temp_list[3]
            temp_tag_dict["general"] = temp_list[4]
            temp_tag_dict["meta"] = temp_list[5]
            temp_tag_dict["rating"] = temp_list[6]

            self.selected_image_dict = {}
            self.selected_image_dict[img_name] = copy.deepcopy(temp_tag_dict)
            self.selected_image_dict["type"] = ext
            help.verbose_print(f"self.selected_image_dict:\t\t{self.selected_image_dict}")
        else:
            self.selected_image_dict = None

    ### Update gellery component
    def update_search_gallery(self, sort_images, sort_option, media_mode="images"):
        temp = '\\' if help.is_windows() else '/'
        if self.custom_dataset_dir:
            folder_path = self.custom_dataset_dir
        else:
            folder_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            folder_path = os.path.join(folder_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])

        images = []
        for ext in list(self.all_images_dict["searched"].keys()):
            if media_mode == "images" and ext in self.video_formats:
                continue
            if media_mode == "videos" and ext not in self.video_formats:
                continue
            if self.custom_dataset_dir:
                search_path = self.custom_dataset_dir
            else:
                search_path = os.path.join(folder_path, self.download_tab_manager.settings_json.get(f"{ext}_folder", ""))
            for img_id in list(self.all_images_dict["searched"][ext].keys()):
                img_path = self.search_image_paths.get((ext, img_id))
                if not img_path:
                    img_path = os.path.join(search_path, f"{img_id}.{ext}")
                images.append(img_path)

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

    def _get_dataset_folder(self, ext):
        """Return directory where media files should be read/written."""
        if self.custom_dataset_dir:
            return self.custom_dataset_dir
        full_path_downloads = os.path.join(
            os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
            self.download_tab_manager.settings_json["downloaded_posts_folder"],
        )
        return os.path.join(full_path_downloads, self.download_tab_manager.settings_json.get(f"{ext}_folder", ""))

    def _get_media_paths(self, ext, img_id):
        base = self._get_dataset_folder(ext)
        # when using a custom dataset, individual files may reside in nested
        # subdirectories. rely on the search_image_paths map built during
        # dataset loading to locate the correct folder.
        if self.custom_dataset_dir and (ext, img_id) in self.search_image_paths:
            img_path = self.search_image_paths[(ext, img_id)]
            tag_path = os.path.splitext(img_path)[0] + ".txt"
            return img_path, tag_path
        return os.path.join(base, f"{img_id}.{ext}"), os.path.join(base, f"{img_id}.txt")

    def load_external_dataset(self, folder_path):
        """Load images and tags from a user provided directory."""
        help.verbose_print(f"load_external_dataset folder_path:\t{folder_path}")
        if not folder_path or not os.path.isdir(folder_path):
            help.verbose_print("load_external_dataset: invalid path")
            return gr.update(), gr.update()

        self.custom_dataset_dir = folder_path
        self.custom_dataset_loaded = True
        # gather tags from the provided folder. if no tag files are found,
        # recursively search all subdirectories as a fallback so that nested
        # datasets still load properly.
        help.verbose_print("gathering tags")
        self.all_images_dict = help.gather_media_tags(folder_path)
        if set(self.all_images_dict.keys()) == {"searched"}:
            subfolders = []
            for root, dirs, _ in os.walk(folder_path):
                for d in dirs:
                    subfolders.append(os.path.join(root, d))
            if subfolders:
                found = help.gather_media_tags(*subfolders)
                for k, v in found.items():
                    if k == "searched":
                        continue
                    self.all_images_dict.setdefault(k, {}).update(v)
        help.verbose_print(f"found extensions:\t{list(self.all_images_dict.keys())}")

        # build search dict and image path map
        self.search_image_paths = {}
        filtered = {}
        for ext, images in self.all_images_dict.items():
            if ext == "searched":
                continue
            filtered[ext] = {}
            for img_id, tags in images.items():
                filtered[ext][img_id] = tags
                # locate the actual file path which may be nested in subfolders
                matches = glob.glob(os.path.join(folder_path, "**", f"{img_id}.{ext}"), recursive=True)
                if matches:
                    self.search_image_paths[(ext, img_id)] = matches[0]
                else:
                    self.search_image_paths[(ext, img_id)] = os.path.join(folder_path, f"{img_id}.{ext}")
        self.all_images_dict["searched"] = copy.deepcopy(filtered)

        # compute creation times for sorting
        self.image_creation_times = {}
        self.initialize_posts_timekeeper()

        images = self.update_search_gallery(False, "", self.current_media_mode)
        try:
            self.gallery_state.value = images
        except Exception:
            pass
        help.verbose_print(f"gallery images loaded:\t{len(images)}")
        count = self.get_total_image_count()
        return gr.update(value=images, visible=True), gr.update(value=f"Total Images: {count}")

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
        if self.custom_dataset_dir:
            self.custom_dataset_loaded = True
            self.custom_dataset_loaded = True
            # when using a custom dataset, populate the gallery exclusively
            # from the provided folder and skip the default batch folders.
            if "searched" in self.all_images_dict:
                del self.all_images_dict["searched"]
                self.all_images_dict["searched"] = {}

            folder_path = self.custom_dataset_dir
            self.all_images_dict = help.gather_media_tags(folder_path)
            if set(self.all_images_dict.keys()) == {"searched"}:
                subfolders = []
                for root, dirs, _ in os.walk(folder_path):
                    for d in dirs:
                        subfolders.append(os.path.join(root, d))
                if subfolders:
                    found = help.gather_media_tags(*subfolders)
                    for k, v in found.items():
                        if k == "searched":
                            continue
                        self.all_images_dict.setdefault(k, {}).update(v)

            # map image ids to actual file paths which may reside in
            # nested subdirectories
            self.search_image_paths = {}
            for ext, images in self.all_images_dict.items():
                if ext == "searched":
                    continue
                for img_id in images.keys():
                    matches = glob.glob(os.path.join(folder_path, "**", f"{img_id}.{ext}"), recursive=True)
                    if matches:
                        self.search_image_paths[(ext, img_id)] = matches[0]
                    else:
                        self.search_image_paths[(ext, img_id)] = os.path.join(folder_path, f"{img_id}.{ext}")

            self.image_creation_times = {}
            self.initialize_posts_timekeeper()
            self.download_tab_manager.is_csv_loaded = True
            self.artist_csv_dict = {}
            self.character_csv_dict = {}
            self.species_csv_dict = {}
            self.general_csv_dict = {}
            self.meta_csv_dict = {}
            self.rating_csv_dict = {}
            self.tags_csv_dict = {}
            return

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
                    folder_paths = []
                    for key, val in self.download_tab_manager.settings_json.items():
                        if key.endswith("_folder") and key not in ["batch_folder", "downloaded_posts_folder", "tag_count_list_folder", "resized_img_folder"]:
                            folder_paths.append(os.path.join(full_path_downloads, val))
                    self.all_images_dict = help.gather_media_tags(*folder_paths)
                    self.persist_images_to_db(full_path_downloads)

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
        if self.custom_dataset_dir:
            folder_path = self.custom_dataset_dir
            self.all_images_dict = help.gather_media_tags(folder_path)
            if set(self.all_images_dict.keys()) == {"searched"}:
                subfolders = []
                for root, dirs, _ in os.walk(folder_path):
                    for d in dirs:
                        subfolders.append(os.path.join(root, d))
                if subfolders:
                    found = help.gather_media_tags(*subfolders)
                    for k, v in found.items():
                        if k == "searched":
                            continue
                        self.all_images_dict.setdefault(k, {}).update(v)
            self.search_image_paths = {}
            for ext, images in self.all_images_dict.items():
                if ext == "searched":
                    continue
                for img_id in images.keys():
                    matches = glob.glob(os.path.join(folder_path, "**", f"{img_id}.{ext}"), recursive=True)
                    if matches:
                        self.search_image_paths[(ext, img_id)] = matches[0]
                    else:
                        self.search_image_paths[(ext, img_id)] = os.path.join(folder_path, f"{img_id}.{ext}")
        else:
            full_path_downloads = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                               self.download_tab_manager.settings_json["downloaded_posts_folder"])
            if not self.all_images_dict or len(self.all_images_dict.keys()) == 0:
                folder_paths = []
                for key, val in self.download_tab_manager.settings_json.items():
                    if key.endswith("_folder") and key not in ["batch_folder", "downloaded_posts_folder", "tag_count_list_folder", "resized_img_folder"]:
                        folder_paths.append(os.path.join(full_path_downloads, val))
                self.all_images_dict = help.gather_media_tags(*folder_paths)
                self.persist_images_to_db(full_path_downloads)

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

    def load_from_db_rows(self, headers, rows):
        """Populate the search gallery using database rows."""
        if "local_path" not in headers:
            return []
        path_idx = headers.index("local_path")
        tag_idx = headers.index("post_tags") if "post_tags" in headers else None
        self.all_images_dict["searched"] = {}
        self.search_image_paths = {}
        for row in rows:
            path = row[path_idx]
            if not path or not os.path.isfile(path):
                continue
            ext = os.path.splitext(path)[1].lstrip('.').lower()
            img_id = os.path.splitext(os.path.basename(path))[0]
            tags = []
            if tag_idx is not None and row[tag_idx]:
                tags = [t for t in str(row[tag_idx]).split() if t]
            if ext not in self.all_images_dict["searched"]:
                self.all_images_dict["searched"][ext] = {}
            self.all_images_dict["searched"][ext][img_id] = tags
            self.search_image_paths[(ext, img_id)] = path
        images = self.update_search_gallery(False, "", self.current_media_mode)
        # persist gallery paths in state
        try:
            self.gallery_state.value = images
        except Exception:
            pass
        return images

    def search_tags(self, tag_search_textbox, global_search_opts, sort_images, sort_option):
        # clear previous search results before filtering
        self.all_images_dict["searched"] = {}
        self.search_image_paths = {}
        # update SEARCHED in global dictionary
        self.filter_images_by_tags(tag_search_textbox, global_search_opts)
        # return updated gallery
        images = self.update_search_gallery(sort_images, sort_option, self.current_media_mode)
        try:
            self.gallery_state.value = images
        except Exception:
            pass
        # clear previous selections when performing a new search
        self.images_selected_state.value = []
        self.only_selected_state_object.value = {}
        self._debug_selection([], {})
        count = self.get_total_image_count()
        return (
            gr.update(value=images, visible=True),
            gr.update(value=f"Total Images: {count}"),
            images,
        )

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
                              self.selected_image_dict[img_id]["species"], self.selected_image_dict[img_id]["invalid"],
                              self.selected_image_dict[img_id]["general"], self.selected_image_dict[img_id]["meta"],
                              self.selected_image_dict[img_id]["rating"]]
        category_order_dict = {"artist": 0, "character": 1, "species": 2, "invalid": 3,
                              "general": 4, "meta": 5, "rating": 6}

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
            img_invalid_tag_checkbox_group = None
            img_general_tag_checkbox_group = None
            img_meta_tag_checkbox_group = None
            img_rating_tag_checkbox_group = None
            if self.selected_image_dict is not None:
                # reload the categories for the self.selected_image_dict
                self.reload_selected_image_dict(temp_ext, img_id)

                img_artist_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['artist'], value=[])
                img_character_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['character'], value=[])
                img_species_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['species'], value=[])
                img_invalid_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['invalid'], value=[])
                img_general_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['general'], value=[])
                img_meta_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['meta'], value=[])
                img_rating_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['rating'], value=[])
            else:
                img_artist_tag_checkbox_group = gr.update(choices=[], value=[])
                img_character_tag_checkbox_group = gr.update(choices=[], value=[])
                img_species_tag_checkbox_group = gr.update(choices=[], value=[])
                img_invalid_tag_checkbox_group = gr.update(choices=[], value=[])
                img_general_tag_checkbox_group = gr.update(choices=[], value=[])
                img_meta_tag_checkbox_group = gr.update(choices=[], value=[])
                img_rating_tag_checkbox_group = gr.update(choices=[], value=[])

            return img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group, \
                   img_invalid_tag_checkbox_group, img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group, \
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
                        last_tag = self.get_insert_last_tags_name(self.get_category_name(tag),
                                                             self.selected_image_dict["type"], img_id,
                                                             tag)  # i.e. the tag before the new one
                        help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                        # get its index on the global list
                        glob_index = 0
                        if last_tag and last_tag in self.all_images_dict["searched"][self.selected_image_dict["type"]][img_id]:
                            glob_index = (
                                self.all_images_dict["searched"][self.selected_image_dict["type"]][img_id]
                            ).index(last_tag) + 1
                        self.all_images_dict["searched"][self.selected_image_dict["type"]][img_id].insert(glob_index, tag)

                        glob_index = 0
                        if last_tag and last_tag in self.all_images_dict[self.selected_image_dict["type"]][img_id]:
                            glob_index = (
                                self.all_images_dict[self.selected_image_dict["type"]][img_id]
                            ).index(last_tag) + 1
                        self.all_images_dict[self.selected_image_dict["type"]][img_id].insert(glob_index, tag)

                        if not img_id in self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]]:
                            self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]][img_id] = []
                        self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]][img_id].append(['+', tag, (glob_index)])

                        # create or increment category table AND frequency table for (all) tags
                        category_key = self.get_category_name(tag)
                        if category_key != "invalid":
                            self.add_to_csv_dictionaries(category_key, tag)  # add
            elif img_id in list(self.all_images_dict[self.selected_image_dict["type"]].keys()):  # find image in ( TYPE ) : id
                for tag in tag_list:
                    if not tag in self.all_images_dict[self.selected_image_dict["type"]][img_id]:
                        # get last tag in category
                        last_tag = self.get_insert_last_tags_name(self.get_category_name(tag),
                                                             self.selected_image_dict["type"], img_id,
                                                             tag)  # i.e. the tag before the new one
                        help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                        # get its index on the global list
                        glob_index = 0
                        if last_tag and last_tag in self.all_images_dict[self.selected_image_dict["type"]][img_id]:
                            glob_index = (
                                self.all_images_dict[self.selected_image_dict["type"]][img_id]
                            ).index(last_tag) + 1
                        self.all_images_dict[self.selected_image_dict["type"]][img_id].insert(glob_index, tag)

                        if not img_id in self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]]:
                            self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]][img_id] = []
                        self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]][img_id].append(['+', tag, (glob_index)])

                        # create or increment category table AND frequency table for (all) tags
                        category_key = self.get_category_name(tag)
                        if category_key != "invalid":
                            self.add_to_csv_dictionaries(category_key, tag)  # add
        if apply_to_all_type_select_checkboxgroup and len(apply_to_all_type_select_checkboxgroup) > 0:
            searched_only = set(apply_to_all_type_select_checkboxgroup) == {"searched"}
            if "searched" in apply_to_all_type_select_checkboxgroup:  # edit searched and then all the instances of the respective types
                if multi_select_ckbx_state[0]:
                    ##### returns index -> [ext, img_id]
                    for index in images_selected_state:
                        ext, img_id = only_selected_state_object[index]
                        if ext in apply_to_all_type_select_checkboxgroup or searched_only:
                            if img_id in list(self.all_images_dict["searched"][ext].keys()):
                                for tag in tag_list:
                                    if not tag in self.all_images_dict["searched"][ext][img_id]:  # add tag
                                        # get last tag in category
                                        last_tag = self.get_insert_last_tags_name(self.get_category_name(tag),
                                                                         ext, img_id,
                                                                         tag)  # i.e. the tag before the new one
                                        help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                                        # get its index on the global list
                                        glob_index = 0
                                        if last_tag and last_tag in self.all_images_dict["searched"][ext][img_id]:
                                            glob_index = (
                                                self.all_images_dict["searched"][ext][img_id]
                                            ).index(last_tag) + 1

                                        help.verbose_print(f"tag:\t\t{tag}")

                                        self.all_images_dict["searched"][ext][img_id].insert(glob_index, tag)

                                        self.all_images_dict[ext][img_id].insert(glob_index, tag)

                                        if not img_id in self.download_tab_manager.auto_complete_config[ext]:
                                            self.download_tab_manager.auto_complete_config[ext][img_id] = []
                                        self.download_tab_manager.auto_complete_config[ext][img_id].append(['+', tag, (glob_index)])

                                        # create or increment category table AND frequency table for (all) tags
                                        category_key = self.get_category_name(tag)
                                        if category_key != "invalid":
                                            self.add_to_csv_dictionaries(category_key, tag)  # add
                else:
                    for key_type in list(self.all_images_dict["searched"].keys()):
                        for img_id in list(self.all_images_dict["searched"][key_type].keys()):
                            for tag in tag_list:
                                if not tag in self.all_images_dict["searched"][key_type][img_id]:  # add tag
                                    # get last tag in category
                                    last_tag = self.get_insert_last_tags_name(self.get_category_name(tag),
                                                                         key_type, img_id,
                                                                         tag)  # i.e. the tag before the new one
                                    help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                                    # get its index on the global list
                                    glob_index = 0
                                    if last_tag and last_tag in self.all_images_dict["searched"][key_type][img_id]:
                                        glob_index = (
                                            self.all_images_dict["searched"][key_type][img_id]
                                        ).index(last_tag) + 1

                                    help.verbose_print(f"tag:\t\t{tag}")

                                    self.all_images_dict["searched"][key_type][img_id].insert(glob_index, tag)

                                    self.all_images_dict[key_type][img_id].insert(glob_index, tag)

                                    if not img_id in self.download_tab_manager.auto_complete_config[key_type]:
                                        self.download_tab_manager.auto_complete_config[key_type][img_id] = []
                                    self.download_tab_manager.auto_complete_config[key_type][img_id].append(['+', tag, (glob_index)])

                                    # create or increment category table AND frequency table for (all) tags
                                    category_key = self.get_category_name(tag)
                                    if category_key != "invalid":
                                        self.add_to_csv_dictionaries(category_key, tag)  # add
            else:
                if multi_select_ckbx_state[0]:
                    ##### returns index -> [ext, img_id]
                    for index in images_selected_state:
                        ext, img_id = only_selected_state_object[index]
                        if ext in apply_to_all_type_select_checkboxgroup or searched_only:
                            if img_id in list(self.all_images_dict[ext].keys()):
                                for tag in tag_list:
                                    if not tag in self.all_images_dict[ext][img_id]:
                                        # get last tag in category
                                        last_tag = self.get_insert_last_tags_name(self.get_category_name(tag),
                                                                                 ext, img_id,
                                                                                 tag)  # i.e. the tag before the new one
                                        help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                                        # get its index on the global list
                                        glob_index = 0
                                        if last_tag and last_tag in self.all_images_dict[ext][img_id]:
                                            glob_index = (
                                                self.all_images_dict[ext][img_id]
                                            ).index(last_tag) + 1

                                        self.all_images_dict[ext][img_id].insert(glob_index, tag)

                                        if not img_id in self.download_tab_manager.auto_complete_config[ext]:
                                            self.download_tab_manager.auto_complete_config[ext][img_id] = []
                                        self.download_tab_manager.auto_complete_config[ext][img_id].append(['+', tag, (glob_index)])

                                        if "searched" in self.all_images_dict and ext in self.all_images_dict[
                                            "searched"] and img_id in self.all_images_dict["searched"][ext]:
                                            self.all_images_dict["searched"][ext][img_id].insert(glob_index, tag)

                                        # create or increment category table AND frequency table for (all) tags
                                    category_key = self.get_category_name(tag)
                                    if category_key != "invalid":
                                        self.add_to_csv_dictionaries(category_key, tag)  # add
                else:
                    for key_type in apply_to_all_type_select_checkboxgroup:
                        for img_id in list(self.all_images_dict[key_type].keys()):
                            for tag in tag_list:
                                if not tag in self.all_images_dict[key_type][img_id]:
                                    # get last tag in category
                                    last_tag = self.get_insert_last_tags_name(self.get_category_name(tag),
                                                                         key_type, img_id,
                                                                         tag)  # i.e. the tag before the new one
                                    help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                                    # get its index on the global list
                                    glob_index = 0
                                    if last_tag and last_tag in self.all_images_dict[key_type][img_id]:
                                        glob_index = (
                                            self.all_images_dict[key_type][img_id]
                                        ).index(last_tag) + 1

                                    self.all_images_dict[key_type][img_id].insert(glob_index, tag)

                                    if not img_id in self.download_tab_manager.auto_complete_config[key_type]:
                                        self.download_tab_manager.auto_complete_config[key_type][img_id] = []
                                    self.download_tab_manager.auto_complete_config[key_type][img_id].append(['+', tag, (glob_index)])

                                    if "searched" in self.all_images_dict and key_type in self.all_images_dict[
                                        "searched"] and img_id in self.all_images_dict["searched"][key_type]:
                                        self.all_images_dict["searched"][key_type][img_id].insert(glob_index, tag)

                                    # create or increment category table AND frequency table for (all) tags
                                    category_key = self.get_category_name(tag)
                                    if category_key != "invalid":
                                        self.add_to_csv_dictionaries(category_key, tag)  # add

        # find type of selected image
        temp_ext = None
        temp_all_images_dict_keys = list(self.all_images_dict.keys())
        if "searched" in temp_all_images_dict_keys:
            temp_all_images_dict_keys.remove("searched")
        for each_key in temp_all_images_dict_keys:
            if img_id in list(self.all_images_dict[each_key]):
                temp_ext = each_key
                break
        # reload the categories for the self.selected_image_dict only if an image
        # id is provided. Without a selected image, the checkbox groups should
        # simply be cleared to avoid NoneType errors
        if img_id:
            self.reload_selected_image_dict(temp_ext, img_id)
        else:
            self.selected_image_dict = None

        if self.selected_image_dict and img_id in self.selected_image_dict:
            img_artist_tag_checkbox_group = gr.update(
                choices=self.selected_image_dict[img_id].get("artist", []),
                value=[],
            )
            img_character_tag_checkbox_group = gr.update(
                choices=self.selected_image_dict[img_id].get("character", []),
                value=[],
            )
            img_species_tag_checkbox_group = gr.update(
                choices=self.selected_image_dict[img_id].get("species", []),
                value=[],
            )
            img_invalid_tag_checkbox_group = gr.update(
                choices=self.selected_image_dict[img_id].get("invalid", []),
                value=[],
            )
            img_general_tag_checkbox_group = gr.update(
                choices=self.selected_image_dict[img_id].get("general", []),
                value=[],
            )
            img_meta_tag_checkbox_group = gr.update(
                choices=self.selected_image_dict[img_id].get("meta", []),
                value=[],
            )
            img_rating_tag_checkbox_group = gr.update(
                choices=self.selected_image_dict[img_id].get("rating", []),
                value=[],
            )
        else:
            img_artist_tag_checkbox_group = gr.update(choices=[], value=[])
            img_character_tag_checkbox_group = gr.update(choices=[], value=[])
            img_species_tag_checkbox_group = gr.update(choices=[], value=[])
            img_invalid_tag_checkbox_group = gr.update(choices=[], value=[])
            img_general_tag_checkbox_group = gr.update(choices=[], value=[])
            img_meta_tag_checkbox_group = gr.update(choices=[], value=[])
            img_rating_tag_checkbox_group = gr.update(choices=[], value=[])

        return img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group, \
               img_invalid_tag_checkbox_group, img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group, \
               new_state_of_suggestion_tag, new_state_of_suggestion_textbox

    def remove_tag_changes(self, category_tag_checkbox_group, apply_to_all_type_select_checkboxgroup, img_id,
                           multi_select_ckbx_state, only_selected_state_object, images_selected_state):

        # Initialize checkbox groups so the function always returns valid values
        img_artist_tag_checkbox_group = None
        img_character_tag_checkbox_group = None
        img_species_tag_checkbox_group = None
        img_invalid_tag_checkbox_group = None
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
                category_key = self.get_category_name(tag)
                if tag in self.selected_image_dict[img_id][category_key]:
                    while tag in self.selected_image_dict[img_id][category_key]:
                        self.selected_image_dict[img_id][category_key].remove(tag)
            # update info for category components
            img_artist_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['artist'], value=[])
            img_character_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['character'], value=[])
            img_species_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['species'], value=[])
            img_invalid_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['invalid'], value=[])
            img_general_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['general'], value=[])
            img_meta_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['meta'], value=[])
            img_rating_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['rating'], value=[])
            # help.verbose_print(
            #     f"self.selected_image_dict[img_id][string_category]:\t\t{self.selected_image_dict[img_id][string_category]}")
        elif img_id and len(img_id) > 0 and self.selected_image_dict and (
                not apply_to_all_type_select_checkboxgroup or len(apply_to_all_type_select_checkboxgroup) == 0):
            # update info for selected image
            for tag in tag_list:
                category_key = self.get_category_name(tag)
                if tag in self.selected_image_dict[img_id][category_key]:
                    while tag in self.selected_image_dict[img_id][category_key]:
                        self.selected_image_dict[img_id][category_key].remove(tag)
            # update info for category components
            img_artist_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['artist'], value=[])
            img_character_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['character'], value=[])
            img_species_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['species'], value=[])
            img_invalid_tag_checkbox_group = gr.update(choices=self.selected_image_dict[img_id]['invalid'], value=[])
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
                        category_key = self.get_category_name(tag)
                        if category_key != "invalid":
                            self.remove_to_csv_dictionaries(category_key, tag)  # remove
            elif img_id in list(self.all_images_dict[self.selected_image_dict["type"]].keys()):  # find image in ( TYPE ) : id
                for tag in tag_list:
                    if tag in self.all_images_dict[self.selected_image_dict["type"]][img_id]:
                        while tag in self.all_images_dict[self.selected_image_dict["type"]][img_id]:
                            self.all_images_dict[self.selected_image_dict["type"]][img_id].remove(tag)

                            if not img_id in self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]]:
                                self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]][img_id] = []
                            self.download_tab_manager.auto_complete_config[self.selected_image_dict["type"]][img_id].append(['-', tag])

                        # create or increment category table AND frequency table for (all) tags
                        category_key = self.get_category_name(tag)
                        if category_key != "invalid":
                            self.remove_to_csv_dictionaries(category_key, tag)  # remove

        if apply_to_all_type_select_checkboxgroup and len(apply_to_all_type_select_checkboxgroup) > 0:
            searched_only = set(apply_to_all_type_select_checkboxgroup) == {"searched"}
            if "searched" in apply_to_all_type_select_checkboxgroup:  # edit searched and then all the instances of the respective types
                if multi_select_ckbx_state[0]:
                    ##### returns index -> [ext, img_id]
                    for index in images_selected_state:
                        ext, img_id = only_selected_state_object[index]
                        if ext in apply_to_all_type_select_checkboxgroup or searched_only:
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
                                        category_key = self.get_category_name(tag)
                                        if category_key != "invalid":
                                            self.remove_to_csv_dictionaries(category_key, tag)  # remove
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
                                    category_key = self.get_category_name(tag)
                                    if category_key != "invalid":
                                        self.remove_to_csv_dictionaries(category_key,
                                                               tag)  # remove
            else:
                if multi_select_ckbx_state[0]:
                    ##### returns index -> [ext, img_id]
                    for index in images_selected_state:
                        ext, img_id = only_selected_state_object[index]
                        if ext in apply_to_all_type_select_checkboxgroup or searched_only:
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
                                        category_key = self.get_category_name(tag)
                                        if category_key != "invalid":
                                            self.remove_to_csv_dictionaries(category_key,
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
                                    category_key = self.get_category_name(tag)
                                    if category_key != "invalid":
                                        self.remove_to_csv_dictionaries(category_key,
                                                               tag)  # remove

        return img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group, \
               img_invalid_tag_checkbox_group, img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group

    def remove_all(self, artist, character, species, invalid, general, meta, rating, apply_to_all_type_select_checkboxgroup,
                   img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state):
        self.remove_tag_changes(artist, apply_to_all_type_select_checkboxgroup,
                           img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state)
        self.remove_tag_changes(character, apply_to_all_type_select_checkboxgroup,
                           img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state)
        self.remove_tag_changes(species, apply_to_all_type_select_checkboxgroup,
                           img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state)
        self.remove_tag_changes(invalid, apply_to_all_type_select_checkboxgroup,
                           img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state)
        self.remove_tag_changes(general, apply_to_all_type_select_checkboxgroup,
                           img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state)
        self.remove_tag_changes(meta, apply_to_all_type_select_checkboxgroup,
                           img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state)
        return self.remove_tag_changes(rating, apply_to_all_type_select_checkboxgroup,
                                  img_id_textbox, multi_select_ckbx_state, only_selected_state_object,
                                  images_selected_state)

    def get_category_name(self, tag):
        tag = tag.strip()
        if tag in self.all_tags_ever_dict:
            category = self.image_board.categories_map[self.all_tags_ever_dict[tag][0]]
            if category in self.image_board.valid_categories:
                return category
            return "invalid"
        return "invalid"

    ### if "searched" is selected in apply_to_all_type_select_checkboxgroup, then all SEARCHED images will be deleted!
    def remove_images(self, apply_to_all_type_select_checkboxgroup, image_id, sort_images, sort_option,
                      multi_select_ckbx_state, only_selected_state_object, images_selected_state):
        image_id = str(image_id)
        if apply_to_all_type_select_checkboxgroup is None:
            apply_to_all_type_select_checkboxgroup = []

        searched_only = set(apply_to_all_type_select_checkboxgroup) == {"searched"}

        if not "searched" in apply_to_all_type_select_checkboxgroup:
            if multi_select_ckbx_state[0] and len(apply_to_all_type_select_checkboxgroup) > 0:
                ##### returns index -> [ext, img_id]
                for index in images_selected_state:
                    ext, img_id = only_selected_state_object[index]
                    if ext in apply_to_all_type_select_checkboxgroup or searched_only:
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
                    if ext in apply_to_all_type_select_checkboxgroup or searched_only:
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
                    if key_type in apply_to_all_type_select_checkboxgroup or searched_only:
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
        images = self.update_search_gallery(sort_images, sort_option, self.current_media_mode)
        try:
            self.gallery_state.value = images
        except Exception:
            pass
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
            for img_id in list(self.all_images_dict[ext]):
                img_path, tag_path = self._get_media_paths(ext, img_id)
                ordered = help.sort_tags_by_priority(self.all_images_dict[ext][img_id], self.get_category_name)
                self.all_images_dict[ext][img_id] = ordered
                temp_tag_string = ", ".join(ordered)
                help.write_tags_to_text_file(temp_tag_string, tag_path)
                if self.db_manager:
                    fid = self.db_manager.get_file_id(img_path)
                    if fid:
                        self.db_manager.add_modified_file(fid, mod_tag_path=tag_path)
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
            full_path_gallery_type = self._get_dataset_folder(ext)
            images = [name.split(temp)[-1].split(".")[0] for name in glob.glob(os.path.join(full_path_gallery_type,
                    f"*.{ext}"))]
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
                                               species_comp_checkboxgroup, invalid_comp_checkboxgroup,
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

        all_available_tags = [[], [], [], [], [], [], []]
        all_available_tags[0] = self.selected_image_dict[img_name]["artist"]
        all_available_tags[1] = self.selected_image_dict[img_name]["character"]
        all_available_tags[2] = self.selected_image_dict[img_name]["species"]
        all_available_tags[3] = self.selected_image_dict[img_name]["invalid"]
        all_available_tags[4] = self.selected_image_dict[img_name]["general"]
        all_available_tags[5] = self.selected_image_dict[img_name]["meta"]
        all_available_tags[6] = self.selected_image_dict[img_name]["rating"]

        all_selected_tags = [[], [], [], [], [], [], []]
        all_selected_tags[0] = artist_comp_checkboxgroup
        all_selected_tags[1] = character_comp_checkboxgroup
        all_selected_tags[2] = species_comp_checkboxgroup
        all_selected_tags[3] = invalid_comp_checkboxgroup
        all_selected_tags[4] = general_comp_checkboxgroup
        all_selected_tags[5] = meta_comp_checkboxgroup
        all_selected_tags[6] = rating_comp_checkboxgroup

        if tag_effects_dropdown is None or len(tag_effects_dropdown) == 0:
            return gr.update(choices=all_available_tags[0], value=all_selected_tags[0]), \
                   gr.update(choices=all_available_tags[1], value=all_selected_tags[1]), \
                   gr.update(choices=all_available_tags[2], value=all_selected_tags[2]), \
                   gr.update(choices=all_available_tags[3], value=all_selected_tags[3]), \
                   gr.update(choices=all_available_tags[4], value=all_selected_tags[4]), \
                   gr.update(choices=all_available_tags[5], value=all_selected_tags[5]), \
                   gr.update(choices=all_available_tags[6], value=all_selected_tags[6])
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
                   gr.update(choices=all_available_tags[5], value=all_selected_tags[5]), \
                   gr.update(choices=all_available_tags[6], value=all_selected_tags[6])





    def reset_selected_img(self, img_id_textbox):
        # reset selected_img
        self.selected_image_dict = None

        # reset img_id_textbox
        img_id_textbox = gr.update(value="")

        # reset all checkboxgroup components
        img_artist_tag_checkbox_group = gr.update(choices=[])
        img_character_tag_checkbox_group = gr.update(choices=[])
        img_species_tag_checkbox_group = gr.update(choices=[])
        img_invalid_tag_checkbox_group = gr.update(choices=[])
        img_general_tag_checkbox_group = gr.update(choices=[])
        img_meta_tag_checkbox_group = gr.update(choices=[])
        img_rating_tag_checkbox_group = gr.update(choices=[])
        return img_id_textbox, img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group, img_invalid_tag_checkbox_group, img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group

    def get_searched_image_total(self):
        total_img_count = 0
        temp_key_list = list(self.all_images_dict["searched"].keys())
        for key in temp_key_list:
            total_img_count += len(list(self.all_images_dict["searched"][key].keys()))
        return total_img_count

    def show_searched_gallery(self, folder_type_select, sort_images, sort_option):
        # type select
        self.current_media_mode = folder_type_select
        if "searched" in self.all_images_dict and len(
                list(self.all_images_dict["searched"].keys())) > 0 and self.get_searched_image_total() > 0:
            images = self.update_search_gallery(sort_images, sort_option, folder_type_select)
        else:
            help.verbose_print(f"in SHOW searched gallery")
            return self.show_gallery(folder_type_select, sort_images, sort_option)
        try:
            self.gallery_state.value = images
        except Exception:
            pass
        count = self.get_total_image_count()
        return (
            gr.update(value=images, visible=True),
            gr.update(value=f"Total Images: {count}"),
            images,
        )

    def clear_categories(self):
        artist_comp_checkboxgroup = gr.update(choices=[])
        character_comp_checkboxgroup = gr.update(choices=[])
        species_comp_checkboxgroup = gr.update(choices=[])
        invalid_comp_checkboxgroup = gr.update(choices=[])
        general_comp_checkboxgroup = gr.update(choices=[])
        meta_comp_checkboxgroup = gr.update(choices=[])
        rating_comp_checkboxgroup = gr.update(choices=[])
        return artist_comp_checkboxgroup, character_comp_checkboxgroup, species_comp_checkboxgroup, invalid_comp_checkboxgroup, general_comp_checkboxgroup, \
               meta_comp_checkboxgroup, rating_comp_checkboxgroup, gr.update(value="")
    def set_ckbx_state(self, select_multiple_images_checkbox,
                       multi_select_ckbx_state):  # UI boolean component, JSON boolean component wrapped in a list
        multi_select_ckbx_state = [select_multiple_images_checkbox]
        toggle_state = gr.update(interactive=select_multiple_images_checkbox)
        return multi_select_ckbx_state, toggle_state, toggle_state, toggle_state, toggle_state

    def _build_selection_mapping(self, gallery_images, indices):
        mapping = {}
        for idx in indices:
            path = gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
            mapping[idx] = self.extract_name_and_extention(path)
        return mapping

    def _update_search_from_mapping(self, mapping):
        self.all_images_dict["searched"] = {}
        for ext, img_id in mapping.values():
            if ext not in self.all_images_dict["searched"]:
                self.all_images_dict["searched"][ext] = {}
            tags = self.all_images_dict.get(ext, {}).get(img_id, [])
            self.all_images_dict["searched"][ext][img_id] = tags.copy()

    def _debug_selection(self, images_selected_state, mapping):
        help.verbose_print(f"images_selected_states:\t{images_selected_state}")
        help.verbose_print(f"only_selected_state_object:\t{mapping}")
        help.verbose_print(f"number_selected:\t{len(images_selected_state)}")

    def select_all(self, gallery_images):
        """Return indices of all images for selection."""
        return list(range(len(gallery_images)))

    def deselect_all(self):
        """Return empty selection list."""
        return []

    def invert_selected(self, gallery_images, images_selected_state):
        all_indices = set(range(len(gallery_images)))
        selected = set(images_selected_state)
        return sorted(list(all_indices - selected))

    def handle_select_all(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.select_all(gallery_images)
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def handle_deselect_all(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.deselect_all()
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def handle_invert_selection(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.invert_selected(gallery_images, images_selected_state)
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def compare_selected(self, gallery_images, images_selected_state):
        if len(images_selected_state) != 2:
            empty = [gr.update(value=None)] + [gr.update(choices=[], value=[]) for _ in range(7)]
            return empty + empty
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        self.compare_left_path = paths[0]
        self.compare_right_path = paths[1]
        # reset accumulated tag actions when a new pair is compared
        self.transfer_buffer = []
        self.remove_buffer = []

        left_tags = image_tag_tools.load_image_tags(paths[0])
        right_tags = image_tag_tools.load_image_tags(paths[1])

        def categorize(tags):
            groups = {"artist": [], "character": [], "species": [], "invalid": [], "general": [], "meta": [], "rating": []}
            for t in tags:
                cat = self.get_category_name(t)
                if cat not in groups:
                    cat = "invalid"
                groups[cat].append(t)
            return groups

        left_groups = categorize(left_tags)
        right_groups = categorize(right_tags)

        outputs = [gr.update(value=paths[0])]
        outputs += [gr.update(choices=left_groups[k], value=[]) for k in ["artist","character","species","invalid","general","meta","rating"]]
        outputs.append(gr.update(value=paths[1]))
        outputs += [gr.update(choices=right_groups[k], value=[]) for k in ["artist","character","species","invalid","general","meta","rating"]]
        return outputs

    def transfer_left_to_right(self, left_artist, left_character, left_species, left_invalid,
                               left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = [t.strip() for t in (
            left_artist + left_character + left_species + left_invalid +
            left_general + left_meta + left_rating
        )]
        image_tag_tools.transfer_tags(
            self.compare_left_path,
            self.compare_right_path,
            tags,
            remove=False,
        )
        self.transfer_buffer = sorted(set(self.transfer_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[8:]
        return groups[1:]

    def remove_left_from_right(self, left_artist, left_character, left_species, left_invalid,
                               left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = [t.strip() for t in (
            left_artist + left_character + left_species + left_invalid +
            left_general + left_meta + left_rating
        )]
        image_tag_tools.apply_tag_modifications(
            [self.compare_right_path],
            remove_tags=tags,
        )
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[8:]
        return groups[1:]

    def transfer_right_to_left(self, right_artist, right_character, right_species, right_invalid,
                               right_general, right_meta, right_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = [t.strip() for t in (
            right_artist + right_character + right_species + right_invalid +
            right_general + right_meta + right_rating
        )]
        image_tag_tools.transfer_tags(
            self.compare_right_path,
            self.compare_left_path,
            tags,
            remove=False,
        )
        self.transfer_buffer = sorted(set(self.transfer_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[:8]
        return groups[1:]

    def remove_right_from_left(self, right_artist, right_character, right_species, right_invalid,
                               right_general, right_meta, right_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = [t.strip() for t in (
            right_artist + right_character + right_species + right_invalid +
            right_general + right_meta + right_rating
        )]
        image_tag_tools.apply_tag_modifications(
            [self.compare_left_path],
            remove_tags=tags,
        )
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[:8]
        return groups[1:]

    def remove_left_from_both(self, left_artist, left_character, left_species, left_invalid,
                              left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        tags = [t.strip() for t in (
            left_artist + left_character + left_species + left_invalid +
            left_general + left_meta + left_rating
        )]
        image_tag_tools.apply_tag_modifications(
            [self.compare_left_path, self.compare_right_path],
            remove_tags=tags,
        )
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def remove_right_from_both(self, right_artist, right_character, right_species, right_invalid,
                               right_general, right_meta, right_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        tags = [t.strip() for t in (
            right_artist + right_character + right_species + right_invalid +
            right_general + right_meta + right_rating
        )]
        image_tag_tools.apply_tag_modifications(
            [self.compare_left_path, self.compare_right_path],
            remove_tags=tags,
        )
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def add_tag_left(self, tag, apply_both):
        if not tag or not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        clean_tag = tag.strip()
        targets = [self.compare_left_path]
        if apply_both:
            targets.append(self.compare_right_path)
        image_tag_tools.apply_tag_modifications(targets, add_tags=[clean_tag])
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def add_tag_right(self, tag, apply_both):
        if not tag or not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        clean_tag = tag.strip()
        targets = [self.compare_right_path]
        if apply_both:
            targets.append(self.compare_left_path)
        image_tag_tools.apply_tag_modifications(targets, add_tags=[clean_tag])
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def apply_transfer_to_selected(self, gallery_images, images_selected_state):
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        if self.transfer_buffer:
            image_tag_tools.apply_tag_modifications(paths, add_tags=self.transfer_buffer)
        return []

    def apply_remove_to_selected(self, gallery_images, images_selected_state):
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        if self.remove_buffer:
            image_tag_tools.apply_tag_modifications(paths, remove_tags=self.remove_buffer)
        return []

    def select_all(self, gallery_images):
        """Return indices of all images for selection."""
        return list(range(len(gallery_images)))

    def deselect_all(self):
        """Return empty selection list."""
        return []

    def invert_selected(self, gallery_images, images_selected_state):
        all_indices = set(range(len(gallery_images)))
        selected = set(images_selected_state)
        return sorted(list(all_indices - selected))

    def handle_select_all(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.select_all(gallery_images)
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def handle_deselect_all(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.deselect_all()
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def handle_invert_selection(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.invert_selected(gallery_images, images_selected_state)
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def compare_selected(self, gallery_images, images_selected_state):
        if len(images_selected_state) != 2:
            empty = [gr.update(value=None)] + [gr.update(choices=[], value=[]) for _ in range(7)]
            return empty + empty
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        self.compare_left_path = paths[0]
        self.compare_right_path = paths[1]
        # reset accumulated tag actions when a new pair is compared
        self.transfer_buffer = []
        self.remove_buffer = []

        left_tags = image_tag_tools.load_image_tags(paths[0])
        right_tags = image_tag_tools.load_image_tags(paths[1])

        def categorize(tags):
            groups = {"artist": [], "character": [], "species": [], "invalid": [], "general": [], "meta": [], "rating": []}
            for t in tags:
                cat = self.get_category_name(t)
                if cat not in groups:
                    cat = "invalid"
                groups[cat].append(t)
            return groups

        left_groups = categorize(left_tags)
        right_groups = categorize(right_tags)

        outputs = [gr.update(value=paths[0])]
        outputs += [gr.update(choices=left_groups[k], value=[]) for k in ["artist","character","species","invalid","general","meta","rating"]]
        outputs.append(gr.update(value=paths[1]))
        outputs += [gr.update(choices=right_groups[k], value=[]) for k in ["artist","character","species","invalid","general","meta","rating"]]
        return outputs

    def transfer_left_to_right(self, left_artist, left_character, left_species, left_invalid,
                               left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = [t.strip() for t in (
            left_artist + left_character + left_species + left_invalid +
            left_general + left_meta + left_rating
        )]
        image_tag_tools.transfer_tags(
            self.compare_left_path,
            self.compare_right_path,
            tags,
            remove=False,
        )
        self.transfer_buffer = sorted(set(self.transfer_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[8:]
        return groups[1:]

    def remove_left_from_right(self, left_artist, left_character, left_species, left_invalid,
                               left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = [t.strip() for t in (
            left_artist + left_character + left_species + left_invalid +
            left_general + left_meta + left_rating
        )]
        image_tag_tools.apply_tag_modifications(
            [self.compare_right_path],
            remove_tags=tags,
        )
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[8:]
        return groups[1:]

    def transfer_right_to_left(self, right_artist, right_character, right_species, right_invalid,
                               right_general, right_meta, right_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = [t.strip() for t in (
            right_artist + right_character + right_species + right_invalid +
            right_general + right_meta + right_rating
        )]
        image_tag_tools.transfer_tags(
            self.compare_right_path,
            self.compare_left_path,
            tags,
            remove=False,
        )
        self.transfer_buffer = sorted(set(self.transfer_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[:8]
        return groups[1:]

    def remove_right_from_left(self, right_artist, right_character, right_species, right_invalid,
                               right_general, right_meta, right_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = [t.strip() for t in (
            right_artist + right_character + right_species + right_invalid +
            right_general + right_meta + right_rating
        )]
        image_tag_tools.apply_tag_modifications(
            [self.compare_left_path],
            remove_tags=tags,
        )
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[:8]
        return groups[1:]

    def remove_left_from_both(self, left_artist, left_character, left_species, left_invalid,
                              left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        tags = [t.strip() for t in (
            left_artist + left_character + left_species + left_invalid +
            left_general + left_meta + left_rating
        )]
        image_tag_tools.apply_tag_modifications(
            [self.compare_left_path, self.compare_right_path],
            remove_tags=tags,
        )
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def remove_right_from_both(self, right_artist, right_character, right_species, right_invalid,
                               right_general, right_meta, right_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        tags = [t.strip() for t in (
            right_artist + right_character + right_species + right_invalid +
            right_general + right_meta + right_rating
        )]
        image_tag_tools.apply_tag_modifications(
            [self.compare_left_path, self.compare_right_path],
            remove_tags=tags,
        )
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def add_tag_left(self, tag, apply_both):
        if not tag or not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        clean_tag = tag.strip()
        targets = [self.compare_left_path]
        if apply_both:
            targets.append(self.compare_right_path)
        image_tag_tools.apply_tag_modifications(targets, add_tags=[clean_tag])
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def add_tag_right(self, tag, apply_both):
        if not tag or not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        clean_tag = tag.strip()
        targets = [self.compare_right_path]
        if apply_both:
            targets.append(self.compare_left_path)
        image_tag_tools.apply_tag_modifications(targets, add_tags=[clean_tag])
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def apply_transfer_to_selected(self, gallery_images, images_selected_state):
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        if self.transfer_buffer:
            image_tag_tools.apply_tag_modifications(paths, add_tags=self.transfer_buffer)
        return []

    def apply_remove_to_selected(self, gallery_images, images_selected_state):
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        if self.remove_buffer:
            image_tag_tools.apply_tag_modifications(paths, remove_tags=self.remove_buffer)
        return []

    def select_all(self, gallery_images):
        """Return indices of all images for selection."""
        return list(range(len(gallery_images)))

    def deselect_all(self):
        """Return empty selection list."""
        return []

    def invert_selected(self, gallery_images, images_selected_state):
        all_indices = set(range(len(gallery_images)))
        selected = set(images_selected_state)
        return sorted(list(all_indices - selected))

    def handle_select_all(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.select_all(gallery_images)
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def handle_deselect_all(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.deselect_all()
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def handle_invert_selection(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.invert_selected(gallery_images, images_selected_state)
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def compare_selected(self, gallery_images, images_selected_state):
        if len(images_selected_state) != 2:
            empty = [gr.update(value=None)] + [gr.update(choices=[], value=[]) for _ in range(7)]
            return empty + empty
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        self.compare_left_path = paths[0]
        self.compare_right_path = paths[1]
        # reset accumulated tag actions when a new pair is compared
        self.transfer_buffer = []
        self.remove_buffer = []

        left_tags = image_tag_tools.load_image_tags(paths[0])
        right_tags = image_tag_tools.load_image_tags(paths[1])

        def categorize(tags):
            groups = {"artist": [], "character": [], "species": [], "invalid": [], "general": [], "meta": [], "rating": []}
            for t in tags:
                cat = self.get_category_name(t)
                if cat not in groups:
                    cat = "invalid"
                groups[cat].append(t)
            return groups

        left_groups = categorize(left_tags)
        right_groups = categorize(right_tags)

        outputs = [gr.update(value=paths[0])]
        outputs += [gr.update(choices=left_groups[k], value=[]) for k in ["artist","character","species","invalid","general","meta","rating"]]
        outputs.append(gr.update(value=paths[1]))
        outputs += [gr.update(choices=right_groups[k], value=[]) for k in ["artist","character","species","invalid","general","meta","rating"]]
        return outputs

    def transfer_left_to_right(self, left_artist, left_character, left_species, left_invalid,
                               left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = [t.strip() for t in (
            left_artist + left_character + left_species + left_invalid +
            left_general + left_meta + left_rating
        )]
        image_tag_tools.transfer_tags(
            self.compare_left_path,
            self.compare_right_path,
            tags,
            remove=False,
        )
        self.transfer_buffer = sorted(set(self.transfer_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[8:]
        return groups[1:]

    def remove_left_from_right(self, left_artist, left_character, left_species, left_invalid,
                               left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = [t.strip() for t in (
            left_artist + left_character + left_species + left_invalid +
            left_general + left_meta + left_rating
        )]
        image_tag_tools.apply_tag_modifications(
            [self.compare_right_path],
            remove_tags=tags,
        )
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[8:]
        return groups[1:]

    def transfer_right_to_left(self, right_artist, right_character, right_species, right_invalid,
                               right_general, right_meta, right_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = [t.strip() for t in (
            right_artist + right_character + right_species + right_invalid +
            right_general + right_meta + right_rating
        )]
        image_tag_tools.transfer_tags(
            self.compare_right_path,
            self.compare_left_path,
            tags,
            remove=False,
        )
        self.transfer_buffer = sorted(set(self.transfer_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[:8]
        return groups[1:]

    def remove_right_from_left(self, right_artist, right_character, right_species, right_invalid,
                               right_general, right_meta, right_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = [t.strip() for t in (
            right_artist + right_character + right_species + right_invalid +
            right_general + right_meta + right_rating
        )]
        image_tag_tools.apply_tag_modifications(
            [self.compare_left_path],
            remove_tags=tags,
        )
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[:8]
        return groups[1:]

    def remove_left_from_both(self, left_artist, left_character, left_species, left_invalid,
                              left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        tags = [t.strip() for t in (
            left_artist + left_character + left_species + left_invalid +
            left_general + left_meta + left_rating
        )]
        image_tag_tools.apply_tag_modifications(
            [self.compare_left_path, self.compare_right_path],
            remove_tags=tags,
        )
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def remove_right_from_both(self, right_artist, right_character, right_species, right_invalid,
                               right_general, right_meta, right_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        tags = [t.strip() for t in (
            right_artist + right_character + right_species + right_invalid +
            right_general + right_meta + right_rating
        )]
        image_tag_tools.apply_tag_modifications(
            [self.compare_left_path, self.compare_right_path],
            remove_tags=tags,
        )
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def add_tag_left(self, tag, apply_both):
        if not tag or not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        clean_tag = tag.strip()
        targets = [self.compare_left_path]
        if apply_both:
            targets.append(self.compare_right_path)
        image_tag_tools.apply_tag_modifications(targets, add_tags=[clean_tag])
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def add_tag_right(self, tag, apply_both):
        if not tag or not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        clean_tag = tag.strip()
        targets = [self.compare_right_path]
        if apply_both:
            targets.append(self.compare_left_path)
        image_tag_tools.apply_tag_modifications(targets, add_tags=[clean_tag])
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def apply_transfer_to_selected(self, gallery_images, images_selected_state):
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        if self.transfer_buffer:
            image_tag_tools.apply_tag_modifications(paths, add_tags=self.transfer_buffer)
        return []

    def apply_remove_to_selected(self, gallery_images, images_selected_state):
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        if self.remove_buffer:
            image_tag_tools.apply_tag_modifications(paths, remove_tags=self.remove_buffer)
        return []

    def select_all(self, gallery_images):
        """Return indices of all images for selection."""
        return list(range(len(gallery_images)))

    def deselect_all(self):
        """Return empty selection list."""
        return []

    def invert_selected(self, gallery_images, images_selected_state):
        all_indices = set(range(len(gallery_images)))
        selected = set(images_selected_state)
        return sorted(list(all_indices - selected))

    def handle_select_all(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.select_all(gallery_images)
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def handle_deselect_all(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.deselect_all()
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def handle_invert_selection(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.invert_selected(gallery_images, images_selected_state)
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def compare_selected(self, gallery_images, images_selected_state):
        if len(images_selected_state) != 2:
            empty = [gr.update(value=None)] + [gr.update(choices=[], value=[]) for _ in range(7)]
            return empty + empty
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        self.compare_left_path = paths[0]
        self.compare_right_path = paths[1]
        # reset accumulated tag actions when a new pair is compared
        self.transfer_buffer = []
        self.remove_buffer = []

        left_tags = image_tag_tools.load_image_tags(paths[0])
        right_tags = image_tag_tools.load_image_tags(paths[1])

        def categorize(tags):
            groups = {"artist": [], "character": [], "species": [], "invalid": [], "general": [], "meta": [], "rating": []}
            for t in tags:
                cat = self.get_category_name(t)
                if cat not in groups:
                    cat = "invalid"
                groups[cat].append(t)
            return groups

        left_groups = categorize(left_tags)
        right_groups = categorize(right_tags)

        outputs = [gr.update(value=paths[0])]
        outputs += [gr.update(choices=left_groups[k], value=[]) for k in ["artist","character","species","invalid","general","meta","rating"]]
        outputs.append(gr.update(value=paths[1]))
        outputs += [gr.update(choices=right_groups[k], value=[]) for k in ["artist","character","species","invalid","general","meta","rating"]]
        return outputs

    def transfer_left_to_right(self, left_artist, left_character, left_species, left_invalid,
                               left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = left_artist + left_character + left_species + left_invalid + left_general + left_meta + left_rating
        image_tag_tools.transfer_tags(self.compare_left_path, self.compare_right_path, tags, remove=False)
        self.transfer_buffer = sorted(set(self.transfer_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[8:]
        return groups[1:]

    def remove_left_from_right(self, left_artist, left_character, left_species, left_invalid,
                               left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = left_artist + left_character + left_species + left_invalid + left_general + left_meta + left_rating
        image_tag_tools.apply_tag_modifications([self.compare_right_path], remove_tags=tags)
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[8:]
        return groups[1:]

    def transfer_right_to_left(self, right_artist, right_character, right_species, right_invalid,
                               right_general, right_meta, right_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = right_artist + right_character + right_species + right_invalid + right_general + right_meta + right_rating
        image_tag_tools.transfer_tags(self.compare_right_path, self.compare_left_path, tags, remove=False)
        self.transfer_buffer = sorted(set(self.transfer_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[:8]
        return groups[1:]

    def remove_right_from_left(self, right_artist, right_character, right_species, right_invalid,
                               right_general, right_meta, right_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = right_artist + right_character + right_species + right_invalid + right_general + right_meta + right_rating
        image_tag_tools.apply_tag_modifications([self.compare_left_path], remove_tags=tags)
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[:8]
        return groups[1:]

    def remove_left_from_both(self, left_artist, left_character, left_species, left_invalid,
                              left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        tags = left_artist + left_character + left_species + left_invalid + left_general + left_meta + left_rating
        image_tag_tools.apply_tag_modifications([self.compare_left_path, self.compare_right_path], remove_tags=tags)
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def remove_right_from_both(self, right_artist, right_character, right_species, right_invalid,
                               right_general, right_meta, right_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        tags = right_artist + right_character + right_species + right_invalid + right_general + right_meta + right_rating
        image_tag_tools.apply_tag_modifications([self.compare_left_path, self.compare_right_path], remove_tags=tags)
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def add_tag_left(self, tag, apply_both):
        if not tag or not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        targets = [self.compare_left_path]
        if apply_both:
            targets.append(self.compare_right_path)
        image_tag_tools.apply_tag_modifications(targets, add_tags=[tag])
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def add_tag_right(self, tag, apply_both):
        if not tag or not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(14)]
        targets = [self.compare_right_path]
        if apply_both:
            targets.append(self.compare_left_path)
        image_tag_tools.apply_tag_modifications(targets, add_tags=[tag])
        outputs = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])
        return outputs[1:8] + outputs[9:]

    def apply_transfer_to_selected(self, gallery_images, images_selected_state):
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        if self.transfer_buffer:
            image_tag_tools.apply_tag_modifications(paths, add_tags=self.transfer_buffer)
        return []

    def apply_remove_to_selected(self, gallery_images, images_selected_state):
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        if self.remove_buffer:
            image_tag_tools.apply_tag_modifications(paths, remove_tags=self.remove_buffer)
        return []

    def select_all(self, gallery_images):
        """Return indices of all images for selection."""
        return list(range(len(gallery_images)))

    def deselect_all(self):
        """Return empty selection list."""
        return []

    def invert_selected(self, gallery_images, images_selected_state):
        all_indices = set(range(len(gallery_images)))
        selected = set(images_selected_state)
        return sorted(list(all_indices - selected))

    def handle_select_all(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.select_all(gallery_images)
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def handle_deselect_all(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.deselect_all()
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def handle_invert_selection(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.invert_selected(gallery_images, images_selected_state)
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def compare_selected(self, gallery_images, images_selected_state):
        if len(images_selected_state) != 2:
            empty = [gr.update(value=None)] + [gr.update(choices=[], value=[]) for _ in range(7)]
            return empty + empty
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        self.compare_left_path = paths[0]
        self.compare_right_path = paths[1]
        # reset accumulated tag actions when a new pair is compared
        self.transfer_buffer = []
        self.remove_buffer = []

        left_tags = help.parse_single_all_tags(os.path.splitext(paths[0])[0] + ".txt")
        right_tags = help.parse_single_all_tags(os.path.splitext(paths[1])[0] + ".txt")

        def categorize(tags):
            groups = {"artist": [], "character": [], "species": [], "invalid": [], "general": [], "meta": [], "rating": []}
            for t in tags:
                cat = self.get_category_name(t)
                if cat not in groups:
                    cat = "invalid"
                groups[cat].append(t)
            return groups

        left_groups = categorize(left_tags)
        right_groups = categorize(right_tags)

        outputs = [gr.update(value=paths[0])]
        outputs += [gr.update(choices=left_groups[k], value=[]) for k in ["artist","character","species","invalid","general","meta","rating"]]
        outputs.append(gr.update(value=paths[1]))
        outputs += [gr.update(choices=right_groups[k], value=[]) for k in ["artist","character","species","invalid","general","meta","rating"]]
        return outputs

    def transfer_left_to_right(self, left_artist, left_character, left_species, left_invalid,
                               left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = left_artist + left_character + left_species + left_invalid + left_general + left_meta + left_rating
        image_tag_tools.transfer_tags(self.compare_left_path, self.compare_right_path, tags, remove=False)
        self.transfer_buffer = sorted(set(self.transfer_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[8:]
        return groups[1:]

    def remove_left_from_right(self, left_artist, left_character, left_species, left_invalid,
                               left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = left_artist + left_character + left_species + left_invalid + left_general + left_meta + left_rating
        image_tag_tools.apply_tag_modifications([self.compare_right_path], remove_tags=tags)
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[8:]
        return groups[1:]

    def transfer_right_to_left(self, right_artist, right_character, right_species, right_invalid,
                               right_general, right_meta, right_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = right_artist + right_character + right_species + right_invalid + right_general + right_meta + right_rating
        image_tag_tools.transfer_tags(self.compare_right_path, self.compare_left_path, tags, remove=False)
        self.transfer_buffer = sorted(set(self.transfer_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[:8]
        return groups[1:]

    def remove_right_from_left(self, right_artist, right_character, right_species, right_invalid,
                               right_general, right_meta, right_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = right_artist + right_character + right_species + right_invalid + right_general + right_meta + right_rating
        image_tag_tools.apply_tag_modifications([self.compare_left_path], remove_tags=tags)
        self.remove_buffer = sorted(set(self.remove_buffer + tags))
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[:8]
        return groups[1:]

    def apply_transfer_to_selected(self, gallery_images, images_selected_state):
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        if self.transfer_buffer:
            image_tag_tools.apply_tag_modifications(paths, add_tags=self.transfer_buffer)
        return []

    def apply_remove_to_selected(self, gallery_images, images_selected_state):
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        if self.remove_buffer:
            image_tag_tools.apply_tag_modifications(paths, remove_tags=self.remove_buffer)
        return []

    def select_all(self, gallery_images):
        """Return indices of all images for selection."""
        return list(range(len(gallery_images)))

    def deselect_all(self):
        """Return empty selection list."""
        return []

    def invert_selected(self, gallery_images, images_selected_state):
        all_indices = set(range(len(gallery_images)))
        selected = set(images_selected_state)
        return sorted(list(all_indices - selected))

    def handle_select_all(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.select_all(gallery_images)
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def handle_deselect_all(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.deselect_all()
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def handle_invert_selection(self, gallery_images, images_selected_state, toggle):
        if toggle:
            images_selected_state = self.invert_selected(gallery_images, images_selected_state)
        mapping = self._build_selection_mapping(gallery_images, images_selected_state)
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = images_selected_state
        self.only_selected_state_object.value = mapping
        self._debug_selection(images_selected_state, mapping)
        return images_selected_state, mapping, gr.update(value=False)

    def compare_selected(self, gallery_images, images_selected_state):
        if len(images_selected_state) != 2:
            empty = [gr.update(value=None)] + [gr.update(choices=[], value=[]) for _ in range(7)]
            return empty + empty
        paths = [gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                 for idx in images_selected_state]
        self.compare_left_path = paths[0]
        self.compare_right_path = paths[1]

        left_tags = help.parse_single_all_tags(os.path.splitext(paths[0])[0] + ".txt")
        right_tags = help.parse_single_all_tags(os.path.splitext(paths[1])[0] + ".txt")

        def categorize(tags):
            groups = {"artist": [], "character": [], "species": [], "invalid": [], "general": [], "meta": [], "rating": []}
            for t in tags:
                cat = self.get_category_name(t)
                if cat not in groups:
                    cat = "invalid"
                groups[cat].append(t)
            return groups

        left_groups = categorize(left_tags)
        right_groups = categorize(right_tags)

        outputs = [gr.update(value=paths[0])]
        outputs += [gr.update(choices=left_groups[k], value=[]) for k in ["artist","character","species","invalid","general","meta","rating"]]
        outputs.append(gr.update(value=paths[1]))
        outputs += [gr.update(choices=right_groups[k], value=[]) for k in ["artist","character","species","invalid","general","meta","rating"]]
        return outputs

    def transfer_left_to_right(self, left_artist, left_character, left_species, left_invalid,
                               left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = left_artist + left_character + left_species + left_invalid + left_general + left_meta + left_rating
        image_tag_tools.transfer_tags(self.compare_left_path, self.compare_right_path, tags, remove=False)
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[8:]
        return groups[1:]

    def remove_left_from_right(self, left_artist, left_character, left_species, left_invalid,
                               left_general, left_meta, left_rating):
        if not hasattr(self, "compare_left_path") or not hasattr(self, "compare_right_path"):
            return [gr.update() for _ in range(7)]
        tags = left_artist + left_character + left_species + left_invalid + left_general + left_meta + left_rating
        image_tag_tools.apply_tag_modifications([self.compare_right_path], remove_tags=tags)
        groups = self.compare_selected([self.compare_left_path, self.compare_right_path], [0,1])[8:]
        return groups[1:]

    ######
    # self.all_images_dict ->
    ### image_type -> {img_id, tags}
    ### searched -> {img_id, tags}
    ######
    def show_gallery(self, folder_type_select, sort_images, sort_option):
        self.current_media_mode = folder_type_select
        help.verbose_print(f"self.download_tab_manager.is_csv_loaded:\t{self.download_tab_manager.is_csv_loaded}")

        images = []
        if folder_type_select is not None:
            help.verbose_print(f"folder_type_select:\t{folder_type_select}")
            temp = '\\' if help.is_windows() else '/'
            # clear searched dict
            if "searched" in self.all_images_dict:
                del self.all_images_dict["searched"]
                self.all_images_dict["searched"] = {}

            if self.custom_dataset_loaded:
                base_path = self.custom_dataset_dir
            else:
                base_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
                base_path = os.path.join(base_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])

            # determine extensions based on mode
            if folder_type_select in ["images", "videos"]:
                exts = self.image_formats if folder_type_select == "images" else self.video_formats
            else:
                exts = [folder_type_select]

            if self.custom_dataset_loaded:
                for ext in exts:
                    for img_id in self.all_images_dict.get(ext, {}).keys():
                        img_path = self.search_image_paths.get((ext, img_id))
                        if not img_path:
                            img_path = os.path.join(base_path, f"{img_id}.{ext}")
                        images.append(img_path)
            else:
                if folder_type_select in ["images", "videos"]:
                    for ext in exts:
                        folder_key = f"{ext}_folder"
                        folder = self.download_tab_manager.settings_json.get(folder_key)
                        if not folder:
                            continue
                        path = os.path.join(base_path, folder)
                        images.extend(glob.glob(os.path.join(path, f"*.{ext}")))
                else:
                    folder_path = os.path.join(base_path, self.download_tab_manager.settings_json[f"{folder_type_select}_folder"])
                    if not self.all_images_dict or len(self.all_images_dict.keys()) == 0 or \
                            (folder_type_select in self.all_images_dict.keys() and len(self.all_images_dict[folder_type_select].keys()) == 0) or \
                            not self.download_tab_manager.is_csv_loaded:
                        images = glob.glob(os.path.join(folder_path, f"*.{folder_type_select}"))
                        help.verbose_print(f"images:\t{images}")
                    else:  # render from existing dictionary
                        for name in list(self.all_images_dict[folder_type_select].keys()):
                            images.append(os.path.join(folder_path, f"{str(name)}.{folder_type_select}"))

            if not self.custom_dataset_loaded and not self.download_tab_manager.is_csv_loaded:
                full_path_downloads = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                                   self.download_tab_manager.settings_json["downloaded_posts_folder"])

                tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                             self.download_tab_manager.settings_json["tag_count_list_folder"])


                if not self.all_images_dict or len(self.all_images_dict.keys()) == 0 or \
                    not self.download_tab_manager.is_csv_loaded:
                    folder_paths = []
                    for key, val in self.download_tab_manager.settings_json.items():
                        if key.endswith("_folder") and key not in ["batch_folder", "downloaded_posts_folder", "tag_count_list_folder", "resized_img_folder"]:
                            folder_paths.append(os.path.join(full_path_downloads, val))
                    self.all_images_dict = help.gather_media_tags(*folder_paths)

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
        try:
            self.gallery_state.value = images
        except Exception:
            pass
        count = self.get_total_image_count()
        return (
            gr.update(value=images, visible=True),
            gr.update(value=f"Total Images: {count}"),
            images,
        )

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
    def get_img_tags(self, gallery_images, select_multiple_images_checkbox, images_selected_state,
                     select_between_images_checkbox, images_tuple_points, event_data: gr.SelectData):
        # self.selected_image_dict  # id -> {categories: tag/s}, type -> string
        temp = '\\' if help.is_windows() else '/'
        help.verbose_print(f"event_data:\t{event_data}")
        help.verbose_print(f"event_data.index:\t{event_data.index}")
        help.verbose_print(f"gallery_images[event_data.index]:\t{gallery_images[event_data.index]}")
        help.verbose_print(f"full_path:\t{(gallery_images[event_data.index])[0] if isinstance(gallery_images[event_data.index], (list, tuple)) else gallery_images[event_data.index]}")
        help.verbose_print(f"image name:\t{(gallery_images[event_data.index])[0].split(temp)[-1] if isinstance(gallery_images[event_data.index], (list, tuple)) else str(gallery_images[event_data.index]).split(temp)[-1]}")

        img_name_update = gr.update()
        artist_comp_checkboxgroup = gr.update()
        character_comp_checkboxgroup = gr.update()
        species_comp_checkboxgroup = gr.update()
        invalid_comp_checkboxgroup = gr.update()
        general_comp_checkboxgroup = gr.update()
        meta_comp_checkboxgroup = gr.update()
        rating_comp_checkboxgroup = gr.update()

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
            img_path = gallery_images[event_data.index][0] if isinstance(gallery_images[event_data.index], (list, tuple)) else gallery_images[event_data.index]
            download_folder_type, img_name = self.extract_name_and_extention(img_path)

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

            img_name_update = gr.update(value=img_name)
            artist_comp_checkboxgroup = gr.update(choices=self.selected_image_dict[img_name]["artist"])
            character_comp_checkboxgroup = gr.update(choices=self.selected_image_dict[img_name]["character"])
            species_comp_checkboxgroup = gr.update(choices=self.selected_image_dict[img_name]["species"])
            invalid_comp_checkboxgroup = gr.update(choices=self.selected_image_dict[img_name]["invalid"])
            general_comp_checkboxgroup = gr.update(choices=self.selected_image_dict[img_name]["general"])
            meta_comp_checkboxgroup = gr.update(choices=self.selected_image_dict[img_name]["meta"])
            rating_comp_checkboxgroup = gr.update(choices=self.selected_image_dict[img_name]["rating"])

        only_selected_state_object = dict()
        for index in images_selected_state:
            img_path = gallery_images[index][0] if isinstance(gallery_images[index], (list, tuple)) else gallery_images[index]
            only_selected_state_object[index] = self.extract_name_and_extention(img_path)
        help.verbose_print(f"only_selected_state_object:\t{only_selected_state_object}")

        return img_name_update, artist_comp_checkboxgroup, character_comp_checkboxgroup, species_comp_checkboxgroup, \
               invalid_comp_checkboxgroup, general_comp_checkboxgroup, meta_comp_checkboxgroup, rating_comp_checkboxgroup, images_selected_state, only_selected_state_object, \
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
        if self.custom_dataset_loaded:
            base_path = self.custom_dataset_dir
        else:
            base_path = os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"])
            base_path = os.path.join(base_path, self.download_tab_manager.settings_json["downloaded_posts_folder"])

        images = []
        if folder_type_select in ["images", "videos"]:
            exts = self.image_formats if folder_type_select == "images" else self.video_formats
        else:
            exts = [folder_type_select]

        if self.custom_dataset_loaded:
            for ext in exts:
                for img_id in self.all_images_dict.get(ext, {}).keys():
                    img_path = self.search_image_paths.get((ext, img_id))
                    if not img_path:
                        img_path = os.path.join(base_path, f"{img_id}.{ext}")
                    images.append(img_path)
        else:
            if folder_type_select in ["images", "videos"]:
                for ext in exts:
                    folder_key = f"{ext}_folder"
                    folder = self.download_tab_manager.settings_json.get(folder_key)
                    if not folder:
                        continue
                    path = os.path.join(base_path, folder)
                    images.extend(glob.glob(os.path.join(path, f"*.{ext}")))
            else:
                folder_path = os.path.join(base_path, self.download_tab_manager.settings_json[f"{folder_type_select}_folder"])
                if not self.all_images_dict or len(self.all_images_dict.keys()) == 0 or \
                        (folder_type_select in self.all_images_dict.keys() and len(self.all_images_dict[folder_type_select].keys()) == 0) or \
                        not self.download_tab_manager.is_csv_loaded:
                    images = glob.glob(os.path.join(folder_path, f"*.{folder_type_select}"))
                else:
                    for name in list(self.all_images_dict[folder_type_select].keys()):
                        images.append(os.path.join(folder_path, f"{str(name)}.{folder_type_select}"))

        self.download_tab_manager.is_csv_loaded = False

        if not self.custom_dataset_loaded and not self.download_tab_manager.is_csv_loaded:
            full_path_downloads = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                               self.download_tab_manager.settings_json["downloaded_posts_folder"])

            tag_count_dir = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                         self.download_tab_manager.settings_json["tag_count_list_folder"])

            if not self.all_images_dict or len(self.all_images_dict.keys()) == 0 or \
                    not self.download_tab_manager.is_csv_loaded:
                folder_paths = []
                for key, val in self.download_tab_manager.settings_json.items():
                    if key.endswith("_folder") and key not in ["batch_folder", "downloaded_posts_folder", "tag_count_list_folder", "resized_img_folder"]:
                        folder_paths.append(os.path.join(full_path_downloads, val))
                self.all_images_dict = help.gather_media_tags(*folder_paths)

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
        try:
            self.gallery_state.value = images
        except Exception:
            pass
        # reset any previous selections on reload
        self.images_selected_state.value = []
        self.only_selected_state_object.value = {}
        self._debug_selection([], {})
        count = self.get_total_image_count()
        return (
            gr.update(value=images, visible=True),
            gr.update(value=f"Total Images: {count}"),
            images,
        )

    def reset_gallery_component_only(self):
        help.verbose_print("reset_gallery_component_only")
        try:
            self.gallery_state.value = []
        except Exception:
            pass
        gallery_comp = gr.update(value=[], visible=True)
        total_count = gr.update(value="Total Images: 0")
        return gallery_comp, total_count

    def reset_gallery_manager(self):
        download_folder_type = gr.update(value=None)
        img_id_textbox = gr.update(value="")
        tag_search_textbox = gr.update(value="")
        tag_search_suggestion_dropdown = gr.update(value=None)
        apply_to_all_type_select_checkboxgroup = gr.update(value=[])
        select_multiple_images_checkbox = gr.update(value=False)
        select_between_images_checkbox = gr.update(value=False)
        select_all_checkbox = gr.update(value=False)
        deselect_all_checkbox = gr.update(value=False)
        invert_selection_checkbox = gr.update(value=False)
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
        compare_button = gr.update()
        compare_image_left = gr.update(value=None)
        comp_left_artist = gr.update(choices=[], value=[])
        comp_left_character = gr.update(choices=[], value=[])
        comp_left_species = gr.update(choices=[], value=[])
        comp_left_invalid = gr.update(choices=[], value=[])
        comp_left_general = gr.update(choices=[], value=[])
        comp_left_meta = gr.update(choices=[], value=[])
        comp_left_rating = gr.update(choices=[], value=[])
        compare_image_right = gr.update(value=None)
        comp_right_artist = gr.update(choices=[], value=[])
        comp_right_character = gr.update(choices=[], value=[])
        comp_right_species = gr.update(choices=[], value=[])
        comp_right_invalid = gr.update(choices=[], value=[])
        comp_right_general = gr.update(choices=[], value=[])
        comp_right_meta = gr.update(choices=[], value=[])
        comp_right_rating = gr.update(choices=[], value=[])
        transfer_tags_button = gr.update()
        remove_tags_button = gr.update()
        remove_tags_both_l_button = gr.update()
        transfer_tags_button_rl = gr.update()
        remove_tags_button_rl = gr.update()
        remove_tags_both_r_button = gr.update()
        comp_left_add_text = gr.update(value="")
        comp_right_add_text = gr.update(value="")
        comp_add_to_both_checkbox = gr.update(value=False)
        apply_transfer_button = gr.update()
        apply_remove_button = gr.update()

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
                select_all_checkbox,
                deselect_all_checkbox,
                invert_selection_checkbox,
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
                gallery_comp,
                compare_button,
                compare_image_left,
                comp_left_artist,
                comp_left_character,
                comp_left_species,
                comp_left_invalid,
                comp_left_general,
                comp_left_meta,
                comp_left_rating,
                compare_image_right,
                comp_right_artist,
                comp_right_character,
                comp_right_species,
                comp_right_invalid,
                comp_right_general,
                comp_right_meta,
                comp_right_rating,
                transfer_tags_button,
                remove_tags_button,
                transfer_tags_button_rl,
                remove_tags_button_rl,
                apply_transfer_button,
                apply_remove_button
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
                ordered = help.sort_tags_by_priority(self.all_images_dict[ext][img_id], self.get_category_name)
                self.all_images_dict[ext][img_id] = ordered
                temp_tag_string = ", ".join(ordered)
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
                ordered = help.sort_tags_by_priority(self.all_images_dict[ext][img_id], self.get_category_name)
                self.all_images_dict[ext][img_id] = ordered
                temp_tag_string = ", ".join(ordered)
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
                ordered = help.sort_tags_by_priority(self.all_images_dict[ext][img_id], self.get_category_name)
                self.all_images_dict[ext][img_id] = ordered
                temp_tag_string = ", ".join(ordered)
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
                        download_folder_type = gr.Radio(choices=self.file_extn_list, label='Gallery Mode', value='images')
                        img_id_textbox = gr.Textbox(label="Image ID", interactive=False, lines=1, value="")
                        total_image_counter = gr.Markdown(f"Total Images: {self.get_total_image_count()}")
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
                                select_all_checkbox = gr.Checkbox(label="Select All", value=False)
                            with gr.Column(min_width=50, scale=1):
                                deselect_all_checkbox = gr.Checkbox(label="Deselect All", value=False)
                            with gr.Column(min_width=50, scale=1):
                                invert_selection_checkbox = gr.Checkbox(label="Invert", value=False)
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
                        with gr.Row():
                            compare_button = gr.Button(value="Compare Selected", variant='secondary')
                        with gr.Row():
                            with gr.Column():
                                compare_image_left = gr.Image(type="filepath")
                                comp_left_artist = gr.CheckboxGroup(label='Artist Tag/s', choices=[])
                                comp_left_character = gr.CheckboxGroup(label='Character Tag/s', choices=[])
                                comp_left_species = gr.CheckboxGroup(label='Species Tag/s', choices=[])
                                comp_left_invalid = gr.CheckboxGroup(label='Invalid Tag/s', choices=[])
                                comp_left_general = gr.CheckboxGroup(label='General Tag/s', choices=[])
                                comp_left_meta = gr.CheckboxGroup(label='Meta Tag/s', choices=[])
                                comp_left_rating = gr.CheckboxGroup(label='Rating Tag/s', choices=[])
                            with gr.Column():
                                compare_image_right = gr.Image(type="filepath")
                                comp_right_artist = gr.CheckboxGroup(label='Artist Tag/s', choices=[])
                                comp_right_character = gr.CheckboxGroup(label='Character Tag/s', choices=[])
                                comp_right_species = gr.CheckboxGroup(label='Species Tag/s', choices=[])
                                comp_right_invalid = gr.CheckboxGroup(label='Invalid Tag/s', choices=[])
                                comp_right_general = gr.CheckboxGroup(label='General Tag/s', choices=[])
                                comp_right_meta = gr.CheckboxGroup(label='Meta Tag/s', choices=[])
                                comp_right_rating = gr.CheckboxGroup(label='Rating Tag/s', choices=[])
                        with gr.Row():
                            transfer_tags_button = gr.Button(value="Transfer Left Tags → Right", variant='secondary')
                            remove_tags_button = gr.Button(value="Remove Left Tags from Right", variant='secondary')
                            remove_tags_both_l_button = gr.Button(value="Remove Left Tags from Both", variant='secondary')
                            transfer_tags_button_rl = gr.Button(value="Transfer Right Tags → Left", variant='secondary')
                            remove_tags_button_rl = gr.Button(value="Remove Right Tags from Left", variant='secondary')
                            remove_tags_both_r_button = gr.Button(value="Remove Right Tags from Both", variant='secondary')
                        with gr.Row():
                            comp_left_add_text = gr.Textbox(label="Add Tag Left", lines=1)
                            comp_right_add_text = gr.Textbox(label="Add Tag Right", lines=1)
                            comp_add_to_both_checkbox = gr.Checkbox(label="Apply tag to both")
                        with gr.Row():
                            apply_transfer_button = gr.Button(value="Apply Transfer Tags to Selected", variant='primary')
                            apply_remove_button = gr.Button(value="Apply Remove Tags to Selected", variant='primary')

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
                        img_invalid_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Invalid Tag/s', value=[])
                        img_general_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='General Tag/s', value=[])
                        img_meta_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Meta Tag/s', value=[])
                        img_rating_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Rating Tag/s', value=[])
                        with gr.Accordion("Groups", open=False):
                            groups_dropdown = gr.Dropdown(label="Saved Groups", choices=list(self.groups_state.value.keys()), multiselect=True)
                            group_name_text = gr.Textbox(label="Group Name", lines=1)
                            with gr.Row():
                                save_group_button = gr.Button(value="Save Group", variant='primary')
                                load_group_button = gr.Button(value="Load Group", variant='secondary')
                                delete_group_button = gr.Button(value="Delete Group", variant='stop')
                            with gr.Row():
                                rename_group_button = gr.Button(value="Rename Group")
                                duplicate_group_button = gr.Button(value="Duplicate Group")
                            with gr.Row():
                                save_groups_cfg_button = gr.Button(value="Save Config")
                                load_groups_cfg_button = gr.Button(value="Load Config")
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
        self.select_all_checkbox = select_all_checkbox
        self.deselect_all_checkbox = deselect_all_checkbox
        self.invert_selection_checkbox = invert_selection_checkbox
        self.apply_datetime_sort_ckbx = apply_datetime_sort_ckbx
        self.apply_datetime_choice_menu = apply_datetime_choice_menu
        self.image_remove_button = image_remove_button
        self.image_save_ids_button = image_save_ids_button
        self.send_img_from_gallery_dropdown = send_img_from_gallery_dropdown
        self.batch_send_from_gallery_checkbox = batch_send_from_gallery_checkbox
        self.send_img_from_gallery_button = send_img_from_gallery_button
        self.compare_button = compare_button
        self.compare_image_left = compare_image_left
        self.comp_left_artist = comp_left_artist
        self.comp_left_character = comp_left_character
        self.comp_left_species = comp_left_species
        self.comp_left_invalid = comp_left_invalid
        self.comp_left_general = comp_left_general
        self.comp_left_meta = comp_left_meta
        self.comp_left_rating = comp_left_rating
        self.compare_image_right = compare_image_right
        self.comp_right_artist = comp_right_artist
        self.comp_right_character = comp_right_character
        self.comp_right_species = comp_right_species
        self.comp_right_invalid = comp_right_invalid
        self.comp_right_general = comp_right_general
        self.comp_right_meta = comp_right_meta
        self.comp_right_rating = comp_right_rating
        self.transfer_tags_button = transfer_tags_button
        self.remove_tags_button = remove_tags_button
        self.remove_tags_both_l_button = remove_tags_both_l_button
        self.transfer_tags_button_rl = transfer_tags_button_rl
        self.remove_tags_button_rl = remove_tags_button_rl
        self.remove_tags_both_r_button = remove_tags_both_r_button
        self.comp_left_add_text = comp_left_add_text
        self.comp_right_add_text = comp_right_add_text
        self.comp_add_to_both_checkbox = comp_add_to_both_checkbox
        self.apply_transfer_button = apply_transfer_button
        self.apply_remove_button = apply_remove_button
        self.tag_remove_button = tag_remove_button
        self.tag_save_button = tag_save_button
        self.tag_add_textbox = tag_add_textbox
        self.tag_add_suggestion_dropdown = tag_add_suggestion_dropdown
        self.category_filter_gallery_dropdown = category_filter_gallery_dropdown
        self.tag_effects_gallery_dropdown = tag_effects_gallery_dropdown
        self.img_artist_tag_checkbox_group = img_artist_tag_checkbox_group
        self.img_character_tag_checkbox_group = img_character_tag_checkbox_group
        self.img_species_tag_checkbox_group = img_species_tag_checkbox_group
        self.img_invalid_tag_checkbox_group = img_invalid_tag_checkbox_group
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
        self.total_image_counter = total_image_counter
        self.groups_dropdown = groups_dropdown
        self.group_name_text = group_name_text
        self.save_group_button = save_group_button
        self.load_group_button = load_group_button
        self.delete_group_button = delete_group_button
        self.rename_group_button = rename_group_button
        self.duplicate_group_button = duplicate_group_button
        self.save_groups_cfg_button = save_groups_cfg_button
        self.load_groups_cfg_button = load_groups_cfg_button

        return [
                self.refresh_aspect_btn,
                self.download_folder_type,
                self.img_id_textbox,
                self.tag_search_textbox,
                self.tag_search_suggestion_dropdown,
                self.apply_to_all_type_select_checkboxgroup,
                self.select_multiple_images_checkbox,
                self.select_between_images_checkbox,
                self.select_all_checkbox,
                self.deselect_all_checkbox,
                self.invert_selection_checkbox,
                self.apply_datetime_sort_ckbx,
                self.apply_datetime_choice_menu,
                self.image_remove_button,
                self.image_save_ids_button,
                self.send_img_from_gallery_dropdown,
                self.batch_send_from_gallery_checkbox,
                self.send_img_from_gallery_button,
                self.compare_button,
                self.compare_image_left,
                self.comp_left_artist,
                self.comp_left_character,
                self.comp_left_species,
                self.comp_left_invalid,
                self.comp_left_general,
                self.comp_left_meta,
                self.comp_left_rating,
                self.compare_image_right,
                self.comp_right_artist,
                self.comp_right_character,
                self.comp_right_species,
                self.comp_right_invalid,
                self.comp_right_general,
                self.comp_right_meta,
                self.comp_right_rating,
                self.transfer_tags_button,
                self.remove_tags_button,
                self.remove_tags_both_l_button,
                transfer_tags_button_rl,
                remove_tags_button_rl,
                self.remove_tags_both_r_button,
                comp_left_add_text,
                comp_right_add_text,
                comp_add_to_both_checkbox,
                apply_transfer_button,
                apply_remove_button,
                self.tag_remove_button,
                self.tag_save_button,
                self.tag_add_textbox,
                self.tag_add_suggestion_dropdown,
                self.category_filter_gallery_dropdown,
                self.tag_effects_gallery_dropdown,
                self.img_artist_tag_checkbox_group,
                self.img_character_tag_checkbox_group,
                self.img_species_tag_checkbox_group,
                self.img_invalid_tag_checkbox_group,
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
                self.prepend_now_button,
                self.total_image_counter,
                self.gallery_state,
                self.groups_dropdown,
                self.group_name_text,
                self.save_group_button,
                self.load_group_button,
                self.delete_group_button,
                self.rename_group_button,
                self.duplicate_group_button,
                self.save_groups_cfg_button,
                self.load_groups_cfg_button
                ]

    def get_event_listeners(self):
        self.year_remove_button.click(
            fn=self.remove_all,
            inputs=[
                self.img_artist_tag_checkbox_group,
                self.img_character_tag_checkbox_group,
                self.img_species_tag_checkbox_group,
                self.img_invalid_tag_checkbox_group,
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
                self.img_invalid_tag_checkbox_group,
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
                   self.img_invalid_tag_checkbox_group, self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group, self.img_rating_tag_checkbox_group],
            outputs=[self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group, self.img_species_tag_checkbox_group,
                   self.img_invalid_tag_checkbox_group, self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group, self.img_rating_tag_checkbox_group]
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
            outputs=[self.gallery_comp, self.total_image_counter, self.gallery_state]).then(
            fn=self.reset_selected_img,
            inputs=[self.img_id_textbox],
            outputs=[self.img_id_textbox, self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group,
                     self.img_species_tag_checkbox_group, self.img_invalid_tag_checkbox_group, self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group,
                     self.img_rating_tag_checkbox_group]
        )
        self.tag_add_textbox.submit(
             fn=self.add_tag_changes,
             inputs=[self.tag_add_textbox, self.apply_to_all_type_select_checkboxgroup, self.img_id_textbox, self.multi_select_ckbx_state,
                     self.only_selected_state_object, self.images_selected_state, self.initial_add_state, gr.State(True)],
             outputs=[self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group, self.img_species_tag_checkbox_group,
                      self.img_invalid_tag_checkbox_group, self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group, self.img_rating_tag_checkbox_group,
                      self.initial_add_state_tag, self.tag_add_textbox]
        )
        self.tag_add_suggestion_dropdown.select(
             fn=self.tag_ideas.dropdown_handler_add_tags,
             inputs=[self.apply_to_all_type_select_checkboxgroup, self.img_id_textbox, self.multi_select_ckbx_state,
                     self.only_selected_state_object, self.images_selected_state, self.initial_add_state],
             outputs=[self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group, self.img_species_tag_checkbox_group,
                      self.img_invalid_tag_checkbox_group, self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group, self.img_rating_tag_checkbox_group,
                      self.tag_add_textbox, self.tag_add_suggestion_dropdown, self.initial_add_state, self.initial_add_state_tag]
        )
        self.image_remove_button.click(
            fn=self.remove_images,
            inputs=[self.apply_to_all_type_select_checkboxgroup, self.img_id_textbox, self.apply_datetime_sort_ckbx,
                    self.apply_datetime_choice_menu, self.multi_select_ckbx_state, self.only_selected_state_object,
                    self.images_selected_state],
            outputs=[self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group, self.img_species_tag_checkbox_group,
                     self.img_invalid_tag_checkbox_group, self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group, self.img_rating_tag_checkbox_group,
                     self.gallery_comp, self.img_id_textbox, self.only_selected_state_object, self.images_selected_state]).then(
            fn=self.reset_gallery_component_only,
            inputs=[],
            outputs=[self.gallery_comp, self.total_image_counter]).then(
            fn=self.show_searched_gallery,
            inputs=[self.download_folder_type, self.apply_datetime_sort_ckbx, self.apply_datetime_choice_menu],
            outputs=[self.gallery_comp, self.total_image_counter, self.gallery_state]
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
                self.img_invalid_tag_checkbox_group,
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
                self.img_invalid_tag_checkbox_group,
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
            outputs=[self.gallery_comp, self.total_image_counter]).then(
            fn=self.show_searched_gallery,
            inputs=[self.download_folder_type, self.apply_datetime_sort_ckbx, self.apply_datetime_choice_menu],
            outputs=[self.gallery_comp, self.total_image_counter, self.gallery_state]).then(
            fn=self.clear_categories,
            inputs=[],
            outputs=[self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group, self.img_species_tag_checkbox_group,
                     self.img_invalid_tag_checkbox_group, self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group, self.img_rating_tag_checkbox_group,
                     self.img_id_textbox]
        )
        self.select_multiple_images_checkbox.change(
            fn=self.set_ckbx_state,
            inputs=[self.select_multiple_images_checkbox, self.multi_select_ckbx_state],
            outputs=[
                self.multi_select_ckbx_state,
                self.select_between_images_checkbox,
                self.select_all_checkbox,
                self.deselect_all_checkbox,
                self.invert_selection_checkbox,
            ]
        ).then(
            None,
            inputs=[self.images_selected_state, self.multi_select_ckbx_state],
            outputs=None,
            js=js_.js_do_everything
        )
        self.select_all_checkbox.change(
            fn=self.handle_select_all,
            inputs=[self.gallery_state, self.images_selected_state, self.select_all_checkbox],
            outputs=[self.images_selected_state, self.only_selected_state_object, self.select_all_checkbox]
        ).then(
            None,
            inputs=[self.images_selected_state, self.multi_select_ckbx_state],
            outputs=None,
            js=js_.js_do_everything
        )
        self.deselect_all_checkbox.change(
            fn=self.handle_deselect_all,
            inputs=[self.gallery_state, self.images_selected_state, self.deselect_all_checkbox],
            outputs=[self.images_selected_state, self.only_selected_state_object, self.deselect_all_checkbox]
        ).then(
            None,
            inputs=[self.images_selected_state, self.multi_select_ckbx_state],
            outputs=None,
            js=js_.js_do_everything
        )
        self.invert_selection_checkbox.change(
            fn=self.handle_invert_selection,
            inputs=[self.gallery_state, self.images_selected_state, self.invert_selection_checkbox],
            outputs=[self.images_selected_state, self.only_selected_state_object, self.invert_selection_checkbox]
        ).then(
            None,
            inputs=[self.images_selected_state, self.multi_select_ckbx_state],
            outputs=None,
            js=js_.js_do_everything
        )
        self.compare_button.click(
            fn=self.compare_selected,
            inputs=[self.gallery_state, self.images_selected_state],
            outputs=[
                self.compare_image_left,
                self.comp_left_artist,
                self.comp_left_character,
                self.comp_left_species,
                self.comp_left_invalid,
                self.comp_left_general,
                self.comp_left_meta,
                self.comp_left_rating,
                self.compare_image_right,
                self.comp_right_artist,
                self.comp_right_character,
                self.comp_right_species,
                self.comp_right_invalid,
                self.comp_right_general,
                self.comp_right_meta,
                self.comp_right_rating,
            ]
        )
        self.transfer_tags_button.click(
            fn=self.transfer_left_to_right,
            inputs=[
                self.comp_left_artist,
                self.comp_left_character,
                self.comp_left_species,
                self.comp_left_invalid,
                self.comp_left_general,
                self.comp_left_meta,
                self.comp_left_rating,
            ],
            outputs=[
                self.comp_right_artist,
                self.comp_right_character,
                self.comp_right_species,
                self.comp_right_invalid,
                self.comp_right_general,
                self.comp_right_meta,
                self.comp_right_rating,
            ]
        )
        self.remove_tags_button.click(
            fn=self.remove_left_from_right,
            inputs=[
                self.comp_left_artist,
                self.comp_left_character,
                self.comp_left_species,
                self.comp_left_invalid,
                self.comp_left_general,
                self.comp_left_meta,
                self.comp_left_rating,
            ],
            outputs=[
                self.comp_right_artist,
                self.comp_right_character,
                self.comp_right_species,
                self.comp_right_invalid,
                self.comp_right_general,
                self.comp_right_meta,
                self.comp_right_rating,
            ]
        )
        self.transfer_tags_button_rl.click(
            fn=self.transfer_right_to_left,
            inputs=[
                self.comp_right_artist,
                self.comp_right_character,
                self.comp_right_species,
                self.comp_right_invalid,
                self.comp_right_general,
                self.comp_right_meta,
                self.comp_right_rating,
            ],
            outputs=[
                self.comp_left_artist,
                self.comp_left_character,
                self.comp_left_species,
                self.comp_left_invalid,
                self.comp_left_general,
                self.comp_left_meta,
                self.comp_left_rating,
            ]
        )
        self.remove_tags_button_rl.click(
            fn=self.remove_right_from_left,
            inputs=[
                self.comp_right_artist,
                self.comp_right_character,
                self.comp_right_species,
                self.comp_right_invalid,
                self.comp_right_general,
                self.comp_right_meta,
                self.comp_right_rating,
            ],
            outputs=[
                self.comp_left_artist,
                self.comp_left_character,
                self.comp_left_species,
                self.comp_left_invalid,
                self.comp_left_general,
                self.comp_left_meta,
                self.comp_left_rating,
            ]
        )
        self.remove_tags_both_l_button.click(
            fn=self.remove_left_from_both,
            inputs=[
                self.comp_left_artist,
                self.comp_left_character,
                self.comp_left_species,
                self.comp_left_invalid,
                self.comp_left_general,
                self.comp_left_meta,
                self.comp_left_rating,
            ],
            outputs=[
                self.comp_left_artist,
                self.comp_left_character,
                self.comp_left_species,
                self.comp_left_invalid,
                self.comp_left_general,
                self.comp_left_meta,
                self.comp_left_rating,
                self.comp_right_artist,
                self.comp_right_character,
                self.comp_right_species,
                self.comp_right_invalid,
                self.comp_right_general,
                self.comp_right_meta,
                self.comp_right_rating,
            ]
        )
        self.remove_tags_both_r_button.click(
            fn=self.remove_right_from_both,
            inputs=[
                self.comp_right_artist,
                self.comp_right_character,
                self.comp_right_species,
                self.comp_right_invalid,
                self.comp_right_general,
                self.comp_right_meta,
                self.comp_right_rating,
            ],
            outputs=[
                self.comp_left_artist,
                self.comp_left_character,
                self.comp_left_species,
                self.comp_left_invalid,
                self.comp_left_general,
                self.comp_left_meta,
                self.comp_left_rating,
                self.comp_right_artist,
                self.comp_right_character,
                self.comp_right_species,
                self.comp_right_invalid,
                self.comp_right_general,
                self.comp_right_meta,
                self.comp_right_rating,
            ]
        )
        self.comp_left_add_text.submit(
            fn=self.add_tag_left,
            inputs=[self.comp_left_add_text, self.comp_add_to_both_checkbox],
            outputs=[
                self.comp_left_artist,
                self.comp_left_character,
                self.comp_left_species,
                self.comp_left_invalid,
                self.comp_left_general,
                self.comp_left_meta,
                self.comp_left_rating,
                self.comp_right_artist,
                self.comp_right_character,
                self.comp_right_species,
                self.comp_right_invalid,
                self.comp_right_general,
                self.comp_right_meta,
                self.comp_right_rating,
            ]
        )
        self.comp_right_add_text.submit(
            fn=self.add_tag_right,
            inputs=[self.comp_right_add_text, self.comp_add_to_both_checkbox],
            outputs=[
                self.comp_left_artist,
                self.comp_left_character,
                self.comp_left_species,
                self.comp_left_invalid,
                self.comp_left_general,
                self.comp_left_meta,
                self.comp_left_rating,
                self.comp_right_artist,
                self.comp_right_character,
                self.comp_right_species,
                self.comp_right_invalid,
                self.comp_right_general,
                self.comp_right_meta,
                self.comp_right_rating,
            ]
        )
        self.apply_transfer_button.click(
            fn=self.apply_transfer_to_selected,
            inputs=[self.gallery_state, self.images_selected_state],
            outputs=[]
        )
        self.apply_remove_button.click(
            fn=self.apply_remove_to_selected,
            inputs=[self.gallery_state, self.images_selected_state],
            outputs=[]
        )
        self.download_folder_type.change(
            fn=self.show_searched_gallery,
            inputs=[self.download_folder_type, self.apply_datetime_sort_ckbx, self.apply_datetime_choice_menu],
            outputs=[self.gallery_comp, self.total_image_counter, self.gallery_state]).then(
            fn=self.reset_selected_img,
            inputs=[self.img_id_textbox],
            outputs=[self.img_id_textbox, self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group,
                     self.img_species_tag_checkbox_group, self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group,
                     self.img_rating_tag_checkbox_group]
        )
        # there is a networking "delay" bug for the below feature to work (do NOT click on the same image after selected) i.e. click on a different image before going back to that one
        self.gallery_comp.select(
            fn=self.get_img_tags,
            inputs=[self.gallery_state, self.select_multiple_images_checkbox, self.images_selected_state,
                    self.select_between_images_checkbox, self.images_tuple_points],
            outputs=[self.img_id_textbox, self.img_artist_tag_checkbox_group, self.img_character_tag_checkbox_group,
                     self.img_species_tag_checkbox_group, self.img_invalid_tag_checkbox_group, self.img_general_tag_checkbox_group, self.img_meta_tag_checkbox_group,
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
            outputs=[self.gallery_comp, self.total_image_counter, self.gallery_state]
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
        self.save_group_button.click(
            fn=self.save_group,
            inputs=[self.group_name_text, self.groups_state, self.gallery_state, self.images_selected_state],
            outputs=[self.groups_state, self.groups_dropdown, self.group_name_text]
        )
        self.delete_group_button.click(
            fn=self.delete_group,
            inputs=[self.groups_state, self.groups_dropdown],
            outputs=[self.groups_state, self.groups_dropdown]
        )
        self.load_group_button.click(
            fn=self.load_group,
            inputs=[self.gallery_state, self.groups_state, self.groups_dropdown],
            outputs=[self.images_selected_state, self.only_selected_state_object]
        ).then(
            None,
            inputs=[self.images_selected_state, self.multi_select_ckbx_state],
            outputs=None,
            js=js_.js_do_everything
        )
        self.rename_group_button.click(
            fn=self.rename_group,
            inputs=[self.groups_state, self.groups_dropdown, self.group_name_text],
            outputs=[self.groups_state, self.groups_dropdown, self.group_name_text]
        )
        self.duplicate_group_button.click(
            fn=self.duplicate_group,
            inputs=[self.groups_state, self.groups_dropdown, self.group_name_text],
            outputs=[self.groups_state, self.groups_dropdown, self.group_name_text]
        )
        self.save_groups_cfg_button.click(
            fn=self.save_groups_config,
            inputs=[self.groups_state],
            outputs=[]
        )
        self.load_groups_cfg_button.click(
            fn=self.load_groups_config,
            inputs=[],
            outputs=[self.groups_state, self.groups_dropdown]
        )
 

    def save_group(self, name, groups_state, gallery_images, indices):
        paths = []
        for idx in indices:
            if 0 <= idx < len(gallery_images):
                path = gallery_images[idx][0] if isinstance(gallery_images[idx], (list, tuple)) else gallery_images[idx]
                paths.append(path)
        groups = group_manager.save_group(groups_state or {}, name, paths)
        self.groups_state.value = groups
        return groups, gr.update(choices=list(groups.keys())), gr.update(value="")

    def delete_group(self, groups_state, group_names):
        groups = group_manager.delete_groups(groups_state or {}, group_names)
        self.groups_state.value = groups
        return groups, gr.update(choices=list(groups.keys()))

    def rename_group(self, groups_state, group_names, new_name):
        if not group_names:
            return groups_state, gr.update(choices=list((groups_state or {}).keys())), gr.update()
        groups = group_manager.rename_group(groups_state or {}, group_names[0], new_name)
        self.groups_state.value = groups
        return groups, gr.update(choices=list(groups.keys()), value=new_name if new_name in groups else None), gr.update(value="")

    def duplicate_group(self, groups_state, group_names, new_name):
        if not group_names:
            return groups_state, gr.update(choices=list((groups_state or {}).keys())), gr.update()
        groups = group_manager.duplicate_group(groups_state or {}, group_names[0], new_name)
        self.groups_state.value = groups
        return groups, gr.update(choices=list(groups.keys()), value=new_name if new_name in groups else None), gr.update(value="")

    def load_group(self, gallery_images, groups_state, group_names):
        targets = set(group_manager.load_groups(groups_state or {}, group_names))
        indices = []
        mapping = {}
        for idx, img in enumerate(gallery_images):
            path = img[0] if isinstance(img, (list, tuple)) else img
            if path in targets:
                ext, img_id = self.extract_name_and_extention(path)
                indices.append(idx)
                mapping[idx] = [ext, img_id]
        self._update_search_from_mapping(mapping)
        self.images_selected_state.value = indices
        self.only_selected_state_object.value = mapping
        self._debug_selection(indices, mapping)
        return indices, mapping

    def save_groups_config(self, groups_state):
        group_manager.save_groups_file(groups_state or {}, self.groups_config_path)

    def load_groups_config(self):
        groups = group_manager.load_groups_file(self.groups_config_path)
        self.groups_state.value = groups
        return groups, gr.update(choices=list(groups.keys()))
