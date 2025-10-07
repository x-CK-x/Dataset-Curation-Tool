import copy
import glob
import os
import shutil
import time
from datetime import datetime
import multiprocessing as mp
import pandas as pd
import gradio as gr
import json
from typing import Dict, List, Optional

from utils import js_constants as js_, md_constants as md_, helper_functions as help
from utils import preset_config
from utils.features.downloader import batch_downloader


class Download_tab:
    def __init__(self, settings_json, cwd, image_board, img_extensions, method_tag_files_opts, collect_checkboxes,
                 download_checkboxes, resize_checkboxes, file_extn_list, config_name, required_tags_list,
                 blacklist_tags, auto_config_path, initial_required_state,
                 initial_required_state_tag, relevant_required_categories, initial_blacklist_state,
                 initial_blacklist_state_tag, relevant_blacklist_categories, auto_complete_config,
                 db_manager=None):
        self.settings_json = settings_json
        self.cwd = cwd
        self.image_board = image_board
        self.img_extensions = img_extensions
        self.method_tag_files_opts = method_tag_files_opts
        self.collect_checkboxes = collect_checkboxes
        self.download_checkboxes = download_checkboxes
        self.resize_checkboxes = resize_checkboxes
        self.file_extn_list = file_extn_list
        self.config_name = config_name
        self.required_tags_list = required_tags_list
        self.blacklist_tags = blacklist_tags
        self.auto_config_path = auto_config_path
        self.initial_required_state = initial_required_state
        self.initial_required_state_tag = initial_required_state_tag
        self.relevant_required_categories = relevant_required_categories
        self.initial_blacklist_state = initial_blacklist_state
        self.initial_blacklist_state_tag = initial_blacklist_state_tag
        self.relevant_blacklist_categories = relevant_blacklist_categories
        self.auto_complete_config = auto_complete_config

        self.db_manager = db_manager
        self.current_download_id = None

        self.advanced_settings_tab_manager = None

        self.gallery_tab_manager = None
        self.tag_ideas = None
        self.is_csv_loaded = False

        self.default_preset_folder = os.path.abspath(os.getcwd())
        stored_settings = preset_config.load_settings()
        legacy_setting = self.settings_json.get("preset_folder")
        stored_folder = stored_settings.get("preset_folder")

        resolved_folder = None
        legacy_resolved = None
        if stored_folder:
            try:
                resolved_folder = self._resolve_folder_path(stored_folder)
            except Exception:
                resolved_folder = None

        if legacy_setting:
            try:
                legacy_resolved = self._resolve_folder_path(legacy_setting)
            except Exception:
                legacy_resolved = None

        if resolved_folder is None and legacy_resolved:
            resolved_folder = legacy_resolved

        if resolved_folder is None:
            resolved_folder = self.default_preset_folder

        self.preset_folder = resolved_folder
        self.settings_json["preset_folder"] = self.preset_folder
        if legacy_setting is None or ((legacy_resolved or legacy_setting) and legacy_resolved != self.preset_folder):
            self._persist_settings()
        if not stored_folder or os.path.abspath(stored_folder) != os.path.abspath(self.preset_folder):
            preset_config.set_preset_folder(self.preset_folder)

        self.batch_to_json_map = {}
        self.preset_download_status: Dict[str, Dict[str, object]] = {}

    def set_tag_ideas(self, tag_ideas):
        self.tag_ideas = tag_ideas

    def _persist_settings(self, persist_to_db=True):
        """Write settings JSON to disk and snapshot to the database."""
        help.update_JSON(self.settings_json, self.config_name)
        if not persist_to_db or not self.db_manager:
            return
        config_path = self.config_name
        if not os.path.isabs(config_path):
            config_path = os.path.abspath(config_path)
        try:
            self.db_manager.add_config(self.settings_json, config_path)
        except Exception as err:
            help.verbose_print(f"Failed to persist settings to database: {err}")

    def set_advanced_settings_tab_manager(self, advanced_settings_tab_manager):
        self.advanced_settings_tab_manager = advanced_settings_tab_manager

    def set_gallery_tab_manager(self, gallery_tab_manager):
        self.gallery_tab_manager = gallery_tab_manager

    def config_save_button(self, batch_folder, resized_img_folder, tag_sep, tag_order_format, prepend_tags, append_tags,
                           img_ext,
                           method_tag_files, min_score, min_fav_count, min_area, top_n, min_short_side,
                           skip_posts_file, skip_posts_type,
                           collect_from_listed_posts_file, collect_from_listed_posts_type, apply_filter_to_listed_posts,
                           save_searched_list_type, save_searched_list_path, downloaded_posts_folder, png_folder,
                           jpg_folder,
                           webm_folder, gif_folder, swf_folder, save_filename_type, remove_tags_list, replace_tags_list,
                           tag_count_list_folder, min_month, min_day, min_year, collect_checkbox_group_var,
                           download_checkbox_group_var,
                           resize_checkbox_group_var, create_new_config_checkbox, settings_path, proxy_url_textbox,
                           custom_csv_path_textbox, use_csv_custom_checkbox, override_download_delay_checkbox,
                           custom_download_delay_slider, custom_retry_attempts_slider):

        self.settings_json["batch_folder"] = str(batch_folder)
        self.settings_json["resized_img_folder"] = str(resized_img_folder)
        self.settings_json["tag_sep"] = str(tag_sep)


        self.settings_json["tag_order_format"] = (self.settings_json["tag_sep"]).join(tag_order_format)
        self.image_board.set_tag_order(tag_order_format)
        self.image_board.update_img_brd()


        self.settings_json["prepend_tags"] = (self.settings_json["tag_sep"]).join(prepend_tags)
        self.settings_json["append_tags"] = (self.settings_json["tag_sep"]).join(append_tags)
        self.settings_json["img_ext"] = str(img_ext)
        self.settings_json["method_tag_files"] = str(method_tag_files)
        self.settings_json["min_score"] = int(min_score)
        self.settings_json["min_fav_count"] = int(min_fav_count)

        self.settings_json["min_year"] = int(min_year)
        self.settings_json["min_month"] = int(min_month)
        self.settings_json["min_day"] = int(min_day)

        self.settings_json["min_date"] = f"{int(min_year)}-{help.to_padded(int(min_month))}-{help.to_padded(int(min_day))}"

        self.settings_json["min_area"] = int(min_area)
        self.settings_json["top_n"] = int(top_n)
        self.settings_json["min_short_side"] = int(min_short_side)

        self.settings_json["proxy_url"] = str(proxy_url_textbox)

        self.settings_json["use_csv_custom"] = bool(use_csv_custom_checkbox)
        self.settings_json["csv_custom_path"] = str(custom_csv_path_textbox)

        self.settings_json["override_download_delay"] = bool(override_download_delay_checkbox)
        self.settings_json["custom_download_delay"] = int(custom_download_delay_slider)
        self.settings_json["custom_retry_attempts"] = int(custom_retry_attempts_slider)

        # COLLECT CheckBox Group
        for key in self.collect_checkboxes:
            if key in collect_checkbox_group_var:
                self.settings_json[key] = True
            else:
                self.settings_json[key] = False
        # DOWNLOAD CheckBox Group
        for key in self.download_checkboxes:
            if key in download_checkbox_group_var:
                self.settings_json[key] = True
            else:
                self.settings_json[key] = False
        # RESIZE CheckBox Group
        for key in self.resize_checkboxes:
            if key in resize_checkbox_group_var:
                self.settings_json[key] = True
            else:
                self.settings_json[key] = False

        self.settings_json["required_tags"] = help.get_string(self.required_tags_list, str(tag_sep))
        self.settings_json["blacklist"] = help.get_string(self.blacklist_tags, " | ")

        self.settings_json["skip_posts_file"] = str(skip_posts_file)
        self.settings_json["skip_posts_type"] = str(skip_posts_type)
        self.settings_json["collect_from_listed_posts_file"] = str(collect_from_listed_posts_file)
        self.settings_json["collect_from_listed_posts_type"] = str(collect_from_listed_posts_type)
        self.settings_json["apply_filter_to_listed_posts"] = bool(apply_filter_to_listed_posts)
        self.settings_json["save_searched_list_type"] = str(save_searched_list_type)
        self.settings_json["save_searched_list_path"] = str(save_searched_list_path)
        self.settings_json["downloaded_posts_folder"] = str(downloaded_posts_folder)
        self.settings_json["png_folder"] = str(png_folder)
        self.settings_json["jpg_folder"] = str(jpg_folder)
        self.settings_json["webm_folder"] = str(webm_folder)
        self.settings_json["gif_folder"] = str(gif_folder)
        self.settings_json["swf_folder"] = str(swf_folder)
        self.settings_json["save_filename_type"] = str(save_filename_type)
        self.settings_json["remove_tags_list"] = str(remove_tags_list)
        self.settings_json["replace_tags_list"] = str(replace_tags_list)
        self.settings_json["tag_count_list_folder"] = str(tag_count_list_folder)

        if create_new_config_checkbox:  # if called from the "create new button" the True flag will always be passed to ensure this
            temp = '\\' if help.is_windows() else '/'
            config_dir = os.path.join(self.settings_json["batch_folder"], "configs")
            if temp in settings_path:
                self.config_name = settings_path
            else:
                self.config_name = os.path.join(config_dir, settings_path)

        if not self.config_name or len(self.config_name) == 0:
            raise ValueError('No Config Name Specified')

        # Update json
        help.update_JSON(self.settings_json, self.config_name)

        # get file names & create dictionary mappings to batch file names
        batch_names, _ = self._load_preset_files()

        all_json_files_checkboxgroup = gr.update(choices=batch_names, value=[])
        quick_json_select = gr.update(choices=batch_names, value=batch_names[0] if batch_names else None)

        return all_json_files_checkboxgroup, quick_json_select

    def check_box_group_handler_required(self, check_box_group):
        for tag in check_box_group:
            self.required_tags_list.remove(tag)
        return gr.update(choices=self.required_tags_list, label='ALL Required Tags', value=[])

    def check_box_group_handler_blacklist(self, check_box_group):
        for tag in check_box_group:
            self.blacklist_tags.remove(tag)
        return gr.update(choices=self.blacklist_tags, label='ALL Blacklisted Tags', value=[])

    ### file expects a format of 1 tag per line, with the tag being before the first comma
    def parse_file_required(self, file_list):
        for single_file in file_list:
            with open(single_file.name, 'r', encoding='utf-8') as read_file:
                while True:
                    line = read_file.readline()
                    if not line:
                        break

                    length = len(line.replace(" ", "").split(","))

                    if length > 3:  # assume everything on one line
                        tags = line.replace(" ", "").split(",")
                        for tag in tags:
                            if not tag in self.required_tags_list:
                                self.required_tags_list.append(tag)
                    else:  # assume cascaded tags
                        tag = line.replace(" ", "").split(",")[0]
                        if not tag in self.required_tags_list:
                            self.required_tags_list.append(tag)
                read_file.close()
        return gr.update(choices=self.required_tags_list, label='ALL Required Tags', value=[])

    ### file expects a format of 1 tag per line, with the tag being before the first comma
    def parse_file_blacklist(self, file_list):
        for single_file in file_list:
            with open(single_file.name, 'r', encoding='utf-8') as read_file:
                while True:
                    line = read_file.readline()
                    if not line:
                        break

                    length = len(line.replace(" ", "").split(","))

                    if length > 3:  # assume everything on one line
                        tags = line.replace(" ", "").split(",")
                        for tag in tags:
                            if not tag in self.blacklist_tags:
                                self.blacklist_tags.append(tag)
                    else:  # assume cascaded tags
                        tag = line.replace(" ", "").split(",")[0]
                        if not tag in self.blacklist_tags:
                            self.blacklist_tags.append(tag)
                read_file.close()
        return gr.update(choices=self.blacklist_tags, label='ALL Blacklisted Tags', value=[])

    def make_run_visible(self):
        return gr.update(interactive=False, visible=True)

    def make_invisible(self):
        return gr.update(interactive=False, visible=False)

    def run_script(self, basefolder='', settings_path=os.getcwd(), numcpu=-1, phaseperbatch=False, keepdb=False,
                   cachepostsdb=False, postscsv='', tagscsv='', postsparquet='', tagsparquet=''):
        help.verbose_print(
            f"RUN COMMAND IS:\t{basefolder, settings_path, numcpu, phaseperbatch, postscsv, tagscsv, postsparquet, tagsparquet, keepdb, cachepostsdb}")

        if self.db_manager is not None:
            import json
            cfg_json = json.dumps(self.settings_json)
            preset_name = None
            if self.config_name:
                preset_name = os.path.splitext(os.path.basename(self.config_name))[0]
            self.current_download_id = self.db_manager.add_download_record(
                website="e621",
                config_json=cfg_json,
                config_path=self.config_name,
                preset_name=preset_name,
            )
            if self.gallery_tab_manager:
                self.gallery_tab_manager.set_download_id(self.current_download_id)

        #### ADD A PIPE parameter that passes the connection to the other process
        self.frontend_conn, self.backend_conn = mp.Pipe()
        self.image_board_downloader = mp.Process(target=batch_downloader.E6_Downloader, args=(
        basefolder, settings_path, numcpu, phaseperbatch, postscsv, tagscsv, postsparquet, tagsparquet, keepdb,
        cachepostsdb, self.backend_conn, self.db_manager.db_path if self.db_manager else None, self.current_download_id), )
        self.image_board_downloader.start()

    def run_script_batch(self, basefolder='', settings_path=os.getcwd(), numcpu=-1, phaseperbatch=False, keepdb=False,
                         cachepostsdb=False, postscsv='', tagscsv='', postsparquet='', tagsparquet='',
                         run_button_batch=None, images_full_change_dict_textbox=None, progress=gr.Progress(track_tqdm=True)):
        help.verbose_print(
            f"RUN COMMAND IS:\t{basefolder, settings_path, numcpu, phaseperbatch, postscsv, tagscsv, postsparquet, tagsparquet, keepdb, cachepostsdb}")

        total = len(run_button_batch)
        start = time.time()
        progress(0, desc="Starting...")
        for idx, setting in enumerate(run_button_batch, start=1):
            eta = (time.time() - start) / idx * (total - idx) if idx > 0 else 0
            progress(idx / total, desc=f"Batch {idx}/{total} - ETA {int(eta)}s")
            yield gr.update(value=f"{idx}/{total} (ETA {int(eta)}s)")
            setting = self.batch_to_json_map[setting]
            path = self._resolve_file_path(setting)
            if not ".json" in path:
                path += ".json"

            if self.db_manager is not None:
                cfg = help.load_session_config(path)
                preset_name = os.path.splitext(os.path.basename(path))[0]
                dl_id = self.db_manager.add_download_record(
                    website="e621",
                    config_json=json.dumps(cfg),
                    config_path=path,
                    preset_name=preset_name,
                )
                if self.gallery_tab_manager:
                    self.gallery_tab_manager.set_download_id(dl_id)

            self.image_board_downloader = batch_downloader.E6_Downloader(basefolder, path, numcpu, phaseperbatch, postscsv, tagscsv,
                                                                         postsparquet, tagsparquet, keepdb, cachepostsdb, None,
                                                                         self.db_manager.db_path if self.db_manager else None, dl_id)
            #
            # settings_json = help.load_session_config(path)
            # # apply post-processing
            # auto_config_apply(images_full_change_dict_textbox)
            del self.image_board_downloader
        yield gr.update(interactive=False, visible=False)

    def data_collect(self, progress=gr.Progress(track_tqdm=True)):
        total = int(self.frontend_conn.recv())
        start = time.time()
        progress(0, desc="Starting...")
        for i in range(total):
            _ = self.frontend_conn.recv()
            elapsed = time.time() - start
            eta = (elapsed / (i + 1)) * (total - i - 1) if i > 0 else 0
            progress((i + 1) / total, desc=f"Collecting {i+1}/{total} - ETA {int(eta)}s")
            yield gr.update(value=f"{i+1}/{total} (ETA {int(eta)}s)")
        yield gr.update(interactive=False, visible=False)

    def data_download(self, progress=gr.Progress(track_tqdm=True)):
        total = int(self.frontend_conn.recv())
        start = time.time()
        progress(0, desc="Starting...")
        for i in range(total):
            _ = int(self.frontend_conn.recv())
            elapsed = time.time() - start
            eta = (elapsed / (i + 1)) * (total - i - 1) if i > 0 else 0
            progress((i + 1) / total, desc=f"Downloading {i+1}/{total} - ETA {int(eta)}s")
            yield gr.update(value=f"{i+1}/{total} (ETA {int(eta)}s)")
        yield gr.update(interactive=False, visible=False)

    def data_resize(self, resize_checkbox_group, progress=gr.Progress(track_tqdm=True)):
        if not "skip_resize" in resize_checkbox_group:
            total = int(self.frontend_conn.recv())
            start = time.time()
            progress(0, desc="Starting...")
            for i in range(total):
                _ = self.frontend_conn.recv()
                elapsed = time.time() - start
                eta = (elapsed / (i + 1)) * (total - i - 1) if i > 0 else 0
                progress((i + 1) / total, desc=f"Resizing {i+1}/{total} - ETA {int(eta)}s")
                yield gr.update(value=f"{i+1}/{total} (ETA {int(eta)}s)")

        self.frontend_conn.close()
        del self.frontend_conn, self.backend_conn
        yield gr.update(interactive=False, visible=False)

    def end_connection(self):
        if hasattr(self, "image_board_downloader"):
            self.image_board_downloader.join(timeout=5)
            if self.image_board_downloader.is_alive():
                self.image_board_downloader.terminate()
                self.image_board_downloader.join()
            del self.image_board_downloader

    def check_to_reload_auto_complete_config(self, optional_path=None):
        temp_config_path = ""
        if not optional_path or optional_path == "":
            if not self.settings_json["batch_folder"] in self.gallery_tab_manager.auto_complete_config_name:
                self.auto_config_path = os.path.join(self.settings_json["batch_folder"], "configs")
                sanitized = self.settings_json['batch_folder'].replace('/', '---').replace('\\', '---')
                self.gallery_tab_manager.auto_complete_config_name = f"auto_complete_{sanitized}.json"

                temp_config_path = os.path.join(self.auto_config_path, self.gallery_tab_manager.auto_complete_config_name)
                if not os.path.exists(self.auto_config_path):
                    os.makedirs(self.auto_config_path)
                # load if data present / create if file not yet created
                self.auto_complete_config = help.load_session_config(temp_config_path)
        else:
            if not self.settings_json["batch_folder"] in optional_path:
                help.eprint("CURRENT LOADED BATCH FOLDER NOT PRESENT IN SPECIFIED PATH!!!")
                self.auto_config_path = os.path.join(self.settings_json["batch_folder"], "configs")
                temp = '\\' if help.is_windows() else '/'
                name = optional_path.split(temp)[-1]
                name = name.replace('/', '---').replace('\\', '---')
                self.gallery_tab_manager.auto_complete_config_name = name

                temp_config_path = os.path.join(self.auto_config_path, self.gallery_tab_manager.auto_complete_config_name)
                if not os.path.exists(self.auto_config_path):
                    os.makedirs(self.auto_config_path)
                # load if data present / create if file not yet created
                self.auto_complete_config = help.load_session_config(temp_config_path)

        # if empty add default entries
        if not self.auto_complete_config:
            self.auto_complete_config = {'png': {}, 'jpg': {}, 'gif': {}}
            help.update_JSON(self.auto_complete_config, temp_config_path)

    def _resolve_folder_path(self, folder_path):
        if not folder_path:
            return self.default_preset_folder
        folder_path = os.path.expanduser(str(folder_path))
        if not os.path.isabs(folder_path):
            folder_path = os.path.abspath(os.path.join(self.default_preset_folder, folder_path))
        return folder_path

    def _resolve_file_path(self, path):
        if not path:
            return ""
        candidate = os.path.expanduser(str(path))
        if os.path.isabs(candidate):
            return os.path.abspath(candidate)
        active_folder = self.get_active_preset_directory()
        preset_candidate = os.path.abspath(os.path.join(active_folder, candidate))
        if os.path.exists(preset_candidate):
            return preset_candidate
        return os.path.abspath(os.path.join(self.default_preset_folder, candidate))

    def _resolve_download_directory(self, folder_path, preset_path):
        if not folder_path:
            return ""
        folder_path = os.path.expanduser(str(folder_path))
        if os.path.isabs(folder_path):
            return os.path.abspath(folder_path)
        preset_dir = os.path.dirname(os.path.abspath(preset_path))
        candidate = os.path.abspath(os.path.join(preset_dir, folder_path))
        if os.path.isdir(candidate):
            return candidate
        return os.path.abspath(os.path.join(self.default_preset_folder, folder_path))

    def get_active_preset_directory(self):
        folder = self._resolve_folder_path(self.preset_folder)
        os.makedirs(folder, exist_ok=True)
        return folder

    def _ensure_unique_display_name(self, name, existing):
        if name not in existing:
            return name
        counter = 1
        base = name
        while True:
            candidate = f"{base} ({counter})"
            if candidate not in existing:
                return candidate
            counter += 1

    def _gather_preset_download_info(self, display_name: str, preset_path: str) -> Dict[str, object]:
        info: Dict[str, object] = {
            "has_media": False,
            "media_count": 0,
            "media_types": [],
            "media_paths": [],
            "last_media_modified": None,
            "db": {},
        }

        try:
            with open(preset_path, "r", encoding="utf-8") as handle:
                preset_data = json.load(handle) or {}
        except Exception as err:
            info["error"] = str(err)
            return info

        candidate_keys = [
            "downloaded_posts_folder",
            "png_folder",
            "jpg_folder",
            "webm_folder",
            "gif_folder",
            "swf_folder",
        ]
        directories: List[str] = []
        for key in candidate_keys:
            folder = preset_data.get(key)
            if not folder:
                continue
            resolved = self._resolve_download_directory(folder, preset_path)
            if resolved and resolved not in directories:
                directories.append(resolved)
        info["media_paths"] = directories

        media_extensions = {".png", ".jpg", ".jpeg", ".mp4", ".webp", ".webm"}
        media_types = set()
        media_count = 0
        last_modified = None
        for directory in directories:
            if not directory or not os.path.isdir(directory):
                continue
            for root, _, files in os.walk(directory):
                for fname in files:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext not in media_extensions:
                        continue
                    media_count += 1
                    media_types.add(ext)
                    try:
                        mtime = os.path.getmtime(os.path.join(root, fname))
                    except OSError:
                        continue
                    if last_modified is None or mtime > last_modified:
                        last_modified = mtime

        info["media_count"] = media_count
        info["media_types"] = sorted(media_types)
        if last_modified is not None:
            info["last_media_modified"] = datetime.fromtimestamp(last_modified).isoformat()
        info["has_media"] = media_count > 0

        if self.db_manager:
            db_stats = self.db_manager.summarize_preset_downloads(
                preset_path=os.path.abspath(preset_path),
                preset_name=display_name,
                fallback_last_download=info.get("last_media_modified"),
                file_count=media_count,
                file_types=info["media_types"],
            ) or {}
            if db_stats.get("last_download_at") and not info.get("last_media_modified"):
                info["last_media_modified"] = db_stats["last_download_at"]
            info["has_media"] = info["has_media"] or bool(db_stats.get("total_files_downloaded"))
            info["db"] = db_stats

        return info

    def _update_preset_status(self, display_names: List[str], mapping: Dict[str, str]) -> None:
        status: Dict[str, Dict[str, object]] = {}
        for name in display_names:
            path = mapping.get(name)
            if not path:
                continue
            status[name] = self._gather_preset_download_info(name, path)
        self.preset_download_status = status

    def _downloaded_preset_names(self) -> List[str]:
        downloaded = []
        for name, info in self.preset_download_status.items():
            if info.get("has_media"):
                downloaded.append(name)
                continue
            db_info = info.get("db", {}) if isinstance(info, dict) else {}
            if isinstance(db_info, dict) and db_info.get("total_files_downloaded"):
                downloaded.append(name)
        downloaded.sort(key=str.casefold)
        return downloaded

    def _build_downloaded_css(self, downloaded: Optional[List[str]] = None) -> str:
        downloaded = downloaded if downloaded is not None else self._downloaded_preset_names()
        style_lines = [
            "<style id='preset-download-style'>",
            "#preset-checkboxgroup label.preset-downloaded {",
            "    background-color: #f9d5d5;",
            "    border-radius: 4px;",
            "    padding: 4px 6px;",
            "}",
            "#preset-checkboxgroup label span.preset-downloaded-text {",
            "    background-color: #f9d5d5;",
            "    border-radius: 4px;",
            "    padding: 2px 6px;",
            "}",
            "</style>",
        ]

        script_lines = [
            "<script>",
            "(function(){",
            f"  const downloaded = {json.dumps(downloaded)};",
            "  const root = document.querySelector('#preset-checkboxgroup');",
            "  if (!root) { return; }",
            "  const cssEscape = (value) => {",
            "    if (window.CSS && typeof window.CSS.escape === 'function') {",
            "      return window.CSS.escape(value);",
            "    }",
            "    return String(value).replace(/([^a-zA-Z0-9_\-])/g, match => `\\${match}`);",
            "  };",
            "  const apply = () => {",
            "    const labels = root.querySelectorAll('label');",
            "    labels.forEach(label => {",
            "      label.classList.remove('preset-downloaded');",
            "      const span = label.querySelector('span');",
            "      if (span) { span.classList.remove('preset-downloaded-text'); }",
            "    });",
            "    downloaded.forEach(name => {",
            "      try {",
            "        const selector = `input[value=\"${cssEscape(name)}\"]`;",
            "        const input = root.querySelector(selector);",
            "        if (!input) { return; }",
            "        const label = input.closest('label');",
            "        if (label) {",
            "          label.classList.add('preset-downloaded');",
            "          const span = input.nextElementSibling;",
            "          if (span) { span.classList.add('preset-downloaded-text'); }",
            "        }",
            "      } catch (err) {",
            "        console.warn('Failed to update preset checkbox style', err);",
            "      }",
            "    });",
            "  };",
            "  if (root.__presetDownloadedObserver) {",
            "    try { root.__presetDownloadedObserver.disconnect(); } catch (err) { console.warn(err); }",
            "  }",
            "  root.__presetDownloadedObserver = new MutationObserver(() => apply());",
            "  root.__presetDownloadedObserver.observe(root, { childList: true, subtree: true });",
            "  apply();",
            "})();",
            "</script>",
        ]

        return "\n".join(style_lines + script_lines)

    def _load_preset_files(self):
        folder = self.get_active_preset_directory()
        json_paths = sorted(glob.glob(os.path.join(folder, "*.json")))
        mapping = {}
        display_names = []
        for path in json_paths:
            display = os.path.splitext(os.path.basename(path))[0]
            display = self._ensure_unique_display_name(display, mapping)
            resolved = os.path.abspath(path)
            mapping[display] = resolved
            display_names.append(display)
        self.batch_to_json_map = mapping
        display_names.sort(key=str.casefold)
        self._update_preset_status(display_names, mapping)
        return display_names, mapping

    def _build_preset_folder_notice(self, extra_message=None):
        folder = self.get_active_preset_directory()
        default = self.default_preset_folder
        lines = [f"**Preset folder:** `{folder}`"]
        if os.path.abspath(folder) != os.path.abspath(default):
            lines.append(f"⚠️ Currently differs from current working directory `{default}`. Update if unintended.")
        else:
            lines.append("Using the current working directory for presets.")
        if extra_message:
            lines.append("")
            lines.append(extra_message)
        return "\n\n".join(lines)

    def _notice_update(self, extra_message=None):
        return gr.update(value=self._build_preset_folder_notice(extra_message))

    def update_preset_notice(self):
        return self._notice_update()

    def refresh_presets_and_notice(self):
        checkbox_update, dropdown_update, style_update = self.refresh_json_options()
        return checkbox_update, dropdown_update, style_update, self._notice_update()

    def update_preset_folder_textbox(self, folder_path):
        if isinstance(folder_path, list):
            folder_path = folder_path[0] if folder_path else ""
        if not folder_path:
            return gr.update(value=self.preset_folder)
        return gr.update(value=str(folder_path))

    def apply_preset_folder_selection(self, folder_path):
        try:
            resolved = self._resolve_folder_path(folder_path)
            os.makedirs(resolved, exist_ok=True)
        except Exception as err:
            checkbox_update, dropdown_update, style_update = self.refresh_json_options()
            message = f"Failed to set preset folder: {err}"
            return (
                gr.update(value=self.preset_folder),
                checkbox_update,
                dropdown_update,
                style_update,
                self._notice_update(message),
            )

        previous_folder = self.settings_json.get("preset_folder")
        if previous_folder:
            try:
                previous_folder = self._resolve_folder_path(previous_folder)
            except Exception:
                previous_folder = None

        self.preset_folder = resolved
        self.settings_json["preset_folder"] = resolved
        persist_to_db = True
        if previous_folder and os.path.abspath(previous_folder) == resolved:
            persist_to_db = False
        self._persist_settings(persist_to_db=persist_to_db)
        preset_config.set_preset_folder(self.preset_folder)
        checkbox_update, dropdown_update, style_update = self.refresh_json_options()
        return (
            gr.update(value=self.preset_folder),
            checkbox_update,
            dropdown_update,
            style_update,
            self._notice_update(),
        )

    def _unique_destination(self, destination):
        base, ext = os.path.splitext(destination)
        candidate = destination
        counter = 1
        while os.path.exists(candidate):
            candidate = f"{base}_{counter}{ext}"
            counter += 1
        return candidate

    def archive_selected_presets(self, selected):
        selected = self._normalize_selection(selected)
        if not selected:
            checkbox_update, dropdown_update, style_update = self.refresh_json_options()
            return (
                checkbox_update,
                dropdown_update,
                style_update,
                self._notice_update("No presets selected to archive."),
            )

        archive_dir = os.path.join(self.get_active_preset_directory(), "preset_archive")
        os.makedirs(archive_dir, exist_ok=True)
        moved = 0
        for name in selected:
            path = self.batch_to_json_map.get(name)
            if not path:
                continue
            resolved = self._resolve_file_path(path)
            if not os.path.isfile(resolved):
                continue
            destination = self._unique_destination(os.path.join(archive_dir, os.path.basename(resolved)))
            shutil.move(resolved, destination)
            moved += 1
            if self.db_manager:
                self.db_manager.remove_config_by_path(resolved)
        checkbox_update, dropdown_update, style_update = self.refresh_json_options()
        if moved:
            message = f"Archived {moved} preset{'s' if moved != 1 else ''} to `{archive_dir}`."
        else:
            message = "Selected presets could not be archived."
        return checkbox_update, dropdown_update, style_update, self._notice_update(message)

    def delete_selected_presets(self, selected):
        selected = self._normalize_selection(selected)
        if not selected:
            checkbox_update, dropdown_update, style_update = self.refresh_json_options()
            return (
                checkbox_update,
                dropdown_update,
                style_update,
                self._notice_update("No presets selected to delete."),
            )

        removed = 0
        for name in selected:
            path = self.batch_to_json_map.get(name)
            if not path:
                continue
            resolved = self._resolve_file_path(path)
            if os.path.isfile(resolved):
                os.remove(resolved)
                removed += 1
                if self.db_manager:
                    self.db_manager.remove_config_by_path(resolved)
        checkbox_update, dropdown_update, style_update = self.refresh_json_options()
        if removed:
            message = f"Deleted {removed} preset{'s' if removed != 1 else ''}."
        else:
            message = "Selected presets could not be deleted."
        return checkbox_update, dropdown_update, style_update, self._notice_update(message)

    def _normalize_selection(self, selected):
        if selected is None:
            return []
        if isinstance(selected, (list, tuple, set)):
            return list(selected)
        if isinstance(selected, (str, bytes)):
            return [selected]
        return [selected]

    def refresh_json_options(self):
        """Refresh config dropdown choices based on the active preset folder."""
        batch_names, _ = self._load_preset_files()
        default_value = batch_names[0] if batch_names else None
        style_update = gr.update(value=self._build_downloaded_css())
        return (
            gr.update(choices=batch_names, value=[]),
            gr.update(choices=batch_names, value=default_value),
            style_update,
        )

    def apply_preset_selection_action(self, action, current_selection):
        batch_names, _ = self._load_preset_files()
        normalized_selection = set(self._normalize_selection(current_selection))

        if action == "Select All":
            new_selection = list(batch_names)
        elif action == "Deselect All":
            new_selection = []
        elif action == "Invert Selection":
            new_selection = [name for name in batch_names if name not in normalized_selection]
        else:
            new_selection = list(normalized_selection)

        checkbox_update = gr.update(choices=batch_names, value=new_selection)
        style_update = gr.update(value=self._build_downloaded_css())
        return checkbox_update, gr.update(value=None), style_update

    def import_queries(self, query_file):
        """Create configs from query file and insert DB entries."""
        if not query_file:
            return self.refresh_json_options()

        path = query_file.name if hasattr(query_file, "name") else query_file
        try:
            with open(path, "r", encoding="utf-8") as f:
                queries = [ln.strip() for ln in f if ln.strip()]
        except Exception:
            return self.refresh_json_options()

        cfg_dir = self.get_active_preset_directory()
        os.makedirs(cfg_dir, exist_ok=True)

        for idx, q in enumerate(queries):
            cfg = copy.deepcopy(self.settings_json)
            cfg["required_tags"] = q
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in q)[:50]
            fname = f"query_{safe or idx}.json"
            fpath = os.path.join(cfg_dir, fname)
            count = 1
            while os.path.exists(fpath):
                fpath = os.path.join(cfg_dir, f"{safe or idx}_{count}.json")
                count += 1
            help.update_JSON(cfg, fpath)
            if self.db_manager:
                preset_name = os.path.splitext(os.path.basename(fpath))[0]
                self.db_manager.add_download_record(
                    "e621",
                    json.dumps(cfg),
                    fpath,
                    preset_name=preset_name,
                )

        return self.refresh_json_options()

    # load a different config
    def change_config_batch_run(self, json_name_list, file_path):
        temp = '\\' if help.is_windows() else '/'
        name = json_name_list[-1]
        name = self.batch_to_json_map[name]

        settings_path = None

        if name != self.config_name:
            path = self._resolve_file_path(name)
            self.settings_json = help.load_session_config(path)
            self.config_name = path
            settings_path = gr.update(value=self.config_name)
        else:
            if file_path:
                path = self._resolve_file_path(file_path)
                self.settings_json = help.load_session_config(path)
                self.config_name = path
                settings_path = gr.update(value=self.config_name)

        self.required_tags_list = help.get_list(self.settings_json["required_tags"], self.settings_json["tag_sep"])
        for tag in self.required_tags_list:
            if len(tag) == 0:
                self.required_tags_list.remove(tag)

        self.blacklist_tags = help.get_list(self.settings_json["blacklist"], " | ")
        for tag in self.blacklist_tags:
            if len(tag) == 0:
                self.blacklist_tags.remove(tag)

        help.verbose_print(f"{self.settings_json}")
        help.verbose_print(f"json key count: {len(self.settings_json)}")

        # UPDATE json with new key, value pairs
        if not "min_date" in self.settings_json:
            self.settings_json["min_year"] = 2000
        elif isinstance(self.settings_json["min_date"], str) and "-" in self.settings_json["min_date"]:
            self.settings_json["min_year"] = int(self.settings_json["min_date"].split("-")[0])
        else:
            self.settings_json["min_year"] = int(self.settings_json["min_date"])

        if not "min_month" in self.settings_json:
            self.settings_json["min_month"] = 1
        elif isinstance(self.settings_json["min_date"], str) and "-" in self.settings_json["min_date"]:
            self.settings_json["min_month"] = help.from_padded(self.settings_json["min_date"].split("-")[1])

        if not "min_day" in self.settings_json:
            self.settings_json["min_day"] = 1
        elif isinstance(self.settings_json["min_date"], str) and self.settings_json["min_date"].count("-") > 1:
            self.settings_json["min_day"] = help.from_padded(self.settings_json["min_date"].split("-")[-1])

        help.update_JSON(self.settings_json, self.config_name)

        # load all presets
        batch_folder = gr.update(value=self.settings_json["batch_folder"])
        resized_img_folder = gr.update(value=self.settings_json["resized_img_folder"])
        tag_sep = gr.update(value=self.settings_json["tag_sep"])
        tag_order_format = gr.update(value=self.image_board.tag_order)

        prepend_tags_text = []
        if len(self.settings_json["prepend_tags"]) > 0:
            prepend_tags_text = self.settings_json["prepend_tags"].split(self.settings_json["tag_sep"])
        append_tags_text = []
        if len(self.settings_json["append_tags"]) > 0:
            append_tags_text = self.settings_json["append_tags"].split(self.settings_json["tag_sep"])

        prepend_tags = gr.update(choices=prepend_tags_text, value=prepend_tags_text)
        append_tags = gr.update(choices=append_tags_text, value=append_tags_text)

        img_ext = gr.update(value=self.settings_json["img_ext"])
        method_tag_files = gr.update(value=self.settings_json["method_tag_files"])
        min_score = gr.update(value=self.settings_json["min_score"])
        min_fav_count = gr.update(value=self.settings_json["min_fav_count"])
        min_month = gr.update(value=self.settings_json["min_month"])
        min_day = gr.update(value=self.settings_json["min_day"])
        min_year = gr.update(value=self.settings_json["min_year"])
        min_area = gr.update(value=self.settings_json["min_area"])
        top_n = gr.update(value=self.settings_json["top_n"])
        min_short_side = gr.update(value=self.settings_json["min_short_side"])
        collect_checkbox_group_var = gr.update(choices=self.collect_checkboxes,
                                               value=help.grab_pre_selected(self.settings_json, self.collect_checkboxes))
        download_checkbox_group_var = gr.update(choices=self.download_checkboxes,
                                                value=help.grab_pre_selected(self.settings_json, self.download_checkboxes))
        resize_checkbox_group_var = gr.update(choices=self.resize_checkboxes,
                                              value=help.grab_pre_selected(self.settings_json, self.resize_checkboxes))
        required_tags_group_var = gr.update(choices=self.required_tags_list, value=[])
        blacklist_tags_group_var = gr.update(choices=self.blacklist_tags, value=[])
        skip_posts_file = gr.update(value=self.settings_json["skip_posts_file"])
        skip_posts_type = gr.update(value=self.settings_json["skip_posts_type"])
        collect_from_listed_posts_file = gr.update(value=self.settings_json["collect_from_listed_posts_file"])
        collect_from_listed_posts_type = gr.update(value=self.settings_json["collect_from_listed_posts_type"])
        apply_filter_to_listed_posts = gr.update(value=self.settings_json["apply_filter_to_listed_posts"])
        save_searched_list_type = gr.update(value=self.settings_json["save_searched_list_type"])
        save_searched_list_path = gr.update(value=self.settings_json["save_searched_list_path"])
        downloaded_posts_folder = gr.update(value=self.settings_json["downloaded_posts_folder"])
        png_folder = gr.update(value=self.settings_json["png_folder"])
        jpg_folder = gr.update(value=self.settings_json["jpg_folder"])
        webm_folder = gr.update(value=self.settings_json["webm_folder"])
        gif_folder = gr.update(value=self.settings_json["gif_folder"])
        swf_folder = gr.update(value=self.settings_json["swf_folder"])
        save_filename_type = gr.update(value=self.settings_json["save_filename_type"])
        remove_tags_list = gr.update(value=self.settings_json["remove_tags_list"])
        replace_tags_list = gr.update(value=self.settings_json["replace_tags_list"])
        tag_count_list_folder = gr.update(value=self.settings_json["tag_count_list_folder"])
        proxy_url_textbox = gr.update(value=self.settings_json["proxy_url"])

        custom_csv_path_textbox = gr.update(value=self.settings_json["use_csv_custom"])
        use_csv_custom_checkbox = gr.update(value=self.settings_json["csv_custom_path"])


        override_download_delay_checkbox = gr.update(value=self.settings_json["override_download_delay"])
        custom_download_delay_slider = gr.update(value=self.settings_json["custom_download_delay"])
        custom_retry_attempts_slider = gr.update(value=self.settings_json["custom_retry_attempts"])


        help.verbose_print(f"{self.settings_json}")
        help.verbose_print(f"json key count: {len(self.settings_json)}")

        self.is_csv_loaded = False

        # get file names & create dictionary mappings to batch file names
        batch_names, mapping = self._load_preset_files()

        current_display = next(
            (key for key, value in mapping.items() if os.path.abspath(value) == os.path.abspath(self.config_name)),
            None,
        )

        all_json_files_checkboxgroup = gr.update(choices=batch_names, value=[])
        quick_json_select = gr.update(
            choices=batch_names,
            value=current_display if current_display else (batch_names[0] if batch_names else None),
        )

        return batch_folder, resized_img_folder, tag_sep, tag_order_format, prepend_tags, append_tags, img_ext, method_tag_files, min_score, min_fav_count, min_year, min_month, \
               min_day, min_area, top_n, min_short_side, collect_checkbox_group_var, download_checkbox_group_var, resize_checkbox_group_var, required_tags_group_var, \
               blacklist_tags_group_var, skip_posts_file, skip_posts_type, collect_from_listed_posts_file, collect_from_listed_posts_type, apply_filter_to_listed_posts, \
               save_searched_list_type, save_searched_list_path, downloaded_posts_folder, png_folder, jpg_folder, webm_folder, gif_folder, swf_folder, save_filename_type, \
               remove_tags_list, replace_tags_list, tag_count_list_folder, all_json_files_checkboxgroup, quick_json_select, proxy_url_textbox, settings_path, \
               custom_csv_path_textbox, use_csv_custom_checkbox, override_download_delay_checkbox, custom_download_delay_slider, custom_retry_attempts_slider

    # load a different config
    def change_config(self, selected: gr.SelectData, file_path):
        selected = selected.value
        selected = self.batch_to_json_map[selected]

        temp = '\\' if help.is_windows() else '/'

        settings_path = None

        if selected != self.config_name:
            path = self._resolve_file_path(selected)
            self.settings_json = help.load_session_config(path)
            self.config_name = path
            settings_path = gr.update(value=self.config_name)
        else:
            if file_path:
                path = self._resolve_file_path(file_path)
                self.settings_json = help.load_session_config(path)
                self.config_name = path
                settings_path = gr.update(value=self.config_name)

        self.required_tags_list = help.get_list(self.settings_json["required_tags"], self.settings_json["tag_sep"])
        for tag in self.required_tags_list:
            if len(tag) == 0:
                self.required_tags_list.remove(tag)

        self.blacklist_tags = help.get_list(self.settings_json["blacklist"], " | ")
        for tag in self.blacklist_tags:
            if len(tag) == 0:
                self.blacklist_tags.remove(tag)

        help.verbose_print(f"{self.settings_json}")
        help.verbose_print(f"json key count: {len(self.settings_json)}")

        # UPDATE json with new key, value pairs
        if not "min_date" in self.settings_json:
            self.settings_json["min_year"] = 2000
        elif isinstance(self.settings_json["min_date"], str) and "-" in self.settings_json["min_date"]:
            self.settings_json["min_year"] = int(self.settings_json["min_date"].split("-")[0])
        else:
            self.settings_json["min_year"] = int(self.settings_json["min_date"])

        if not "min_month" in self.settings_json:
            self.settings_json["min_month"] = 1
        elif isinstance(self.settings_json["min_date"], str) and "-" in self.settings_json["min_date"]:
            self.settings_json["min_month"] = help.from_padded(self.settings_json["min_date"].split("-")[1])

        if not "min_day" in self.settings_json:
            self.settings_json["min_day"] = 1
        elif isinstance(self.settings_json["min_date"], str) and self.settings_json["min_date"].count("-") > 1:
            self.settings_json["min_day"] = help.from_padded(self.settings_json["min_date"].split("-")[-1])

        help.update_JSON(self.settings_json, self.config_name)

        # load all presets
        batch_folder = gr.update(value=self.settings_json["batch_folder"])
        resized_img_folder = gr.update(value=self.settings_json["resized_img_folder"])
        tag_sep = gr.update(value=self.settings_json["tag_sep"])
        tag_order_format = gr.update(value=self.image_board.tag_order)

        prepend_tags_text = []
        if len(self.settings_json["prepend_tags"]) > 0:
            prepend_tags_text = self.settings_json["prepend_tags"].split(self.settings_json["tag_sep"])
        append_tags_text = []
        if len(self.settings_json["append_tags"]) > 0:
            append_tags_text = self.settings_json["append_tags"].split(self.settings_json["tag_sep"])

        prepend_tags = gr.update(choices=prepend_tags_text, value=prepend_tags_text)
        append_tags = gr.update(choices=append_tags_text, value=append_tags_text)

        img_ext = gr.update(value=self.settings_json["img_ext"])
        method_tag_files = gr.update(value=self.settings_json["method_tag_files"])
        min_score = gr.update(value=self.settings_json["min_score"])
        min_fav_count = gr.update(value=self.settings_json["min_fav_count"])
        min_month = gr.update(value=self.settings_json["min_month"])
        min_day = gr.update(value=self.settings_json["min_day"])
        min_year = gr.update(value=self.settings_json["min_year"])
        min_area = gr.update(value=self.settings_json["min_area"])
        top_n = gr.update(value=self.settings_json["top_n"])
        min_short_side = gr.update(value=self.settings_json["min_short_side"])
        collect_checkbox_group_var = gr.update(choices=self.collect_checkboxes,
                                               value=help.grab_pre_selected(self.settings_json, self.collect_checkboxes))
        download_checkbox_group_var = gr.update(choices=self.download_checkboxes,
                                                value=help.grab_pre_selected(self.settings_json, self.download_checkboxes))
        resize_checkbox_group_var = gr.update(choices=self.resize_checkboxes,
                                              value=help.grab_pre_selected(self.settings_json, self.resize_checkboxes))
        required_tags_group_var = gr.update(choices=self.required_tags_list, value=[])
        blacklist_tags_group_var = gr.update(choices=self.blacklist_tags, value=[])
        skip_posts_file = gr.update(value=self.settings_json["skip_posts_file"])
        skip_posts_type = gr.update(value=self.settings_json["skip_posts_type"])
        collect_from_listed_posts_file = gr.update(value=self.settings_json["collect_from_listed_posts_file"])
        collect_from_listed_posts_type = gr.update(value=self.settings_json["collect_from_listed_posts_type"])
        apply_filter_to_listed_posts = gr.update(value=self.settings_json["apply_filter_to_listed_posts"])
        save_searched_list_type = gr.update(value=self.settings_json["save_searched_list_type"])
        save_searched_list_path = gr.update(value=self.settings_json["save_searched_list_path"])
        downloaded_posts_folder = gr.update(value=self.settings_json["downloaded_posts_folder"])
        png_folder = gr.update(value=self.settings_json["png_folder"])
        jpg_folder = gr.update(value=self.settings_json["jpg_folder"])
        webm_folder = gr.update(value=self.settings_json["webm_folder"])
        gif_folder = gr.update(value=self.settings_json["gif_folder"])
        swf_folder = gr.update(value=self.settings_json["swf_folder"])
        save_filename_type = gr.update(value=self.settings_json["save_filename_type"])
        remove_tags_list = gr.update(value=self.settings_json["remove_tags_list"])
        replace_tags_list = gr.update(value=self.settings_json["replace_tags_list"])
        tag_count_list_folder = gr.update(value=self.settings_json["tag_count_list_folder"])
        proxy_url_textbox = gr.update(value=self.settings_json["proxy_url"])

        custom_csv_path_textbox = gr.update(value=self.settings_json["csv_custom_path"])
        use_csv_custom_checkbox = gr.update(value=self.settings_json["use_csv_custom"])


        override_download_delay_checkbox = gr.update(value=self.settings_json["override_download_delay"])
        custom_download_delay_slider = gr.update(value=self.settings_json["custom_download_delay"])
        custom_retry_attempts_slider = gr.update(value=self.settings_json["custom_retry_attempts"])


        help.verbose_print(f"{self.settings_json}")
        help.verbose_print(f"json key count: {len(self.settings_json)}")

        self.is_csv_loaded = False

        # get file names & create dictionary mappings to batch file names
        batch_names, _ = self._load_preset_files()

        all_json_files_checkboxgroup = gr.update(choices=batch_names, value=[])
        quick_json_select = gr.update(choices=batch_names, value=batch_names[0] if batch_names else None)

        return batch_folder, resized_img_folder, tag_sep, tag_order_format, prepend_tags, append_tags, img_ext, method_tag_files, min_score, min_fav_count, min_year, min_month, \
               min_day, min_area, top_n, min_short_side, collect_checkbox_group_var, download_checkbox_group_var, resize_checkbox_group_var, required_tags_group_var, \
               blacklist_tags_group_var, skip_posts_file, skip_posts_type, collect_from_listed_posts_file, collect_from_listed_posts_type, apply_filter_to_listed_posts, \
               save_searched_list_type, save_searched_list_path, downloaded_posts_folder, png_folder, jpg_folder, webm_folder, gif_folder, swf_folder, save_filename_type, \
               remove_tags_list, replace_tags_list, tag_count_list_folder, all_json_files_checkboxgroup, quick_json_select, proxy_url_textbox, settings_path, \
               custom_csv_path_textbox, use_csv_custom_checkbox, override_download_delay_checkbox, custom_download_delay_slider, custom_retry_attempts_slider

    def change_config_file(self, file_path):
        """Wrapper to load a config directly from a file picker."""
        if file_path is None:
            return [gr.update() for _ in range(48)]  # no-op if no file selected
        sd = gr.SelectData(value=help.get_batch_name(file_path))
        return self.change_config(sd, file_path)

    def textbox_handler_required(self, tag_string_comp, state, is_textbox):
        # help.verbose_print(f"tag_string_comp:\t{tag_string_comp}")
        # help.verbose_print(f"state:\t{state}")
        # help.verbose_print(f"len(tag_string_comp):\t{len(tag_string_comp)}")

        if tag_string_comp is not None and len(tag_string_comp) and (not tag_string_comp in self.required_tags_list):
            self.required_tags_list.append(tag_string_comp)

        new_textbox_value = "" if is_textbox else state
        new_state_tag = new_textbox_value

        check_box_group = gr.update(choices=self.required_tags_list, value=[])
        return new_state_tag, check_box_group, gr.update(value=new_textbox_value)

    def textbox_handler_blacklist(self, tag_string_comp, state, is_textbox):
        # help.verbose_print(f"tag_string_comp:\t{tag_string_comp}")
        # help.verbose_print(f"state:\t{state}")
        # help.verbose_print(f"len(tag_string_comp):\t{len(tag_string_comp)}")

        if tag_string_comp is not None and len(tag_string_comp) and (not tag_string_comp in self.blacklist_tags):
            self.blacklist_tags.append(tag_string_comp)

        new_textbox_value = "" if is_textbox else state
        new_state_tag = new_textbox_value

        check_box_group = gr.update(choices=self.blacklist_tags, value=[])
        return new_state_tag, check_box_group, gr.update(value=new_textbox_value)

    def gen_tags_list(self, reference_model_tags_file):
        help.convert_to_list_file(reference_model_tags_file)
        help.verbose_print(f"done")

    def gen_tags_diff_list(self, reference_model_tags_file):
        df_keep = pd.read_csv(reference_model_tags_file)
        first_column_keep = df_keep.iloc[:, 0]
        first_column_keep = first_column_keep.iloc[1:]
        set_keep = set(first_column_keep)

        tags_current_path = os.path.join(os.getcwd(), str(self.settings_json["batch_folder"]),
                                         str(self.settings_json["tag_count_list_folder"]), "tags.csv")
        df_current = pd.read_csv(tags_current_path)
        first_column_current = df_current.iloc[:, 0]
        first_column_current = first_column_current.iloc[1:]
        set_current = set(first_column_current)

        # Calculate the difference between set1 and set2
        difference_set = set_current - (set_current & set_keep)
        # Save the difference elements to a text file
        with open('remove_tags.txt', 'w') as f:
            for element in difference_set:
                f.write(element + '\n')
        # Delete the dataframe
        del first_column_keep
        del first_column_current
        help.verbose_print(f"done")

    def filter_out(self):
        temp_key_list = list(self.gallery_tab_manager.all_images_dict.keys())
        temp_tag_freq_table = {}

        if "searched" in temp_key_list:
            for ext in list(self.gallery_tab_manager.all_images_dict["searched"].keys()):
                for img_id in list(self.gallery_tab_manager.all_images_dict["searched"][ext].keys()):
                    if not img_id in list(self.auto_complete_config[ext].keys()):
                        # generate frequency table for images being removed
                        # no frequency table here to prevent duplicates
                        # delete entry
                        del self.gallery_tab_manager.all_images_dict["searched"][ext][img_id]
            temp_key_list.remove("searched")

        for ext in temp_key_list:
            for img_id in list(self.gallery_tab_manager.all_images_dict[ext].keys()):
                if not img_id in list(self.auto_complete_config[ext].keys()):
                    # generate frequency table for images being removed
                    for tag in self.gallery_tab_manager.all_images_dict[ext][img_id]:
                        if not tag in list(temp_tag_freq_table.keys()):
                            temp_tag_freq_table[tag] = 1
                        else:
                            temp_tag_freq_table[tag] += 1
                    # delete entry
                    del self.gallery_tab_manager.all_images_dict[ext][img_id]

        # remove all tags from the csvs
        for tag in list(temp_tag_freq_table.keys()):
            category_key = self.gallery_tab_manager.get_category_name(tag)
            if category_key:
                # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
                # edit csv dictionaries
                self.gallery_tab_manager.remove_to_csv_dictionaries(category_key, tag, temp_tag_freq_table[tag])
        # persist
        self.gallery_tab_manager.csv_persist_to_disk()

    ###
    # update_per_image -> ['-', tag] or ['+', tag, index]
    ###
    def apply_stack_changes(self, progress=gr.Progress()):
        temp_key_list = list(self.gallery_tab_manager.all_images_dict.keys())
        temp_tag_freq_table = {}

        if "searched" in temp_key_list:
            # clear searched dict
            del self.gallery_tab_manager.all_images_dict["searched"]
            self.gallery_tab_manager.all_images_dict["searched"] = {}
            temp_key_list.remove("searched")

        for ext in temp_key_list:
            valid_images = list(self.auto_complete_config[ext].keys())
            progress(0, desc="Applying Tag Filters...")
            for i in progress.tqdm(range(0, len(valid_images), 1), desc=f"{ext}:\tTag Filtering Progress"):
                img_id = valid_images[i]

                for update in self.auto_complete_config[ext][img_id]:
                    if '-' in update:  # remove
                        tag = update[-1]
                        # remove tag
                        self.gallery_tab_manager.all_images_dict[ext][img_id].remove(tag)
                        if not tag in list(temp_tag_freq_table.keys()):
                            temp_tag_freq_table[tag] = -1
                        else:
                            temp_tag_freq_table[tag] -= 1
                    else:  # add
                        tag = update[1]
                        index = update[-1]
                        # add tag
                        self.gallery_tab_manager.all_images_dict[ext][img_id].insert(index, tag)
                        if not tag in list(temp_tag_freq_table.keys()):
                            temp_tag_freq_table[tag] = 1
                        else:
                            temp_tag_freq_table[tag] += 1

            # remove invalid images
            ext_all_images = list(self.gallery_tab_manager.all_images_dict[ext].keys())
            progress(0, desc="Applying Image Filters...")
            for i in progress.tqdm(range(len(ext_all_images) - 1, -1, -1), desc=f"{ext}:\tImage Filtering Progress"):
                img_id = ext_all_images[i]

                if not img_id in valid_images:
                    # remove tags
                    for tag in self.gallery_tab_manager.all_images_dict[ext][img_id]:
                        if not tag in list(temp_tag_freq_table.keys()):
                            temp_tag_freq_table[tag] = -1
                        else:
                            temp_tag_freq_table[tag] -= 1
                    # remove image
                    del self.gallery_tab_manager.all_images_dict[ext][img_id]

        # create an add and remove frequency table
        positive_table = {}
        negative_table = {}
        for tag in list(temp_tag_freq_table.keys()):
            if temp_tag_freq_table[tag] > 0:
                positive_table[tag] = temp_tag_freq_table[tag]
            elif temp_tag_freq_table[tag] < 0:
                negative_table[tag] = abs(temp_tag_freq_table[tag])  # make positive
        # add to csvs
        for tag in list(positive_table.keys()):
            category_key = self.gallery_tab_manager.get_category_name(tag)
            if category_key:
                # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
                self.gallery_tab_manager.add_to_csv_dictionaries(category_key, tag, positive_table[tag])
        # remove to csvs
        for tag in list(negative_table.keys()):
            category_key = self.gallery_tab_manager.get_category_name(tag)
            if category_key:
                # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
                self.gallery_tab_manager.remove_to_csv_dictionaries(category_key, tag, negative_table[tag])

        # persist
        self.gallery_tab_manager.csv_persist_to_disk()
        full_path_downloads = os.path.join(os.path.join(self.cwd, self.settings_json["batch_folder"]),
                                           self.settings_json["downloaded_posts_folder"])
        for ext in list(self.gallery_tab_manager.all_images_dict.keys()):
            ext_all_images = list(self.gallery_tab_manager.all_images_dict[ext].keys())
            progress(0, desc="Saving Changes...")
            for i in progress.tqdm(range(0, len(ext_all_images), 1), desc=f"{ext}:\tSaving Changes Progress"):
                img_id = ext_all_images[i]
                full_path_gallery_type = os.path.join(full_path_downloads, self.settings_json[f"{ext}_folder"])
                full_path = os.path.join(full_path_gallery_type, f"{img_id}.txt")
                temp_tag_string = ",".join(self.gallery_tab_manager.all_images_dict[ext][img_id])
                help.write_tags_to_text_file(temp_tag_string, full_path)  # update img txt file

        # display stats
        png_cnt, jpg_cnt, gif_cnt, total_imgs = self.gallery_tab_manager.get_saved_image_count()
        help.verbose_print(f"total_imgs:\t{total_imgs}")
        help.verbose_print(f"png_cnt:\t{png_cnt}")
        help.verbose_print(f"jpg_cnt:\t{jpg_cnt}")
        help.verbose_print(f"gif_cnt:\t{gif_cnt}")
        help.verbose_print("Done")
        return gr.update(interactive=False, visible=False)

    def auto_config_apply(self, images_full_change_dict_textbox, progress=gr.Progress()):
        if len(images_full_change_dict_textbox) > 0 and self.auto_complete_config and (
                (len(list(self.auto_complete_config['png'].keys())) > 0) or (
                len(list(self.auto_complete_config['jpg'].keys())) > 0) or (
                        len(list(self.auto_complete_config['gif'].keys())) > 0)):  # if file is empty DO NOT RUN
            # load correct config
            self.check_to_reload_auto_complete_config(images_full_change_dict_textbox)

            # load the csvs if not already loaded and the image dictionaries
            self.gallery_tab_manager.load_images_and_csvs()

            # filter out invalid images & update CSVs
            # filter_out()

            # apply every in order image change & remove invalid images & update CSVs & save image changes
            return self.apply_stack_changes(progress)
        else:
            raise ValueError('no path name specified | no config created | config empty')

    def load_single_tag_json(self, selected, existing_tags, json, json_key):
        selected = [selected] if not isinstance(selected, list) else selected
        tags = None
        # only load existing tags if (one) is selected
        if len(selected) == 1:
            # display contents for that entry
            tags = gr.update(choices=json[selected[0]][json_key])
        else:
            tags = gr.update(choices=existing_tags)
        return tags

    def new_json_proto_entry(self, json, json_key):
        # json update
        next_entry_key = str((max([int(key) for key in json.keys()]) + 1) if (len(list(json.keys())) > 0) else 0)
        json[next_entry_key] = {"required": {}, "blacklist": {}}
        json[next_entry_key][json_key] = []
        json_update = gr.update(value=json)
        # entry dropdown update
        dropdown = gr.update(choices=list(json.keys()), value=[])
        # current checkbox group clear
        # checkbox_group = gr.update(choices=[], value=[])
        return json_update, dropdown, json_update, dropdown#checkbox_group

    def reset_json_proto_entry(self, json, json_key, selected):
        selected = [selected] if not isinstance(selected, list) else selected
        for entry_number in selected:
            # json update
            json[entry_number][json_key] = []
        json_update = gr.update(value=json)
        # current checkbox group clear
        # checkbox_group = gr.update(choices=[], value=[])
        return json_update, json_update#checkbox_group

    def add_to_json_proto_entry(self, json, json_key, selected, checkbox_group):#checkbox_group_choices
        selected = [selected] if not isinstance(selected, list) else selected
        for entry_number in selected:
            # json update
            json[entry_number][json_key] = checkbox_group
            help.verbose_print(f"entry_number:\t{entry_number}")
            help.verbose_print(f"json_key:\t{json_key}")
            help.verbose_print(f"checkbox_group:\t{checkbox_group}")
            help.verbose_print(f"json status [{entry_number}]:\t{json[entry_number][json_key]}")
            help.verbose_print(f"json:\t{json}")
        json_update = gr.update(value=json)
        # current checkbox group remove selected tags
        # checkbox_group = list(set(checkbox_group_choices)-set(checkbox_group))
        # help.verbose_print(f"checkbox_group:\t{checkbox_group}")
        # checkbox_group = gr.update(choices=checkbox_group, value=[])
        return json_update, json_update#checkbox_group

    def remove_json_proto_entry(self, json, selected):
        selected = [selected] if not isinstance(selected, list) else selected
        for entry_number in selected:
            # json update
            del json[entry_number]
        json_update = gr.update(value=json)
        # entry dropdown update
        dropdown = gr.update(choices=list(json.keys()), value=[])
        # current checkbox group clear
        # checkbox_group = gr.update(choices=[], value=[])
        return json_update, dropdown, json_update, dropdown#checkbox_group

    def create_all_setting_configs(self, json, settings_path):
        settings_copy = copy.deepcopy(self.settings_json)
        config_dir = os.path.join(self.settings_json["batch_folder"], "configs")
        path = settings_path
        temp = '\\' if help.is_windows() else '/'
        if ".json" in path:
            path = (path.split(temp))[:-1]
            path = f'{temp}'.join(path)
        if temp not in path:
            path = os.path.join(config_dir, path)
        entries = list(json.keys())
        for entry_key in entries:
            # edit copy
            # update batch_folder, required_tags, blacklist
            settings_copy["batch_folder"] = '_'.join(json[entry_key]["required"])
            settings_copy["required_tags"] = settings_copy["tag_sep"].join(json[entry_key]["required"])
            settings_copy["blacklist"] = settings_copy["tag_sep"].join(json[entry_key]["blacklist"])
            # check new file name
            number = 0
            new_path = os.path.join(path, f"settings_{number}.json")
            while os.path.exists(new_path):
                number += 1
                new_path = os.path.join(path, f"settings_{number}.json")
            # save with path
            help.update_JSON(settings_copy, new_path)

        # get file names & create dictionary mappings to batch file names
        batch_names, _ = self._load_preset_files()

        all_json_files_checkboxgroup = gr.update(choices=batch_names, value=[])
        return all_json_files_checkboxgroup

    def set_tag(self, tags, text):
        tags.append(text)
        return gr.update(choices=tags, value=tags), gr.update(value="")

    def convert_tags_to_entries(self, json, json_key, checkbox_group):
        next_entry_key = str((max([int(key) for key in json.keys()]) + 1) if (len(list(json.keys())) > 0) else 0)

        for i, tag in enumerate(checkbox_group):
            json[str(i+int(next_entry_key))] = {"required": {}, "blacklist": {}}
            json[str(i+int(next_entry_key))][json_key] = []
            # json update
            json[str(i+int(next_entry_key))][json_key].append(checkbox_group[i])
            help.verbose_print(f"entry_number:\t{str(i+int(next_entry_key))}")
            help.verbose_print(f"json_key:\t{json_key}")
            help.verbose_print(f"checkbox_group:\t{checkbox_group}")
            help.verbose_print(f"json status [{str(i+int(next_entry_key))}]:\t{json[str(i+int(next_entry_key))][json_key]}")
            help.verbose_print(f"json:\t{json}")
        json_update = gr.update(value=json)
        # current checkbox group remove selected tags
        # checkbox_group = list(set(checkbox_group_choices)-set(checkbox_group))
        # help.verbose_print(f"checkbox_group:\t{checkbox_group}")
        # checkbox_group = gr.update(choices=checkbox_group, value=[])

        dropdown = gr.update(choices=list(json.keys()), value=[])
        return json_update, json_update, dropdown, dropdown#checkbox_group

    def remove_json_files(self, selected):
        selected = self._normalize_selection(selected)
        if not selected:
            checkbox_update, dropdown_update, style_update = self.refresh_json_options()
            return (
                checkbox_update,
                dropdown_update,
                style_update,
                self._notice_update("No presets selected to remove."),
            )

        removed = 0
        for name in selected:
            path = self.batch_to_json_map.get(name)
            if not path:
                continue
            resolved = self._resolve_file_path(path)
            if os.path.isfile(resolved):
                os.remove(resolved)
                removed += 1
                if self.db_manager:
                    self.db_manager.remove_config_by_path(resolved)

        # get file names & create dictionary mappings to batch file names
        batch_names, _ = self._load_preset_files()

        all_json_files_checkboxgroup = gr.update(choices=batch_names, value=[])
        quick_json_select = gr.update(choices=batch_names, value=batch_names[0] if batch_names else None)
        style_update = gr.update(value=self._build_downloaded_css())

        if removed:
            message = f"Removed {removed} preset{'s' if removed != 1 else ''}."
        else:
            message = "Selected presets could not be removed."

        return (
            all_json_files_checkboxgroup,
            quick_json_select,
            style_update,
            self._notice_update(message),
        )










    def render_tab(self):
        with gr.Tab("Downloading Image/s"):
            config_save_var = gr.Button(value="Apply & Save Settings", variant='primary')
            with gr.Accordion("Edit Requirements for General Download INFO", visible=True, open=False):
                gr.Markdown(md_.general_config)
                with gr.Row():
                    with gr.Column(min_width=50, scale=2):
                        batch_folder = gr.Textbox(lines=1, label='Path to Batch Directory', value=self.settings_json["batch_folder"])
                    with gr.Column(min_width=50, scale=1):
                        batch_browse = gr.File(label='Browse', type='filepath', file_count='directory')
                    with gr.Column(min_width=50, scale=2):
                        resized_img_folder = gr.Textbox(lines=1, label='Path to Resized Images', value=self.settings_json["resized_img_folder"])
                    with gr.Column(min_width=50, scale=2):
                        custom_csv_path_textbox = gr.Textbox(lines=1, label='Path to Custom CSV',
                                                            value=self.settings_json["csv_custom_path"]
                                                            if "csv_custom_path" in self.settings_json else "")
                    with gr.Column(min_width=50, scale=1):
                        use_csv_custom_checkbox = gr.Checkbox(label='Use Custom CSV (Applies at start)',
                                                              value=bool(self.settings_json["use_csv_custom"])
                                                              if "use_csv_custom" in self.settings_json else False)
                with gr.Row():
                    with gr.Column(min_width=50, scale=1):
                        proxy_value = ""
                        if not "proxy_url" in self.settings_json:
                            self.settings_json["proxy_url"] = proxy_value
                        proxy_url_textbox = gr.Textbox(lines=1, label='(Optional Proxy URL)', value=self.settings_json["proxy_url"])
                    with gr.Column(min_width=50, scale=1):
                        tag_sep = gr.Textbox(lines=1, label='Tag Separator/Delimiter', value=self.settings_json["tag_sep"])
                    with gr.Column(min_width=50, scale=5):
                        tag_order_format = gr.Dropdown(multiselect=True, interactive=True, label='Tag ORDER',
                                                       choices=self.image_board.valid_categories,
                                                       value=self.image_board.tag_order
                                                       )
                with gr.Row():
                    with gr.Column(min_width=50, scale=1):
                        prepend_tags_textbox = gr.Textbox(lines=1, label='Enter Tag', value=None)
                    with gr.Column(min_width=50, scale=4):
                        prepend_tags_text = []
                        if len(self.settings_json["prepend_tags"]) > 0:
                            prepend_tags_text = self.settings_json["prepend_tags"].split(self.settings_json["tag_sep"])

                        prepend_tags = gr.Dropdown(multiselect=True, interactive=True, label='Prepend Tags',
                                                   choices=prepend_tags_text, value=prepend_tags_text)
                    with gr.Column(min_width=50, scale=1):
                        append_tags_textbox = gr.Textbox(lines=1, label='Enter Tag', value=None)
                    with gr.Column(min_width=50, scale=4):
                        append_tags_text = []
                        if len(self.settings_json["append_tags"]) > 0:
                            append_tags_text = self.settings_json["append_tags"].split(self.settings_json["tag_sep"])

                        append_tags = gr.Dropdown(multiselect=True, interactive=True, label='Append Tags',
                                                  choices=append_tags_text, value=append_tags_text)

                with gr.Row():
                    with gr.Column():
                        img_ext = gr.Dropdown(choices=self.img_extensions, label='Image Extension', value=self.settings_json["img_ext"])
                    with gr.Column():
                        method_tag_files = gr.Radio(choices=self.method_tag_files_opts, label='Resized Img Tag Handler', value=self.settings_json["method_tag_files"])
                    with gr.Column():
                        settings_path = gr.Textbox(lines=1, label='Path/Name to \"NEW\" JSON (REQUIRED)', value=self.config_name)
                    create_new_config_checkbox = gr.Checkbox(label="Create NEW Config", value=False)

                    batch_names, _ = self._load_preset_files()

                    default_val = batch_names[0] if batch_names else None
                    quick_json_select = gr.Dropdown(
                        choices=batch_names,
                        label='JSON Select',
                        value=default_val,
                        interactive=True,
                    )
                    json_browse = gr.File(label='Browse JSON', type='filepath', file_types=['.json'])

            with gr.Accordion("Edit Requirements for Image Stat/s", visible=True, open=False):
                gr.Markdown(md_.stats_config)
                with gr.Row():
                    min_score = gr.Slider(minimum=0, maximum=10000, step=1, label='Filter: Min Score', value=self.settings_json["min_score"])
                with gr.Row():
                    min_fav_count = gr.Slider(minimum=0, maximum=10000, step=1, label='Filter: Min Fav Count', value=self.settings_json["min_fav_count"])
                with gr.Row():
                    with gr.Column():
                        min_year = gr.Slider(minimum=2000, maximum=2050, step=1, label='Filter: Min Year', value=int(self.settings_json["min_year"]))
                        min_month = gr.Slider(minimum=1, maximum=12, step=1, label='Filter: Min Month',
                                         value=int(self.settings_json["min_month"]))
                        min_day = gr.Slider(minimum=1, maximum=31, step=1, label='Filter: Min Day',
                                         value=int(self.settings_json["min_day"]))
                with gr.Row():
                    min_area = gr.Slider(minimum=1, maximum=1000000, step=1, label='Filter: Min Area', value=self.settings_json["min_area"], info='ONLY images with LxW > this value will be downloaded')
                with gr.Row():
                    top_n = gr.Slider(minimum=0, maximum=1000000, step=1, label='Filter: Top N', value=self.settings_json["top_n"], info='ONLY the top N images will be downloaded')
                with gr.Row():
                    min_short_side = gr.Slider(minimum=1, maximum=100000, step=1, label='Resize Param: Min Short Side', value=self.settings_json["min_short_side"], info='ANY image\'s length or width that falls (ABOVE) this number will be resized')
            with gr.Accordion("Edit Requirements for Image Collection & Downloading Pre/Post-Processing", visible=True, open=False):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown(md_.collect)
                        collect_checkbox_group_var = gr.CheckboxGroup(choices=self.collect_checkboxes, label='Collect Checkboxes', value=help.grab_pre_selected(self.settings_json, self.collect_checkboxes))
                    with gr.Column():
                        gr.Markdown(md_.download)
                        download_checkbox_group_var = gr.CheckboxGroup(choices=self.download_checkboxes, label='Download Checkboxes', value=help.grab_pre_selected(self.settings_json, self.download_checkboxes))
                    with gr.Column():
                        gr.Markdown(md_.resize)
                        resize_checkbox_group_var = gr.CheckboxGroup(choices=self.resize_checkboxes, label='Resize Checkboxes', value=help.grab_pre_selected(self.settings_json, self.resize_checkboxes))
            ######################################## prototype config creation tool ########################################
            tag_json_fast_proto_settings = {}
            fast_proto_path = os.path.join(self.cwd, "fast_downloader_config")
            fast_proto_path_name = "fast_downloader.json"
            if not os.path.exists(fast_proto_path):
                os.mkdir(fast_proto_path)
                help.update_JSON(settings=tag_json_fast_proto_settings, temp_config_name=os.path.join(fast_proto_path, fast_proto_path_name))
            else:
                tag_json_fast_proto_settings = help.load_session_config(f_name=os.path.join(fast_proto_path, fast_proto_path_name))
            ################################################################################################################
            # fast_tag_proto_list = [sorted([(proto_file.split(temp)[-1]) for proto_file in glob.glob(os.path.join(fast_proto_path, f"*.json"))])]
            with gr.Accordion("Edit Requirements for Required Tags", visible=True, open=False):
                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            with gr.Column(min_width=50, scale=3):
                                required_tags_textbox = gr.Textbox(lines=1, label='Press Enter/Space to ADD tag/s', value="")
                            with gr.Column(min_width=50, scale=2):
                                tag_required_suggestion_dropdown = gr.Dropdown(label="Tag Suggestions", choices=[], interactive=True, allow_custom_value=True, elem_id="required_dropdown")
                        required_tags_group_var = gr.CheckboxGroup(choices=self.required_tags_list, label='ALL Required Tags',
                                                                   value=[])
                    with gr.Column():
                        file_all_tags_list_required = gr.File(file_count="multiple", file_types=["file"], label="Select ALL files with Tags to be parsed and Added")
                with gr.Row():
                    remove_button_required = gr.Button(value="Remove Checked Tags", variant='secondary')
                    parse_button_required = gr.Button(value="Parse/Add Tags", variant='secondary')
                with gr.Row():
                    with gr.Column(min_width=50, scale=5):
                        tag_json_fast_proto_required = gr.JSON(label="Fast Tag Downloader Prototype",
                                                           value=tag_json_fast_proto_settings, visible=True)
                    with gr.Column(min_width=50, scale=1):
                        # dropdown menu to select the entry to edit --- multi-select ----- use the options below to add tags to multiple entries at a time
                        entry_selection_required = gr.Dropdown(show_label=False, info="Entry Selection",
                                                               choices=list(tag_json_fast_proto_settings.keys()),
                                                               multiselect=True, interactive=True)
                        entry_load_button_required = gr.Button(value="Load Entry", variant='secondary')
                        # add new entry w/ incrementing (numbers) designating the new potential configs >>>> (defaults to that entry when creating it)
                        new_entry_button_required = gr.Button(value="New Entry", variant='secondary')
                        # reset json button
                        reset_entry_button_required = gr.Button(value="Reset Entry", variant='secondary')
                        # add tags to current entry button
                        add_to_entry_button_required = gr.Button(value="Add Tag/s to Entry", variant='secondary')
                        # remove tags to current entry button
                        remove_entry_button_required = gr.Button(value="Remove Entry", variant='secondary')

                        # split checkbox group into different entries
                        create_entries_from_checkboxgroup_button_required = gr.Button(value="Create Entry/s from Tag/s", variant='primary')

                        # split into setting_(NUMBER).json files
                        fast_create_json_button_required = gr.Button(value="Split to Setting Files", variant='primary')

            with gr.Accordion("Edit Requirements for Blacklist Tags", visible=True, open=False):
                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            with gr.Column(min_width=50, scale=3):
                                blacklist_tags_textbox = gr.Textbox(lines=1, label='Press Enter/Space to ADD tag/s', value="")
                            with gr.Column(min_width=50, scale=2):
                                tag_blacklist_suggestion_dropdown = gr.Dropdown(label="Tag Suggestions", choices=[], interactive=True, allow_custom_value=True, elem_id="blacklist_dropdown")
                        blacklist_tags_group_var = gr.CheckboxGroup(choices=self.blacklist_tags, label='ALL Blacklisted Tags',
                                                               value=[])
                    with gr.Column():
                        file_all_tags_list_blacklist = gr.File(file_count="multiple", file_types=["file"], label="Select ALL files with Tags to be parsed and Added")
                with gr.Row():
                    remove_button_blacklist = gr.Button(value="Remove Checked Tags", variant='secondary')
                    parse_button_blacklist = gr.Button(value="Parse/Add Tags", variant='secondary')
                with gr.Row():
                    with gr.Column(min_width=50, scale=5):
                        tag_json_fast_proto_blacklist = gr.JSON(label="Fast Tag Downloader Prototype",
                                                      value=tag_json_fast_proto_settings, visible=True)
                    with gr.Column(min_width=50, scale=1):
                        # dropdown menu to select the entry to edit --- multi-select ----- use the options below to add tags to multiple entries at a time
                        entry_selection_blacklist = gr.Dropdown(show_label=False, info="Entry Selection",
                                                                choices=list(tag_json_fast_proto_settings.keys()),
                                                                multiselect=True, interactive=True)
                        entry_load_button_blacklist = gr.Button(value="Load Entry", variant='secondary')
                        # add new entry w/ incrementing (numbers) designating the new potential configs >>>> (defaults to that entry when creating it)
                        new_entry_button_blacklist = gr.Button(value="New Entry", variant='secondary')
                        # reset json button
                        reset_entry_button_blacklist = gr.Button(value="Reset Entry", variant='secondary')
                        # add tags to current entry button
                        add_to_entry_button_blacklist = gr.Button(value="Add Tag/s to Entry", variant='secondary')
                        # remove tags to current entry button
                        remove_entry_button_blacklist = gr.Button(value="Remove Tag/s to Entry", variant='secondary')

                        # split checkbox group into different entries
                        create_entries_from_checkboxgroup_button_blacklist = gr.Button(value="Create Entry/s from Tag/s", variant='primary')

                        # split into setting_(NUMBER).json files
                        fast_create_json_button_blacklist = gr.Button(value="Split to Setting Files", variant='primary') # info="Converts json file to auto create setting_(NUMBER).json files"

            with gr.Accordion("Edit Requirements for Advanced Configuration", visible=True, open=False):
                gr.Markdown(md_.add_comps_config)
                with gr.Row():
                    with gr.Column():
                        skip_posts_file = gr.Textbox(lines=1, label='Path to file w/ multiple id/md5 to skip',
                                                 value=self.settings_json["skip_posts_file"])
                        skip_posts_type = gr.Radio(choices=["id","md5"], label='id/md5 skip', value=self.settings_json["skip_posts_type"])
                    with gr.Column():
                        save_searched_list_path = gr.Textbox(lines=1, label='id/md5 list to file path', value=self.settings_json["save_searched_list_path"])
                        save_searched_list_type = gr.Radio(choices=["id", "md5", "None"], label='Save id/md5 list to file', value=self.settings_json["save_searched_list_type"])
                with gr.Row():
                    with gr.Column():
                        apply_filter_to_listed_posts = gr.Checkbox(label='Apply Filters to Collected Posts',
                                                       value=self.settings_json["apply_filter_to_listed_posts"])
                        collect_from_listed_posts_type = gr.Radio(choices=["id", "md5"], label='id/md5 collect',
                                                              value=self.settings_json["collect_from_listed_posts_type"])
                        collect_from_listed_posts_file = gr.Textbox(lines=1, label='Path to file w/ multiple id/md5 to collect',
                                                                value=self.settings_json["collect_from_listed_posts_file"])
                with gr.Row():
                    downloaded_posts_folder = gr.Textbox(lines=1, label='Path for downloaded posts',
                                                     value=self.settings_json["downloaded_posts_folder"])
                    png_folder = gr.Textbox(lines=1, label='Path for png data', value=self.settings_json["png_folder"])
                    jpg_folder = gr.Textbox(lines=1, label='Path for jpg data', value=self.settings_json["jpg_folder"])
                    webm_folder = gr.Textbox(lines=1, label='Path for webm data', value=self.settings_json["webm_folder"])
                    gif_folder = gr.Textbox(lines=1, label='Path for gif data', value=self.settings_json["gif_folder"])
                    swf_folder = gr.Textbox(lines=1, label='Path for swf data', value=self.settings_json["swf_folder"])
                with gr.Row():
                    download_remove_tag_file_button = gr.Button(value="(Optional) Download Negative Tags File", variant='secondary')
                with gr.Row():
                    reference_model_tags_file = gr.Textbox(lines=1, label='Path to model tags file')
                    gen_tags_list_button = gr.Button(value="Generate Tag/s List", variant='secondary')
                    gen_tags_diff_list_button = gr.Button(value="Generate Tag/s Diff List", variant='secondary')
                with gr.Row():
                    save_filename_type = gr.Radio(choices=["id","md5"], label='Select Filename Type', value=self.settings_json["save_filename_type"])
                    tag_count_list_folder = gr.Textbox(lines=1, label='Path to tag count file',
                                                       value=self.settings_json["tag_count_list_folder"])
            with gr.Accordion("Edit Requirements for Run Configuration", visible=True, open=False):
                gr.Markdown(md_.run)
                with gr.Row():
                    with gr.Column():
                        basefolder = gr.Textbox(lines=1, label='Root Output Dir Path', value=self.cwd)
                        numcpu = gr.Slider(minimum=1, maximum=mp.cpu_count(), step=1, label='Worker Threads', value=int(mp.cpu_count()/2))
                with gr.Row():
                    with gr.Column():
                       phaseperbatch = gr.Checkbox(label='Completes all phases per batch', value=True)
                    with gr.Column():
                       keepdb = gr.Checkbox(label='Keep e6 db data', value=False)
                    with gr.Column():
                        cachepostsdb = gr.Checkbox(label='cache e6 posts file when multiple batches', value=False)
                with gr.Row():
                    with gr.Column():
                        override_download_delay_checkbox = gr.Checkbox(
                            label='Override Download Delay & Retries',
                            value=self.settings_json.get("override_download_delay", False)
                        )
                    with gr.Column():
                        custom_download_delay_slider = gr.Slider(
                            minimum=0, maximum=60, step=1,
                            label='Download Delay (seconds)',
                            value=self.settings_json.get("custom_download_delay", 1)
                        )
                    with gr.Column():
                        custom_retry_attempts_slider = gr.Slider(
                            minimum=1, maximum=10, step=1,
                            label='Retry Attempts',
                            value=self.settings_json.get("custom_retry_attempts", 3)
                        )
                with gr.Row():
                    postscsv = gr.Textbox(lines=1, label='Path to e6 posts csv', value="")
                    tagscsv = gr.Textbox(lines=1, label='Path to e6 tags csv', value="")
                    postsparquet = gr.Textbox(lines=1, label='Path to e6 posts parquet', value="")
                    tagsparquet = gr.Textbox(lines=1, label='Path to e6 tags parquet', value="")
                with gr.Row():
                    images_full_change_dict_textbox = gr.Textbox(lines=1, label='Path to Image Full Change Log JSON (Optional)',
                                                             value=os.path.join(self.auto_config_path, f"auto_complete_{self.settings_json['batch_folder']}.json"))
                    images_full_change_dict_run_button = gr.Button(value="(POST-PROCESSING only) Apply Auto-Config Update Changes", variant='secondary')
                with gr.Row():
                    query_file = gr.File(label='Queries File', file_types=['.txt'])
                    import_queries_btn = gr.Button(value='Import Queries', variant='secondary')
                    refresh_json_btn = gr.Button(value='Refresh Configs', variant='secondary')
            with gr.Row():
                run_button = gr.Button(value="Run", variant='primary')
            with gr.Row():
                progress_bar_textbox_collect = gr.Textbox(interactive=False, visible=False)
            with gr.Row():
                progress_bar_textbox_download = gr.Textbox(interactive=False, visible=False)
            with gr.Row():
                progress_bar_textbox_resize = gr.Textbox(interactive=False, visible=False)
            preset_names, _ = self._load_preset_files()
            with gr.Accordion("Batch Run", visible=True, open=False):
                with gr.Row():
                    all_json_files_checkboxgroup = gr.CheckboxGroup(choices=preset_names,
                                                                label='Select to Run', value=[],
                                                                elem_id="preset-checkboxgroup")
                preset_status_style = gr.HTML(
                    value=self._build_downloaded_css(),
                    show_label=False,
                )
                with gr.Row():
                    preset_selection_action_dropdown = gr.Dropdown(
                        choices=["Select All", "Deselect All", "Invert Selection"],
                        label='Preset Selection Actions',
                        value=None,
                        interactive=True,
                    )
                with gr.Row():
                    remove_json_batch_buttton = gr.Button(value="Batch Remove JSON", variant='secondary')
                    run_button_batch = gr.Button(value="Batch Run", variant='primary')
                with gr.Row():
                    preset_folder_textbox = gr.Textbox(
                        lines=1,
                        label='Preset Folder',
                        value=self.preset_folder,
                    )
                    preset_folder_browser = gr.File(label='Browse Preset Folder', type='filepath', file_count='directory')
                with gr.Row():
                    apply_preset_folder_button = gr.Button(value="Use Preset Folder", variant='secondary')
                    refresh_presets_button = gr.Button(value="Refresh Presets", variant='secondary')
                with gr.Row():
                    archive_presets_button = gr.Button(value="Archive Selected Presets", variant='secondary')
                    delete_presets_button = gr.Button(value="Delete Selected Presets", variant='secondary')
                with gr.Row():
                    preset_folder_notice = gr.Markdown(self._build_preset_folder_notice())
                with gr.Row():
                    progress_run_batch = gr.Textbox(interactive=False, visible=False)

        self.config_save_var = config_save_var
        self.batch_folder = batch_folder
        self.batch_browse = batch_browse
        self.resized_img_folder = resized_img_folder
        self.custom_csv_path_textbox = custom_csv_path_textbox
        self.use_csv_custom_checkbox = use_csv_custom_checkbox
        self.proxy_url_textbox = proxy_url_textbox
        self.tag_sep = tag_sep
        self.tag_order_format = tag_order_format
        self.prepend_tags = prepend_tags
        self.append_tags = append_tags
        self.img_ext = img_ext
        self.method_tag_files = method_tag_files
        self.settings_path = settings_path
        self.create_new_config_checkbox = create_new_config_checkbox
        self.quick_json_select = quick_json_select
        self.json_browse = json_browse
        self.min_score = min_score
        self.min_fav_count = min_fav_count
        self.min_year = min_year
        self.min_month = min_month
        self.min_day = min_day
        self.min_area = min_area
        self.top_n = top_n
        self.min_short_side = min_short_side
        self.collect_checkbox_group_var = collect_checkbox_group_var
        self.download_checkbox_group_var = download_checkbox_group_var
        self.resize_checkbox_group_var = resize_checkbox_group_var
        self.required_tags_textbox = required_tags_textbox
        self.tag_required_suggestion_dropdown = tag_required_suggestion_dropdown
        self.required_tags_group_var = required_tags_group_var
        self.file_all_tags_list_required = file_all_tags_list_required
        self.remove_button_required = remove_button_required
        self.parse_button_required = parse_button_required
        self.blacklist_tags_textbox = blacklist_tags_textbox
        self.tag_blacklist_suggestion_dropdown = tag_blacklist_suggestion_dropdown
        self.blacklist_tags_group_var = blacklist_tags_group_var
        self.file_all_tags_list_blacklist = file_all_tags_list_blacklist
        self.remove_button_blacklist = remove_button_blacklist
        self.parse_button_blacklist = parse_button_blacklist
        self.skip_posts_file = skip_posts_file
        self.skip_posts_type = skip_posts_type
        self.save_searched_list_path = save_searched_list_path
        self.save_searched_list_type = save_searched_list_type
        self.apply_filter_to_listed_posts = apply_filter_to_listed_posts
        self.collect_from_listed_posts_type = collect_from_listed_posts_type
        self.collect_from_listed_posts_file = collect_from_listed_posts_file
        self.downloaded_posts_folder = downloaded_posts_folder
        self.png_folder = png_folder
        self.jpg_folder = jpg_folder
        self.webm_folder = webm_folder
        self.gif_folder = gif_folder
        self.swf_folder = swf_folder
        self.download_remove_tag_file_button = download_remove_tag_file_button
        self.reference_model_tags_file = reference_model_tags_file
        self.gen_tags_list_button = gen_tags_list_button
        self.gen_tags_diff_list_button = gen_tags_diff_list_button
        self.save_filename_type = save_filename_type
        self.tag_count_list_folder = tag_count_list_folder
        self.basefolder = basefolder
        self.numcpu = numcpu
        self.phaseperbatch = phaseperbatch
        self.keepdb = keepdb
        self.cachepostsdb = cachepostsdb
        self.postscsv = postscsv
        self.tagscsv = tagscsv
        self.postsparquet = postsparquet
        self.tagsparquet = tagsparquet
        self.images_full_change_dict_textbox = images_full_change_dict_textbox
        self.images_full_change_dict_run_button = images_full_change_dict_run_button
        self.query_file = query_file
        self.import_queries_btn = import_queries_btn
        self.refresh_json_btn = refresh_json_btn
        self.run_button = run_button
        self.progress_bar_textbox_collect = progress_bar_textbox_collect
        self.progress_bar_textbox_download = progress_bar_textbox_download
        self.progress_bar_textbox_resize = progress_bar_textbox_resize
        self.all_json_files_checkboxgroup = all_json_files_checkboxgroup
        self.preset_selection_action_dropdown = preset_selection_action_dropdown
        self.run_button_batch = run_button_batch
        self.progress_run_batch = progress_run_batch
        self.tag_json_fast_proto_required = tag_json_fast_proto_required
        self.entry_selection_required = entry_selection_required
        self.new_entry_button_required = new_entry_button_required
        self.reset_entry_button_required = reset_entry_button_required
        self.add_to_entry_button_required = add_to_entry_button_required
        self.remove_entry_button_required = remove_entry_button_required
        self.fast_create_json_button_required = fast_create_json_button_required
        self.tag_json_fast_proto_blacklist = tag_json_fast_proto_blacklist
        self.entry_selection_blacklist = entry_selection_blacklist
        self.new_entry_button_blacklist = new_entry_button_blacklist
        self.reset_entry_button_blacklist = reset_entry_button_blacklist
        self.add_to_entry_button_blacklist = add_to_entry_button_blacklist
        self.remove_entry_button_blacklist = remove_entry_button_blacklist
        self.fast_create_json_button_blacklist = fast_create_json_button_blacklist
        self.entry_load_button_required = entry_load_button_required
        self.entry_load_button_blacklist = entry_load_button_blacklist
        self.prepend_tags_textbox = prepend_tags_textbox
        self.append_tags_textbox = append_tags_textbox
        self.create_entries_from_checkboxgroup_button_required = create_entries_from_checkboxgroup_button_required
        self.create_entries_from_checkboxgroup_button_blacklist = create_entries_from_checkboxgroup_button_blacklist
        self.remove_json_batch_buttton = remove_json_batch_buttton
        self.preset_folder_textbox = preset_folder_textbox
        self.preset_folder_browser = preset_folder_browser
        self.apply_preset_folder_button = apply_preset_folder_button
        self.refresh_presets_button = refresh_presets_button
        self.archive_presets_button = archive_presets_button
        self.delete_presets_button = delete_presets_button
        self.preset_folder_notice = preset_folder_notice
        self.preset_status_style = preset_status_style
        self.override_download_delay_checkbox = override_download_delay_checkbox
        self.custom_download_delay_slider = custom_download_delay_slider
        self.custom_retry_attempts_slider = custom_retry_attempts_slider

        return [
                self.config_save_var,
                self.batch_folder,
                self.batch_browse,
                self.resized_img_folder,
                self.custom_csv_path_textbox,
                self.use_csv_custom_checkbox,
                self.proxy_url_textbox,
                self.tag_sep,
                self.tag_order_format,
                self.prepend_tags,
                self.append_tags,
                self.img_ext,
                self.method_tag_files,
                self.settings_path,
                self.create_new_config_checkbox,
                self.quick_json_select,
                self.json_browse,
                self.min_score,
                self.min_fav_count,
                self.min_year,
                self.min_month,
                self.min_day,
                self.min_area,
                self.top_n,
                self.min_short_side,
                self.collect_checkbox_group_var,
                self.download_checkbox_group_var,
                self.resize_checkbox_group_var,
                self.required_tags_textbox,
                self.tag_required_suggestion_dropdown,
                self.required_tags_group_var,
                self.file_all_tags_list_required,
                self.remove_button_required,
                self.parse_button_required,
                self.blacklist_tags_textbox,
                self.tag_blacklist_suggestion_dropdown,
                self.blacklist_tags_group_var,
                self.file_all_tags_list_blacklist,
                self.remove_button_blacklist,
                self.parse_button_blacklist,
                self.skip_posts_file,
                self.skip_posts_type,
                self.save_searched_list_path,
                self.save_searched_list_type,
                self.apply_filter_to_listed_posts,
                self.collect_from_listed_posts_type,
                self.collect_from_listed_posts_file,
                self.downloaded_posts_folder,
                self.png_folder,
                self.jpg_folder,
                self.webm_folder,
                self.gif_folder,
                self.swf_folder,
                self.download_remove_tag_file_button,
                self.reference_model_tags_file,
                self.gen_tags_list_button,
                self.gen_tags_diff_list_button,
                self.save_filename_type,
                self.tag_count_list_folder,
                self.basefolder,
                self.numcpu,
                self.phaseperbatch,
                self.keepdb,
                self.cachepostsdb,
                self.postscsv,
                self.tagscsv,
                self.postsparquet,
                self.tagsparquet,
                self.images_full_change_dict_textbox,
                self.images_full_change_dict_run_button,
                self.query_file,
                self.import_queries_btn,
                self.refresh_json_btn,
                self.run_button,
                self.progress_bar_textbox_collect,
                self.progress_bar_textbox_download,
                self.progress_bar_textbox_resize,
                self.all_json_files_checkboxgroup,
                self.preset_selection_action_dropdown,
                self.run_button_batch,
                self.progress_run_batch,
                self.tag_json_fast_proto_required,
                self.entry_selection_required,
                self.new_entry_button_required,
                self.reset_entry_button_required,
                self.add_to_entry_button_required,
                self.remove_entry_button_required,
                self.fast_create_json_button_required,
                self.tag_json_fast_proto_blacklist,
                self.entry_selection_blacklist,
                self.new_entry_button_blacklist,
                self.reset_entry_button_blacklist,
                self.add_to_entry_button_blacklist,
                self.remove_entry_button_blacklist,
                self.fast_create_json_button_blacklist,
                self.entry_load_button_required,
                self.entry_load_button_blacklist,
                self.prepend_tags_textbox,
                self.append_tags_textbox,
                self.create_entries_from_checkboxgroup_button_required,
                self.create_entries_from_checkboxgroup_button_blacklist,
                self.remove_json_batch_buttton,
                self.preset_folder_textbox,
                self.preset_folder_browser,
                self.apply_preset_folder_button,
                self.refresh_presets_button,
                self.archive_presets_button,
                self.delete_presets_button,
                self.preset_folder_notice,
                self.override_download_delay_checkbox,
                self.custom_download_delay_slider,
                self.custom_retry_attempts_slider
                ]

    def get_event_listeners(self):
        self.import_queries_btn.click(
            fn=self.import_queries,
            inputs=[self.query_file],
            outputs=[
                self.all_json_files_checkboxgroup,
                self.quick_json_select,
                self.preset_status_style,
            ]
        )
        self.refresh_json_btn.click(
            fn=self.refresh_json_options,
            inputs=None,
            outputs=[
                self.all_json_files_checkboxgroup,
                self.quick_json_select,
                self.preset_status_style,
            ]
        ).then(
            fn=self.update_preset_notice,
            inputs=None,
            outputs=[self.preset_folder_notice]
        )
        self.remove_json_batch_buttton.click(
            fn=self.remove_json_files,
            inputs=[self.all_json_files_checkboxgroup],
            outputs=[
                self.all_json_files_checkboxgroup,
                self.quick_json_select,
                self.preset_status_style,
                self.preset_folder_notice,
            ],
        )
        self.preset_selection_action_dropdown.change(
            fn=self.apply_preset_selection_action,
            inputs=[self.preset_selection_action_dropdown, self.all_json_files_checkboxgroup],
            outputs=[
                self.all_json_files_checkboxgroup,
                self.preset_selection_action_dropdown,
                self.preset_status_style,
            ],
        )
        self.preset_folder_browser.change(
            fn=self.update_preset_folder_textbox,
            inputs=[self.preset_folder_browser],
            outputs=[self.preset_folder_textbox]
        )
        self.apply_preset_folder_button.click(
            fn=self.apply_preset_folder_selection,
            inputs=[self.preset_folder_textbox],
            outputs=[
                self.preset_folder_textbox,
                self.all_json_files_checkboxgroup,
                self.quick_json_select,
                self.preset_status_style,
                self.preset_folder_notice,
            ],
        )
        self.refresh_presets_button.click(
            fn=self.refresh_presets_and_notice,
            inputs=None,
            outputs=[
                self.all_json_files_checkboxgroup,
                self.quick_json_select,
                self.preset_status_style,
                self.preset_folder_notice,
            ],
        )
        self.archive_presets_button.click(
            fn=self.archive_selected_presets,
            inputs=[self.all_json_files_checkboxgroup],
            outputs=[
                self.all_json_files_checkboxgroup,
                self.quick_json_select,
                self.preset_status_style,
                self.preset_folder_notice,
            ],
        )
        self.delete_presets_button.click(
            fn=self.delete_selected_presets,
            inputs=[self.all_json_files_checkboxgroup],
            outputs=[
                self.all_json_files_checkboxgroup,
                self.quick_json_select,
                self.preset_status_style,
                self.preset_folder_notice,
            ],
        )

        self.create_entries_from_checkboxgroup_button_required.click(
            fn=self.convert_tags_to_entries,
            inputs=[self.tag_json_fast_proto_required, gr.State("required"), self.required_tags_group_var],
            outputs=[self.tag_json_fast_proto_required, self.tag_json_fast_proto_blacklist,
                     self.entry_selection_required, self.entry_selection_blacklist]
        )
        self.create_entries_from_checkboxgroup_button_blacklist.click(
            fn=self.convert_tags_to_entries,
            inputs=[self.tag_json_fast_proto_blacklist, gr.State("blacklist"), self.blacklist_tags_group_var],
            outputs=[self.tag_json_fast_proto_required, self.tag_json_fast_proto_blacklist,
                     self.entry_selection_required, self.entry_selection_blacklist]
        )
        self.prepend_tags_textbox.submit(
            fn=self.set_tag,
            inputs=[self.prepend_tags, self.prepend_tags_textbox],
            outputs=[self.prepend_tags, self.prepend_tags_textbox]
        )
        self.append_tags_textbox.submit(
            fn=self.set_tag,
            inputs=[self.append_tags, self.append_tags_textbox],
            outputs=[self.append_tags, self.prepend_tags_textbox]
        )
        self.entry_load_button_required.click(
            fn=self.load_single_tag_json,
            inputs=[self.entry_selection_required, self.required_tags_group_var, self.tag_json_fast_proto_required,
                    gr.State("required")],
            outputs=[self.required_tags_group_var]
        )
        self.new_entry_button_required.click(
            fn=self.new_json_proto_entry,
            inputs=[self.tag_json_fast_proto_required, gr.State("required")],
            outputs=[
                self.tag_json_fast_proto_required,
                self.entry_selection_required,
                # self.required_tags_group_var,
                self.tag_json_fast_proto_blacklist,
                self.entry_selection_blacklist
            ]
        )
        self.reset_entry_button_required.click(
            fn=self.reset_json_proto_entry,
            inputs=[self.tag_json_fast_proto_required, gr.State("required"), self.entry_selection_required],
            outputs=[
                self.tag_json_fast_proto_required,
                # self.required_tags_group_var,
                self.tag_json_fast_proto_blacklist
            ]
        )
        self.add_to_entry_button_required.click(
            fn=self.add_to_json_proto_entry,
            inputs=[
                self.tag_json_fast_proto_required,
                gr.State("required"),
                self.entry_selection_required,
                self.required_tags_group_var
                # gr.State(self.required_tags_group_var.choices)
            ],
            outputs=[
                self.tag_json_fast_proto_required,
                # self.required_tags_group_var,
                self.tag_json_fast_proto_blacklist
            ]
        )
        self.remove_entry_button_required.click(
            fn=self.remove_json_proto_entry,
            inputs=[self.tag_json_fast_proto_required, self.entry_selection_required],
            outputs=[
                self.tag_json_fast_proto_required,
                self.entry_selection_required,
                # self.required_tags_group_var,
                self.tag_json_fast_proto_blacklist,
                self.entry_selection_blacklist
            ]
        )
        self.fast_create_json_button_required.click(
            fn=self.create_all_setting_configs,
            inputs=[self.tag_json_fast_proto_required, self.settings_path],
            outputs=[self.all_json_files_checkboxgroup]
        )
        self.entry_load_button_blacklist.click(
            fn=self.load_single_tag_json,
            inputs=[self.entry_selection_blacklist, self.blacklist_tags_group_var, self.tag_json_fast_proto_blacklist,
                    gr.State("blacklist")],
            outputs=[self.blacklist_tags_group_var]
        )
        self.new_entry_button_blacklist.click(
            fn=self.new_json_proto_entry,
            inputs=[self.tag_json_fast_proto_blacklist, gr.State("blacklist")],
            outputs=[
                self.tag_json_fast_proto_blacklist,
                self.entry_selection_blacklist,
                # self.blacklist_tags_group_var,
                self.tag_json_fast_proto_required,
                self.entry_selection_required
            ]
        )
        self.reset_entry_button_blacklist.click(
            fn=self.reset_json_proto_entry,
            inputs=[self.tag_json_fast_proto_blacklist, gr.State("blacklist"), self.entry_selection_blacklist],
            outputs=[
                self.tag_json_fast_proto_blacklist,
                # self.blacklist_tags_group_var,
                self.tag_json_fast_proto_required
            ]
        )
        self.add_to_entry_button_blacklist.click(
            fn=self.add_to_json_proto_entry,
            inputs=[
                self.tag_json_fast_proto_blacklist,
                gr.State("blacklist"),
                self.entry_selection_blacklist,
                self.blacklist_tags_group_var
                # gr.State(self.blacklist_tags_group_var.choices)
            ],
            outputs=[
                self.tag_json_fast_proto_blacklist,
                # self.blacklist_tags_group_var,
                self.tag_json_fast_proto_required
            ]
        )
        self.remove_entry_button_blacklist.click(
            fn=self.remove_json_proto_entry,
            inputs=[self.tag_json_fast_proto_blacklist, self.entry_selection_blacklist],
            outputs=[
                self.tag_json_fast_proto_blacklist,
                self.entry_selection_blacklist,
                # self.blacklist_tags_group_var,
                self.tag_json_fast_proto_required,
                self.entry_selection_required
            ]
        )
        self.fast_create_json_button_blacklist.click(
            fn=self.create_all_setting_configs,
            inputs=[self.tag_json_fast_proto_blacklist, self.settings_path],
            outputs=[self.all_json_files_checkboxgroup]
        )
        self.quick_json_select.select(
            fn=self.change_config,
            inputs=[self.settings_path],
            outputs=[self.batch_folder, self.resized_img_folder, self.tag_sep, self.tag_order_format,
                     self.prepend_tags, self.append_tags, self.img_ext, self.method_tag_files, self.min_score,
                     self.min_fav_count, self.min_year, self.min_month, self.min_day, self.min_area, self.top_n,
                     self.min_short_side, self.collect_checkbox_group_var, self.download_checkbox_group_var,
                     self.resize_checkbox_group_var, self.required_tags_group_var, self.blacklist_tags_group_var,
                     self.skip_posts_file, self.skip_posts_type, self.collect_from_listed_posts_file,
                     self.collect_from_listed_posts_type, self.apply_filter_to_listed_posts,
                     self.save_searched_list_type, self.save_searched_list_path, self.downloaded_posts_folder,
                     self.png_folder, self.jpg_folder, self.webm_folder, self.gif_folder, self.swf_folder,
                     self.save_filename_type, self.gallery_tab_manager.remove_tags_list, self.gallery_tab_manager.replace_tags_list,
                     self.tag_count_list_folder, self.all_json_files_checkboxgroup, self.quick_json_select,
                     self.proxy_url_textbox, self.settings_path,  self.custom_csv_path_textbox,
                     self.use_csv_custom_checkbox, self.override_download_delay_checkbox, self.custom_download_delay_slider,
                     self.custom_retry_attempts_slider]
        ).then(
            fn=self.check_to_reload_auto_complete_config,
            inputs=[],
            outputs=[]
        ).then(
            fn=self.gallery_tab_manager.reset_gallery_manager,
            inputs=[],
            outputs=[
                self.gallery_tab_manager.download_folder_type,
                self.gallery_tab_manager.img_id_textbox,
                self.gallery_tab_manager.tag_search_textbox,
                self.gallery_tab_manager.tag_search_suggestion_dropdown,
                self.gallery_tab_manager.apply_to_all_type_select_checkboxgroup,
                self.gallery_tab_manager.select_multiple_images_checkbox,
                self.gallery_tab_manager.select_between_images_checkbox,
                self.gallery_tab_manager.apply_datetime_sort_ckbx,
                self.gallery_tab_manager.apply_datetime_choice_menu,
                self.gallery_tab_manager.send_img_from_gallery_dropdown,
                self.gallery_tab_manager.batch_send_from_gallery_checkbox,
                self.gallery_tab_manager.tag_add_textbox,
                self.gallery_tab_manager.tag_add_suggestion_dropdown,
                self.gallery_tab_manager.category_filter_gallery_dropdown,
                self.gallery_tab_manager.tag_effects_gallery_dropdown,
                self.gallery_tab_manager.img_artist_tag_checkbox_group,
                self.gallery_tab_manager.img_character_tag_checkbox_group,
                self.gallery_tab_manager.img_species_tag_checkbox_group,
                self.gallery_tab_manager.img_general_tag_checkbox_group,
                self.gallery_tab_manager.img_meta_tag_checkbox_group,
                self.gallery_tab_manager.img_rating_tag_checkbox_group,
                self.gallery_tab_manager.gallery_comp
            ]
        )
        self.config_save_var.click(
            fn=self.config_save_button,
            inputs=[
                self.batch_folder,
                self.resized_img_folder,
                self.tag_sep,
                self.tag_order_format,
                self.prepend_tags,
                self.append_tags,
                self.img_ext,
                self.method_tag_files,
                self.min_score,
                self.min_fav_count,
                self.min_area,
                self.top_n,
                self.min_short_side,
                self.skip_posts_file,
                self.skip_posts_type,
                self.collect_from_listed_posts_file,
                self.collect_from_listed_posts_type,
                self.apply_filter_to_listed_posts,
                self.save_searched_list_type,
                self.save_searched_list_path,
                self.downloaded_posts_folder,
                self.png_folder,
                self.jpg_folder,
                self.webm_folder,
                self.gif_folder,
                self.swf_folder,
                self.save_filename_type,
                self.gallery_tab_manager.remove_tags_list,
                self.gallery_tab_manager.replace_tags_list,
                self.tag_count_list_folder,
                self.min_month,
                self.min_day,
                self.min_year,
                self.collect_checkbox_group_var,
                self.download_checkbox_group_var,
                self.resize_checkbox_group_var,
                self.create_new_config_checkbox,
                self.settings_path,
                self.proxy_url_textbox,
                self.custom_csv_path_textbox,
                self.use_csv_custom_checkbox,
                self.override_download_delay_checkbox,
                self.custom_download_delay_slider,
                self.custom_retry_attempts_slider
            ],
            outputs=[
                self.all_json_files_checkboxgroup,
                self.quick_json_select,
                self.preset_status_style,
            ]
        ).then(
            fn=self.check_to_reload_auto_complete_config,
            inputs=[],
            outputs=[]
        )
        self.run_button.click(
            fn=self.config_save_button,
            inputs=[
                self.batch_folder,
                self.resized_img_folder,
                self.tag_sep,
                self.tag_order_format,
                self.prepend_tags,
                self.append_tags,
                self.img_ext,
                self.method_tag_files,
                self.min_score,
                self.min_fav_count,
                self.min_area,
                self.top_n,
                self.min_short_side,
                self.skip_posts_file,
                self.skip_posts_type,
                self.collect_from_listed_posts_file,
                self.collect_from_listed_posts_type,
                self.apply_filter_to_listed_posts,
                self.save_searched_list_type,
                self.save_searched_list_path,
                self.downloaded_posts_folder,
                self.png_folder,
                self.jpg_folder,
                self.webm_folder,
                self.gif_folder,
                self.swf_folder,
                self.save_filename_type,
                self.gallery_tab_manager.remove_tags_list,
                self.gallery_tab_manager.replace_tags_list,
                self.tag_count_list_folder,
                self.min_month,
                self.min_day,
                self.min_year,
                self.collect_checkbox_group_var,
                self.download_checkbox_group_var,
                self.resize_checkbox_group_var,
                self.create_new_config_checkbox,
                self.settings_path,
                self.proxy_url_textbox,
                self.custom_csv_path_textbox,
                self.use_csv_custom_checkbox,
                self.override_download_delay_checkbox,
                self.custom_download_delay_slider,
                self.custom_retry_attempts_slider
            ],
            outputs=[
                self.all_json_files_checkboxgroup,
                self.quick_json_select,
                self.preset_status_style,
            ]
        ).then(
            fn=self.run_script,
            inputs=[self.basefolder,self.settings_path,self.numcpu,self.phaseperbatch,self.keepdb,self.cachepostsdb,self.postscsv,self.tagscsv,self.postsparquet,
                    self.tagsparquet],
            outputs=[]).then(
            fn=self.make_run_visible,
            inputs=[],
            outputs=[self.progress_bar_textbox_collect]).then(
            fn=self.data_collect,
            inputs=[],
            outputs=[self.progress_bar_textbox_collect]).then(
            fn=self.make_run_visible,
            inputs=[],
            outputs=[self.progress_bar_textbox_download]).then(
            fn=self.data_download,
            inputs=[],
            outputs=[self.progress_bar_textbox_download]).then(
            fn=self.make_run_visible,
            inputs=[],
            outputs=[self.progress_bar_textbox_resize]).then(
            fn=self.data_resize,
            inputs=[self.resize_checkbox_group_var],
            outputs=[self.progress_bar_textbox_resize]).then(
            fn=self.end_connection,
            inputs=[],
            outputs=[]).then(
            fn=self.gallery_tab_manager.reset_gallery_manager,
            inputs=[],
            outputs=[
                self.gallery_tab_manager.download_folder_type,
                self.gallery_tab_manager.img_id_textbox,
                self.gallery_tab_manager.tag_search_textbox,
                self.gallery_tab_manager.tag_search_suggestion_dropdown,
                self.gallery_tab_manager.apply_to_all_type_select_checkboxgroup,
                self.gallery_tab_manager.select_multiple_images_checkbox,
                self.gallery_tab_manager.select_between_images_checkbox,
                self.gallery_tab_manager.apply_datetime_sort_ckbx,
                self.gallery_tab_manager.apply_datetime_choice_menu,
                self.gallery_tab_manager.send_img_from_gallery_dropdown,
                self.gallery_tab_manager.batch_send_from_gallery_checkbox,
                self.gallery_tab_manager.tag_add_textbox,
                self.gallery_tab_manager.tag_add_suggestion_dropdown,
                self.gallery_tab_manager.category_filter_gallery_dropdown,
                self.gallery_tab_manager.tag_effects_gallery_dropdown,
                self.gallery_tab_manager.img_artist_tag_checkbox_group,
                self.gallery_tab_manager.img_character_tag_checkbox_group,
                self.gallery_tab_manager.img_species_tag_checkbox_group,
                self.gallery_tab_manager.img_general_tag_checkbox_group,
                self.gallery_tab_manager.img_meta_tag_checkbox_group,
                self.gallery_tab_manager.img_rating_tag_checkbox_group,
                self.gallery_tab_manager.gallery_comp
            ]
        ).then(
            fn=self.refresh_json_options,
            inputs=[],
            outputs=[
                self.all_json_files_checkboxgroup,
                self.quick_json_select,
                self.preset_status_style,
            ]
        )
        self.run_button_batch.click(
            fn=self.make_run_visible,
            inputs=[],
            outputs=[self.progress_run_batch]).then(
            fn=self.run_script_batch,
            inputs=[self.basefolder,self.settings_path,self.numcpu,self.phaseperbatch,self.keepdb,self.cachepostsdb,self.postscsv,self.tagscsv,self.postsparquet,
                    self.tagsparquet,self.all_json_files_checkboxgroup,self.images_full_change_dict_textbox],
            outputs=[self.progress_run_batch]).then(
            fn=self.change_config_batch_run,
            inputs=[self.all_json_files_checkboxgroup, self.settings_path],
            outputs=[self.batch_folder,self.resized_img_folder,self.tag_sep,self.tag_order_format,self.prepend_tags,self.append_tags,self.img_ext,
                     self.method_tag_files,self.min_score,self.min_fav_count,self.min_year,self.min_month,self.min_day,self.min_area,self.top_n,self.min_short_side,
                     self.collect_checkbox_group_var,self.download_checkbox_group_var,self.resize_checkbox_group_var,
                     self.required_tags_group_var,self.blacklist_tags_group_var,self.skip_posts_file,self.skip_posts_type,
                     self.collect_from_listed_posts_file,self.collect_from_listed_posts_type,self.apply_filter_to_listed_posts,
                     self.save_searched_list_type,self.save_searched_list_path,self.downloaded_posts_folder,self.png_folder,self.jpg_folder,
                     self.webm_folder,self.gif_folder,self.swf_folder,self.save_filename_type,self.gallery_tab_manager.remove_tags_list,self.gallery_tab_manager.replace_tags_list,
                     self.tag_count_list_folder,self.all_json_files_checkboxgroup,self.quick_json_select,self.proxy_url_textbox,
                     self.settings_path, self.custom_csv_path_textbox, self.use_csv_custom_checkbox, 
                     self.override_download_delay_checkbox, self.custom_download_delay_slider, self.custom_retry_attempts_slider]
        ).then(
            fn=self.check_to_reload_auto_complete_config,
            inputs=[],
            outputs=[]
        ).then(
            fn=self.gallery_tab_manager.reset_gallery_manager,
            inputs=[],
            outputs=[
                self.gallery_tab_manager.download_folder_type,
                self.gallery_tab_manager.img_id_textbox,
                self.gallery_tab_manager.tag_search_textbox,
                self.gallery_tab_manager.tag_search_suggestion_dropdown,
                self.gallery_tab_manager.apply_to_all_type_select_checkboxgroup,
                self.gallery_tab_manager.select_multiple_images_checkbox,
                self.gallery_tab_manager.select_between_images_checkbox,
                self.gallery_tab_manager.apply_datetime_sort_ckbx,
                self.gallery_tab_manager.apply_datetime_choice_menu,
                self.gallery_tab_manager.send_img_from_gallery_dropdown,
                self.gallery_tab_manager.batch_send_from_gallery_checkbox,
                self.gallery_tab_manager.tag_add_textbox,
                self.gallery_tab_manager.tag_add_suggestion_dropdown,
                self.gallery_tab_manager.category_filter_gallery_dropdown,
                self.gallery_tab_manager.tag_effects_gallery_dropdown,
                self.gallery_tab_manager.img_artist_tag_checkbox_group,
                self.gallery_tab_manager.img_character_tag_checkbox_group,
                self.gallery_tab_manager.img_species_tag_checkbox_group,
                self.gallery_tab_manager.img_general_tag_checkbox_group,
                self.gallery_tab_manager.img_meta_tag_checkbox_group,
                self.gallery_tab_manager.img_rating_tag_checkbox_group,
                self.gallery_tab_manager.gallery_comp
            ]
        ).then(
            fn=self.refresh_json_options,
            inputs=[],
            outputs=[
                self.all_json_files_checkboxgroup,
                self.quick_json_select,
                self.preset_status_style,
            ]
        )
        self.remove_button_required.click(
            fn=self.check_box_group_handler_required,
            inputs=[self.required_tags_group_var],
            outputs=[self.required_tags_group_var]
        )
        self.remove_button_blacklist.click(
            fn=self.check_box_group_handler_blacklist,
            inputs=[self.blacklist_tags_group_var],
            outputs=[self.blacklist_tags_group_var]
        )
        self.parse_button_required.click(
            fn=self.parse_file_required,
            inputs=[self.file_all_tags_list_required],
            outputs=[self.required_tags_group_var]
        )
        self.parse_button_blacklist.click(
            fn=self.parse_file_blacklist,
            inputs=[self.file_all_tags_list_blacklist],
            outputs=[self.blacklist_tags_group_var]
        )
        self.required_tags_textbox.submit(
             fn=self.textbox_handler_required,
             inputs=[self.required_tags_textbox, self.initial_required_state, gr.State(True)],
             outputs=[self.initial_required_state_tag, self.required_tags_group_var, self.required_tags_textbox]
        )
        self.tag_required_suggestion_dropdown.select(
            fn=self.tag_ideas.dropdown_handler_required,
            inputs=[],
            outputs=[self.required_tags_textbox, self.tag_required_suggestion_dropdown, self.initial_required_state,
                     self.initial_required_state_tag, self.required_tags_group_var]
        )
        self.blacklist_tags_textbox.submit(
            fn=self.textbox_handler_blacklist,
            inputs=[self.blacklist_tags_textbox, self.initial_blacklist_state, gr.State(True)],
            outputs=[self.initial_blacklist_state_tag, self.blacklist_tags_group_var, self.blacklist_tags_textbox]
        )
        self.tag_blacklist_suggestion_dropdown.select(
            fn=self.tag_ideas.dropdown_handler_blacklist,
            inputs=[],
            outputs=[self.blacklist_tags_textbox, self.tag_blacklist_suggestion_dropdown, self.initial_blacklist_state,
                     self.initial_blacklist_state_tag, self.blacklist_tags_group_var]
        )
        self.gen_tags_list_button.click(
            fn=self.gen_tags_list,
            inputs=[self.reference_model_tags_file],
            outputs=[]
        )
        self.gen_tags_diff_list_button.click(
            fn=self.gen_tags_diff_list,
            inputs=[self.reference_model_tags_file],
            outputs=[]
        )
        self.download_remove_tag_file_button.click(
            fn=help.download_negative_tags_file,
            inputs=None,
            outputs=None
        )
        self.batch_browse.change(lambda p: p, inputs=self.batch_browse, outputs=self.batch_folder)
        self.json_browse.change(
            fn=self.change_config_file,
            inputs=self.json_browse,
            outputs=[self.batch_folder, self.resized_img_folder, self.tag_sep, self.tag_order_format,
                     self.prepend_tags, self.append_tags, self.img_ext, self.method_tag_files, self.min_score,
                     self.min_fav_count, self.min_year, self.min_month, self.min_day, self.min_area, self.top_n,
                     self.min_short_side, self.collect_checkbox_group_var, self.download_checkbox_group_var,
                     self.resize_checkbox_group_var, self.required_tags_group_var, self.blacklist_tags_group_var,
                     self.skip_posts_file, self.skip_posts_type, self.collect_from_listed_posts_file,
                     self.collect_from_listed_posts_type, self.apply_filter_to_listed_posts,
                     self.save_searched_list_type, self.save_searched_list_path, self.downloaded_posts_folder,
                     self.png_folder, self.jpg_folder, self.webm_folder, self.gif_folder, self.swf_folder,
                     self.save_filename_type, self.gallery_tab_manager.remove_tags_list, self.gallery_tab_manager.replace_tags_list,
                     self.tag_count_list_folder, self.all_json_files_checkboxgroup, self.quick_json_select,
                     self.proxy_url_textbox, self.settings_path,  self.custom_csv_path_textbox,
                     self.use_csv_custom_checkbox, self.override_download_delay_checkbox, self.custom_download_delay_slider,
                     self.custom_retry_attempts_slider]
        )
        self.images_full_change_dict_run_button.click(
            fn=self.make_run_visible,
            inputs=[],
            outputs=[self.progress_bar_textbox_collect]).then(
            fn=self.auto_config_apply,
            inputs=[self.images_full_change_dict_textbox],
            outputs=[self.progress_bar_textbox_collect]
        )
