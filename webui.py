import gradio as gr
import os
import multiprocessing as mp
import glob
import copy

import batch_downloader
import autotag
import helper_functions as help
import css_constants as css_
import js_constants as js_
import md_constants as md_

import argparse
import datetime
import pandas as pd
from tqdm import tqdm
import numpy as np
from PIL import Image

'''
##################################################################################################################################
#################################################     COMPONENT/S FUNCTION/S     #################################################
##################################################################################################################################
'''
def generate_all_dirs():
    global settings_json
    temp_path_list_dirs = []
    batch_dir_path = os.path.join(os.getcwd(), settings_json["batch_folder"])
    temp_path_list_dirs.append(batch_dir_path)
    downloaded_posts_dir_path = os.path.join(batch_dir_path, settings_json["downloaded_posts_folder"])
    temp_path_list_dirs.append(downloaded_posts_dir_path)
    temp_path_list_dirs.append(os.path.join(downloaded_posts_dir_path, settings_json["png_folder"]))
    temp_path_list_dirs.append(os.path.join(downloaded_posts_dir_path, settings_json["jpg_folder"]))
    temp_path_list_dirs.append(os.path.join(downloaded_posts_dir_path, settings_json["webm_folder"]))
    temp_path_list_dirs.append(os.path.join(downloaded_posts_dir_path, settings_json["gif_folder"]))
    temp_path_list_dirs.append(os.path.join(downloaded_posts_dir_path, settings_json["swf_folder"]))
    temp_path_list_dirs.append(os.path.join(batch_dir_path, settings_json["tag_count_list_folder"]))
    # create all dirs
    help.make_all_dirs(temp_path_list_dirs)
    # check to create tags & category csv files
    tag_folder = os.path.join(batch_dir_path, settings_json["tag_count_list_folder"])
    # persist changes to csv dictionary files OR (CREATE NEW)
    help.write_tags_to_csv(artist_csv_dict, os.path.join(tag_folder, "artist.csv"))
    help.write_tags_to_csv(character_csv_dict, os.path.join(tag_folder, "character.csv"))
    help.write_tags_to_csv(species_csv_dict, os.path.join(tag_folder, "species.csv"))
    help.write_tags_to_csv(general_csv_dict, os.path.join(tag_folder, "general.csv"))
    help.write_tags_to_csv(meta_csv_dict, os.path.join(tag_folder, "meta.csv"))
    help.write_tags_to_csv(rating_csv_dict, os.path.join(tag_folder, "rating.csv"))
    help.write_tags_to_csv(tags_csv_dict, os.path.join(tag_folder, "tags.csv"))

def add_current_images():
    global auto_complete_config, all_images_dict
    temp = list(all_images_dict.keys())
    if "searched" in temp:
        temp.remove("searched")
    for ext in temp:
        for every_image in list(all_images_dict[ext].keys()):
            if not every_image in auto_complete_config[ext]:
                auto_complete_config[ext][every_image] = []

def reset_selected_img(img_id_textbox):
    # reset selected_img
    global selected_image_dict
    selected_image_dict = None

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

def config_save_button(batch_folder,resized_img_folder,tag_sep,tag_order_format,prepend_tags,append_tags,img_ext,
                              method_tag_files,min_score,min_fav_count,min_area,top_n,min_short_side,
                              skip_posts_file,skip_posts_type,
                       collect_from_listed_posts_file,collect_from_listed_posts_type,apply_filter_to_listed_posts,
                       save_searched_list_type,save_searched_list_path,downloaded_posts_folder,png_folder,jpg_folder,
                       webm_folder,gif_folder,swf_folder,save_filename_type,remove_tags_list,replace_tags_list,
                       tag_count_list_folder,min_month,min_day,min_year,collect_checkbox_group_var,download_checkbox_group_var,
                       resize_checkbox_group_var,create_new_config_checkbox,settings_path,proxy_url_textbox):

    global settings_json
    settings_json["batch_folder"] = str(batch_folder)
    settings_json["resized_img_folder"] = str(resized_img_folder)
    settings_json["tag_sep"] = str(tag_sep)
    settings_json["tag_order_format"] = str(tag_order_format)
    settings_json["prepend_tags"] = str(prepend_tags)
    settings_json["append_tags"] = str(append_tags)
    settings_json["img_ext"] = str(img_ext)
    settings_json["method_tag_files"] = str(method_tag_files)
    settings_json["min_score"] = int(min_score)
    settings_json["min_fav_count"] = int(min_fav_count)

    settings_json["min_year"] = int(min_year)
    settings_json["min_month"] = int(min_month)
    settings_json["min_day"] = int(min_day)

    settings_json["min_date"] = f"{int(min_year)}-{help.to_padded(int(min_month))}-{help.to_padded(int(min_day))}"

    settings_json["min_area"] = int(min_area)
    settings_json["top_n"] = int(top_n)
    settings_json["min_short_side"] = int(min_short_side)

    settings_json["proxy_url"] = str(min_short_side)

    # COLLECT CheckBox Group
    for key in collect_checkboxes:
        if key in collect_checkbox_group_var:
            settings_json[key] = True
        else:
            settings_json[key] = False
    # DOWNLOAD CheckBox Group
    for key in download_checkboxes:
        if key in download_checkbox_group_var:
            settings_json[key] = True
        else:
            settings_json[key] = False
    # RESIZE CheckBox Group
    for key in resize_checkboxes:
        if key in resize_checkbox_group_var:
            settings_json[key] = True
        else:
            settings_json[key] = False

    settings_json["required_tags"] = help.get_string(required_tags_list, str(tag_sep))
    settings_json["blacklist"] = help.get_string(blacklist_tags, " | ")

    settings_json["skip_posts_file"] = str(skip_posts_file)
    settings_json["skip_posts_type"] = str(skip_posts_type)
    settings_json["collect_from_listed_posts_file"] = str(collect_from_listed_posts_file)
    settings_json["collect_from_listed_posts_type"] = str(collect_from_listed_posts_type)
    settings_json["apply_filter_to_listed_posts"] = bool(apply_filter_to_listed_posts)
    settings_json["save_searched_list_type"] = str(save_searched_list_type)
    settings_json["save_searched_list_path"] = str(save_searched_list_path)
    settings_json["downloaded_posts_folder"] = str(downloaded_posts_folder)
    settings_json["png_folder"] = str(png_folder)
    settings_json["jpg_folder"] = str(jpg_folder)
    settings_json["webm_folder"] = str(webm_folder)
    settings_json["gif_folder"] = str(gif_folder)
    settings_json["swf_folder"] = str(swf_folder)
    settings_json["save_filename_type"] = str(save_filename_type)
    settings_json["remove_tags_list"] = str(remove_tags_list)
    settings_json["replace_tags_list"] = str(replace_tags_list)
    settings_json["tag_count_list_folder"] = str(tag_count_list_folder)

    if create_new_config_checkbox: # if called from the "create new button" the True flag will always be passed to ensure this
        temp = '\\' if help.is_windows() else '/'
        global config_name
        if temp in settings_path:
            config_name = settings_path
        else:
            config_name = os.path.join(cwd, settings_path)

    if not config_name or len(config_name) == 0:
        raise ValueError('No Config Name Specified')

    # Update json
    help.update_JSON(settings_json, config_name)

    temp = '\\' if help.is_windows() else '/'
    all_json_files_checkboxgroup = gr.update(choices=sorted([(each_settings_file.split(temp)[-1]) for each_settings_file in glob.glob(os.path.join(cwd, f"*.json"))]), value=[])
    quick_json_select = gr.update(choices=sorted([(each_settings_file.split(temp)[-1]) for each_settings_file in glob.glob(os.path.join(cwd, f"*.json"))]))

    return all_json_files_checkboxgroup, quick_json_select

def textbox_handler_required(tag_string_comp):
    temp_tags = None
    if settings_json["tag_sep"] in tag_string_comp:
        temp_tags = tag_string_comp.split(settings_json["tag_sep"])
    elif " | " in tag_string_comp:
        temp_tags = tag_string_comp.split(" | ")
    else:
        temp_tags = [tag_string_comp]

    for tag in temp_tags:
        if not tag in required_tags_list:
            required_tags_list.append(tag)
    return gr.update(lines=1, label='Press Enter to ADD tag/s (E.g. tag1    or    tag1, tag2, ..., etc.)', value=""), \
           gr.update(choices=required_tags_list, label='ALL Required Tags', value=[])

def textbox_handler_blacklist(tag_string_comp):
    temp_tags = None
    if settings_json["tag_sep"] in tag_string_comp:
        temp_tags = tag_string_comp.split(settings_json["tag_sep"])
    elif " | " in tag_string_comp:
        temp_tags = tag_string_comp.split(" | ")
    else:
        temp_tags = [tag_string_comp]

    for tag in temp_tags:
        if not tag in blacklist_tags:
            blacklist_tags.append(tag)
    return gr.update(lines=1, label='Press Enter to ADD tag/s (E.g. tag1    or    tag1, tag2, ..., etc.)', value=""), \
           gr.update(choices=blacklist_tags, label='ALL Blacklisted Tags', value=[])

def check_box_group_handler_required(check_box_group):
    for tag in check_box_group:
        required_tags_list.remove(tag)
    return gr.update(choices=required_tags_list, label='ALL Required Tags', value=[])

def check_box_group_handler_blacklist(check_box_group):
    for tag in check_box_group:
        blacklist_tags.remove(tag)
    return gr.update(choices=blacklist_tags, label='ALL Blacklisted Tags', value=[])

### file expects a format of 1 tag per line, with the tag being before the first comma
def parse_file_required(file_list):
    for single_file in file_list:
        with open(single_file.name, 'r', encoding='utf-8') as read_file:
            while True:
                line = read_file.readline()
                if not line:
                    break

                length = len(line.replace(" ", "").split(","))

                if length > 3: # assume everything on one line
                    tags = line.replace(" ", "").split(",")
                    for tag in tags:
                        if not tag in required_tags_list:
                            required_tags_list.append(tag)
                else: # assume cascaded tags
                    tag = line.replace(" ", "").split(",")[0]
                    if not tag in required_tags_list:
                        required_tags_list.append(tag)
            read_file.close()
    return gr.update(choices=required_tags_list, label='ALL Required Tags', value=[])

### file expects a format of 1 tag per line, with the tag being before the first comma
def parse_file_blacklist(file_list):
    for single_file in file_list:
        with open(single_file.name, 'r', encoding='utf-8') as read_file:
            while True:
                line = read_file.readline()
                if not line:
                    break

                length = len(line.replace(" ", "").split(","))

                if length > 3: # assume everything on one line
                    tags = line.replace(" ", "").split(",")
                    for tag in tags:
                        if not tag in blacklist_tags:
                            blacklist_tags.append(tag)
                else: # assume cascaded tags
                    tag = line.replace(" ", "").split(",")[0]
                    if not tag in blacklist_tags:
                        blacklist_tags.append(tag)
            read_file.close()
    return gr.update(choices=blacklist_tags, label='ALL Blacklisted Tags', value=[])

def make_run_visible():
    return gr.update(interactive=False, visible=True)

def make_invisible():
    return gr.update(interactive=False, visible=False)

def run_script(basefolder='',settings_path=os.getcwd(),numcpu=-1,phaseperbatch=False,keepdb=False,cachepostsdb=False,postscsv='',tagscsv='',postsparquet='',tagsparquet=''):
    help.verbose_print(f"RUN COMMAND IS:\t{basefolder, settings_path, numcpu, phaseperbatch, postscsv, tagscsv, postsparquet, tagsparquet, keepdb, cachepostsdb}")

    #### ADD A PIPE parameter that passes the connection to the other process
    global frontend_conn, backend_conn
    frontend_conn, backend_conn = mp.Pipe()
    global e6_downloader
    e6_downloader = mp.Process(target=batch_downloader.E6_Downloader, args=(basefolder, settings_path, numcpu, phaseperbatch, postscsv, tagscsv, postsparquet, tagsparquet, keepdb, cachepostsdb, backend_conn),)
    e6_downloader.start()

def run_script_batch(basefolder='',settings_path=os.getcwd(),numcpu=-1,phaseperbatch=False,keepdb=False,cachepostsdb=False,postscsv='',tagscsv='',postsparquet='',tagsparquet='',run_button_batch=None,images_full_change_dict_textbox=None,progress=gr.Progress()):
    global settings_json
    help.verbose_print(f"RUN COMMAND IS:\t{basefolder, settings_path, numcpu, phaseperbatch, postscsv, tagscsv, postsparquet, tagsparquet, keepdb, cachepostsdb}")

    progress(0, desc="Starting...")
    for setting in progress.tqdm(run_button_batch, desc="Tracking Total Progress"):
        path = os.path.join(cwd, setting)
        if not ".json" in path:
            path += ".json"

        e6_downloader = batch_downloader.E6_Downloader(basefolder, path, numcpu, phaseperbatch, postscsv, tagscsv, postsparquet, tagsparquet, keepdb, cachepostsdb, None)
        #
        # settings_json = help.load_session_config(path)
        # # apply post-processing
        # auto_config_apply(images_full_change_dict_textbox)
        del e6_downloader
    return gr.update(interactive=False, visible=False)

def data_collect(progress=gr.Progress()):
    # thread block and wait for response
    total = int(frontend_conn.recv())

    progress(0, desc="Starting...")
    for i in progress.tqdm(range(total), desc="Collecting"):
        _ = frontend_conn.recv()
    return gr.update(interactive=False, visible=False)

def data_download(progress=gr.Progress()):
    # thread block and wait for response
    total = int(frontend_conn.recv())

    progress(0, desc="Starting...")
    for i in progress.tqdm(range(0,total), desc="Downloading"):
        _ = int(frontend_conn.recv())
    return gr.update(interactive=False, visible=False)

def data_resize(resize_checkbox_group, progress=gr.Progress()):
    global frontend_conn, backend_conn
    if not "skip_resize" in resize_checkbox_group:
        # thread block and wait for response
        total = int(frontend_conn.recv())

        progress(0, desc="Starting...")
        for i in progress.tqdm(range(total), desc="Resizing"):
            _ = frontend_conn.recv()

    frontend_conn.close()
    del frontend_conn, backend_conn
    return gr.update(interactive=False, visible=False)

def end_connection():
    global e6_downloader
    e6_downloader.join()
    del e6_downloader

def initialize_posts_timekeeper():
    global all_images_dict, image_creation_times
    start_year_temp = int(settings_json["min_year"])
    end_year_temp = datetime.date.today().year
    help.verbose_print(f"start_year_temp:\t{start_year_temp}")
    help.verbose_print(f"end_year_temp:\t{end_year_temp}")
    years_to_check_list = list(range(start_year_temp, (end_year_temp + 1), 1))
    help.verbose_print(f"years_to_check_list:\t{years_to_check_list}")

    if len(list(image_creation_times.keys())) == 0:
        temp_keys_all_images_dict = list(all_images_dict.keys())
        if "searched" in temp_keys_all_images_dict:
            temp_keys_all_images_dict.remove("searched")
        for ext in temp_keys_all_images_dict:
            for img_id in list(all_images_dict[ext].keys()):
                for year in years_to_check_list:
                    if str(year) in all_images_dict[ext][img_id]:
                        image_creation_times[img_id] = year
                        break
    help.verbose_print(f"image_creation_times:\t{image_creation_times}")

### Update gellery component
def update_search_gallery(sort_images, sort_option):
    global all_images_dict, image_creation_times
    temp = '\\' if help.is_windows() else '/'
    folder_path = os.path.join(cwd, settings_json["batch_folder"])
    folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
    images = []
    for ext in list(all_images_dict["searched"].keys()):
        search_path = os.path.join(folder_path, settings_json[f"{ext}_folder"])
        for img_id in list(all_images_dict["searched"][ext].keys()):
            images.append(os.path.join(search_path, f"{img_id}.{ext}"))

    if sort_images and len(sort_option) > 0 and len(list(image_creation_times.keys())) > 0:
        # parse to img_id -> to get the year
        if sort_option == "new-to-old":
            images = sorted(images, key=lambda x: image_creation_times.get(((x.split(temp)[-1]).split(".")[0]), float('-inf')), reverse=True)
        elif sort_option == "old-to-new":
            images = sorted(images, key=lambda x: image_creation_times.get(((x.split(temp)[-1]).split(".")[0]), float('-inf')))
    # help.verbose_print(f"images:\t{images}")
    return images

######
# all_images_dict ->
### image_type -> {img_id, tags}
### searched -> {img_id, tags}
######
def show_gallery(folder_type_select, sort_images, sort_option):
    help.verbose_print(f"folder_type_select:\t{folder_type_select}")

    global all_images_dict, image_creation_times
    temp = '\\' if help.is_windows() else '/'
    # clear searched dict
    if "searched" in all_images_dict:
        del all_images_dict["searched"]
        all_images_dict["searched"] = {}

    folder_path = os.path.join(cwd, settings_json["batch_folder"])
    folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
    folder_path = os.path.join(folder_path, settings_json[f"{folder_type_select}_folder"])

    # type select
    images = []
    if not all_images_dict or len(all_images_dict.keys()) == 0:
        images = glob.glob(os.path.join(folder_path, f"*.{folder_type_select}"))
        # loading images
        add_current_images()
    else:
        for name in list(all_images_dict[folder_type_select].keys()):
            images.append(os.path.join(folder_path, f"{str(name)}.{folder_type_select}"))

    global is_csv_loaded
    if not is_csv_loaded:
        full_path_downloads = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                           settings_json["downloaded_posts_folder"])

        tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]), settings_json["tag_count_list_folder"])
        # load ALL tags into relative categorical dictionaries
        is_csv_loaded = True
        global artist_csv_dict, character_csv_dict, species_csv_dict, general_csv_dict, meta_csv_dict, rating_csv_dict, tags_csv_dict
        artist_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "artist.csv"))
        character_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "character.csv"))
        species_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "species.csv"))
        general_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "general.csv"))
        meta_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "meta.csv"))
        rating_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "rating.csv"))
        tags_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "tags.csv"))

        if not all_images_dict or len(all_images_dict.keys()) == 0:
            all_images_dict = help.merge_dict(os.path.join(full_path_downloads, settings_json[f"png_folder"]),
                                         os.path.join(full_path_downloads, settings_json[f"jpg_folder"]),
                                         os.path.join(full_path_downloads, settings_json[f"gif_folder"]))

        # populate the timekeeping dictionary
        initialize_posts_timekeeper()

        # verbose_print(f"all_images_dict:\t\t{all_images_dict}")
        # help.verbose_print(f"list(all_images_dict[ext]):\t\t{list(all_images_dict[folder_type_select])}")

    if sort_images and len(sort_option) > 0 and len(list(image_creation_times.keys())) > 0:
        # parse to img_id -> to get the year
        if sort_option == "new-to-old":
            images = sorted(images, key=lambda x: image_creation_times.get(((x.split(temp)[-1]).split(".")[0]), float('-inf')),
                            reverse=True)
        elif sort_option == "old-to-new":
            images = sorted(images, key=lambda x: image_creation_times.get(((x.split(temp)[-1]).split(".")[0]), float('-inf')))

    # help.verbose_print(f"images:\t{images}")
    return gr.update(value=images, visible=True)

######
# all_images_dict ->
### image_type -> {img_id, tags}
### searched -> {img_id, tags}
######
def force_reload_show_gallery(folder_type_select, sort_images, sort_option):
    help.verbose_print(f"folder_type_select:\t{folder_type_select}")

    global all_images_dict, image_creation_times
    temp = '\\' if help.is_windows() else '/'
    # clear searched dict
    if "searched" in all_images_dict:
        del all_images_dict["searched"]
        all_images_dict["searched"] = {}

    folder_path = os.path.join(cwd, settings_json["batch_folder"])
    folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
    folder_path = os.path.join(folder_path, settings_json[f"{folder_type_select}_folder"])

    # type select
    images = []
    if not all_images_dict or len(all_images_dict.keys()) == 0:
        images = glob.glob(os.path.join(folder_path, f"*.{folder_type_select}"))
        # loading images
        add_current_images()
    else:
        for name in list(all_images_dict[folder_type_select].keys()):
            images.append(os.path.join(folder_path, f"{str(name)}.{folder_type_select}"))

    global is_csv_loaded
    is_csv_loaded = False
    if not is_csv_loaded:
        full_path_downloads = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                           settings_json["downloaded_posts_folder"])

        tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]), settings_json["tag_count_list_folder"])
        # load ALL tags into relative categorical dictionaries
        is_csv_loaded = True
        global artist_csv_dict, character_csv_dict, species_csv_dict, general_csv_dict, meta_csv_dict, rating_csv_dict, tags_csv_dict
        artist_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "artist.csv"))
        character_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "character.csv"))
        species_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "species.csv"))
        general_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "general.csv"))
        meta_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "meta.csv"))
        rating_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "rating.csv"))
        tags_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "tags.csv"))

        if not all_images_dict or len(all_images_dict.keys()) == 0:
            all_images_dict = help.merge_dict(os.path.join(full_path_downloads, settings_json[f"png_folder"]),
                                         os.path.join(full_path_downloads, settings_json[f"jpg_folder"]),
                                         os.path.join(full_path_downloads, settings_json[f"gif_folder"]))

        # populate the timekeeping dictionary
        initialize_posts_timekeeper()

        # verbose_print(f"all_images_dict:\t\t{all_images_dict}")
        # help.verbose_print(f"list(all_images_dict[ext]):\t\t{list(all_images_dict[folder_type_select])}")

    if sort_images and len(sort_option) > 0 and len(list(image_creation_times.keys())) > 0:
        # parse to img_id -> to get the year
        if sort_option == "new-to-old":
            images = sorted(images, key=lambda x: image_creation_times.get(((x.split(temp)[-1]).split(".")[0]), float('-inf')),
                            reverse=True)
        elif sort_option == "old-to-new":
            images = sorted(images, key=lambda x: image_creation_times.get(((x.split(temp)[-1]).split(".")[0]), float('-inf')))

    # help.verbose_print(f"images:\t{images}")
    return gr.update(value=images, visible=True)

def clear_categories():
    artist_comp_checkboxgroup = gr.update(choices=[])
    character_comp_checkboxgroup = gr.update(choices=[])
    species_comp_checkboxgroup = gr.update(choices=[])
    general_comp_checkboxgroup = gr.update(choices=[])
    meta_comp_checkboxgroup = gr.update(choices=[])
    rating_comp_checkboxgroup = gr.update(choices=[])
    return artist_comp_checkboxgroup, character_comp_checkboxgroup, species_comp_checkboxgroup, general_comp_checkboxgroup, \
           meta_comp_checkboxgroup, rating_comp_checkboxgroup, gr.update(value="")

def get_saved_image_count():
    global auto_complete_config
    total_img_count = 0
    img_count_list = []
    for key in ['png', 'jpg', 'gif']:
        img_count_list.append(len(list(auto_complete_config[key].keys())))
        total_img_count += img_count_list[-1]
    img_count_list.append(total_img_count)
    return img_count_list

def get_searched_image_total():
    global all_images_dict
    total_img_count = 0
    temp_key_list = list(all_images_dict["searched"].keys())
    for key in temp_key_list:
        total_img_count += len(list(all_images_dict["searched"][key].keys()))
    return total_img_count

def show_searched_gallery(folder_type_select, sort_images, sort_option):
    global all_images_dict
    # type select
    if "searched" in all_images_dict and len(list(all_images_dict["searched"].keys())) > 0 and get_searched_image_total() > 0:
        images = update_search_gallery(sort_images, sort_option)
    else:
        help.verbose_print(f"in SHOW searched gallery")
        return show_gallery(folder_type_select, sort_images, sort_option)
    return gr.update(value=images, visible=True)

def reset_gallery():
    return gr.update(value=[], visible=True)

# load a different config
def change_config(quick_json_select, file_path):
    temp = '\\' if help.is_windows() else '/'
    global settings_json
    global config_name

    settings_path = None

    if quick_json_select != config_name:
        settings_json = help.load_session_config(os.path.join(cwd, quick_json_select))
        config_name = os.path.join(cwd, quick_json_select)
        settings_path = gr.update(value=config_name)
    else:
        if temp in file_path:
            settings_json = help.load_session_config(file_path)
            config_name = file_path
            settings_path = gr.update(value=config_name)
        else:
            settings_json = help.load_session_config(os.path.join(cwd, file_path))
            config_name = os.path.join(cwd, file_path)
            settings_path = gr.update(value=config_name)

    global required_tags_list
    required_tags_list = help.get_list(settings_json["required_tags"], settings_json["tag_sep"])
    for tag in required_tags_list:
        if len(tag) == 0:
            required_tags_list.remove(tag)

    global blacklist_tags
    blacklist_tags = help.get_list(settings_json["blacklist"], " | ")
    for tag in blacklist_tags:
        if len(tag) == 0:
            blacklist_tags.remove(tag)

    help.verbose_print(f"{settings_json}")
    help.verbose_print(f"json key count: {len(settings_json)}")

    # UPDATE json with new key, value pairs
    if not "min_date" in settings_json:
        settings_json["min_year"] = 2000
    elif isinstance(settings_json["min_date"], str) and "-" in settings_json["min_date"]:
        settings_json["min_year"] = int(settings_json["min_date"].split("-")[0])
    else:
        settings_json["min_year"] = int(settings_json["min_date"])

    if not "min_month" in settings_json:
        settings_json["min_month"] = 1
    elif isinstance(settings_json["min_date"], str) and "-" in settings_json["min_date"]:
        settings_json["min_month"] = help.from_padded(settings_json["min_date"].split("-")[1])

    if not "min_day" in settings_json:
        settings_json["min_day"] = 1
    elif isinstance(settings_json["min_date"], str) and settings_json["min_date"].count("-") > 1:
        settings_json["min_day"] = help.from_padded(settings_json["min_date"].split("-")[-1])

    help.update_JSON(settings_json, config_name)

    # load all presets
    batch_folder = gr.update(value=settings_json["batch_folder"])
    resized_img_folder = gr.update(value=settings_json["resized_img_folder"])
    tag_sep = gr.update(value=settings_json["tag_sep"])
    tag_order_format = gr.update(value=settings_json["tag_order_format"])
    prepend_tags = gr.update(value=settings_json["prepend_tags"])
    append_tags = gr.update(value=settings_json["append_tags"])
    img_ext = gr.update(value=settings_json["img_ext"])
    method_tag_files = gr.update(value=settings_json["method_tag_files"])
    min_score = gr.update(value=settings_json["min_score"])
    min_fav_count = gr.update(value=settings_json["min_fav_count"])
    min_month = gr.update(value=settings_json["min_month"])
    min_day = gr.update(value=settings_json["min_day"])
    min_year = gr.update(value=settings_json["min_year"])
    min_area = gr.update(value=settings_json["min_area"])
    top_n = gr.update(value=settings_json["top_n"])
    min_short_side = gr.update(value=settings_json["min_short_side"])
    collect_checkbox_group_var = gr.update(choices=collect_checkboxes, value=help.grab_pre_selected(settings_json, collect_checkboxes))
    download_checkbox_group_var = gr.update(choices=download_checkboxes, value=help.grab_pre_selected(settings_json, download_checkboxes))
    resize_checkbox_group_var = gr.update(choices=resize_checkboxes, value=help.grab_pre_selected(settings_json, resize_checkboxes))
    required_tags_group_var = gr.update(choices=required_tags_list, value=[])
    blacklist_group_var = gr.update(choices=blacklist_tags, value=[])
    skip_posts_file = gr.update(value=settings_json["skip_posts_file"])
    skip_posts_type = gr.update(value=settings_json["skip_posts_type"])
    collect_from_listed_posts_file = gr.update(value=settings_json["collect_from_listed_posts_file"])
    collect_from_listed_posts_type = gr.update(value=settings_json["collect_from_listed_posts_type"])
    apply_filter_to_listed_posts = gr.update(value=settings_json["apply_filter_to_listed_posts"])
    save_searched_list_type = gr.update(value=settings_json["save_searched_list_type"])
    save_searched_list_path = gr.update(value=settings_json["save_searched_list_path"])
    downloaded_posts_folder = gr.update(value=settings_json["downloaded_posts_folder"])
    png_folder = gr.update(value=settings_json["png_folder"])
    jpg_folder = gr.update(value=settings_json["jpg_folder"])
    webm_folder = gr.update(value=settings_json["webm_folder"])
    gif_folder = gr.update(value=settings_json["gif_folder"])
    swf_folder = gr.update(value=settings_json["swf_folder"])
    save_filename_type = gr.update(value=settings_json["save_filename_type"])
    remove_tags_list = gr.update(value=settings_json["remove_tags_list"])
    replace_tags_list = gr.update(value=settings_json["replace_tags_list"])
    tag_count_list_folder = gr.update(value=settings_json["tag_count_list_folder"])
    proxy_url_textbox = gr.update(value=settings_json["proxy_url"])

    help.verbose_print(f"{settings_json}")
    help.verbose_print(f"json key count: {len(settings_json)}")

    global is_csv_loaded
    is_csv_loaded = False

    all_json_files_checkboxgroup = gr.update(choices=sorted([(each_settings_file.split(temp)[-1]) for each_settings_file in glob.glob(os.path.join(cwd, f"*.json"))]), value=[])
    quick_json_select = gr.update(choices=sorted([(each_settings_file.split(temp)[-1]) for each_settings_file in glob.glob(os.path.join(cwd, f"*.json"))]))

    return batch_folder,resized_img_folder,tag_sep,tag_order_format,prepend_tags,append_tags,img_ext,method_tag_files,min_score,min_fav_count,min_year,min_month, \
           min_day,min_area,top_n,min_short_side,collect_checkbox_group_var,download_checkbox_group_var,resize_checkbox_group_var,required_tags_group_var, \
           blacklist_group_var,skip_posts_file,skip_posts_type,collect_from_listed_posts_file,collect_from_listed_posts_type,apply_filter_to_listed_posts, \
           save_searched_list_type,save_searched_list_path,downloaded_posts_folder,png_folder,jpg_folder,webm_folder,gif_folder,swf_folder,save_filename_type, \
           remove_tags_list,replace_tags_list,tag_count_list_folder,all_json_files_checkboxgroup,quick_json_select,proxy_url_textbox,settings_path

def reload_selected_image_dict(ext, img_name):
    global selected_image_dict  # id -> {categories: tag/s}, type -> string
    global all_tags_ever_dict
    if img_name:
        img_tag_list = copy.deepcopy(all_images_dict[ext][img_name])
        help.verbose_print(f"img_tag_list:\t\t{img_tag_list}")
        # determine the category of each tag (TAGS WITHOUT A CATEGORY ARE NOT DISPLAYED)
        temp_tag_dict = {}
        temp_list = [[],[],[],[],[],[]]
        for tag in img_tag_list:
            if categories_map[all_tags_ever_dict[tag]] == 'artist':
                temp_list[0].append(tag)
            if categories_map[all_tags_ever_dict[tag]] == 'character':
                temp_list[1].append(tag)
            if categories_map[all_tags_ever_dict[tag]] == 'species':
                temp_list[2].append(tag)
            if categories_map[all_tags_ever_dict[tag]] == 'general':
                temp_list[3].append(tag)
            if categories_map[all_tags_ever_dict[tag]] == 'meta':
                temp_list[4].append(tag)
            if categories_map[all_tags_ever_dict[tag]] == 'rating':
                temp_list[5].append(tag)
        temp_tag_dict["artist"] = temp_list[0]
        temp_tag_dict["character"] = temp_list[1]
        temp_tag_dict["species"] = temp_list[2]
        temp_tag_dict["general"] = temp_list[3]
        temp_tag_dict["meta"] = temp_list[4]
        temp_tag_dict["rating"] = temp_list[5]

        selected_image_dict = {}
        selected_image_dict[img_name] = copy.deepcopy(temp_tag_dict)
        selected_image_dict["type"] = ext
        help.verbose_print(f"selected_image_dict:\t\t{selected_image_dict}")
    else:
        selected_image_dict = None

def extract_name_and_extention(gallery_comp_path):
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

def get_full_text_path(download_folder_type, img_name):
    global settings_json
    full_path_downloads = os.path.join(os.path.join(cwd, settings_json["batch_folder"]), settings_json["downloaded_posts_folder"])
    full_path_gallery_type = os.path.join(full_path_downloads, settings_json[f"{download_folder_type}_folder"])
    full_path = os.path.join(full_path_gallery_type, f"{img_name}.txt")
    # help.verbose_print(f"img_name:\t\t{img_name}")
    # help.verbose_print(f"full_path:\t\t{full_path}")
    return full_path

### Select an image
def get_img_tags(gallery_comp, select_multiple_images_checkbox, images_selected_state, select_between_images_checkbox, images_tuple_points, event_data: gr.SelectData):
    global selected_image_dict  # id -> {categories: tag/s}, type -> string

    help.verbose_print(f"gallery_comp[event_data.index]['name']:\t{gallery_comp[event_data.index]['name']}")

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

        if select_between_images_checkbox: # select/unselect all in-between n-1 & n
            if len(images_tuple_points) < 1:
                images_tuple_points.append(event_data.index)
                help.verbose_print(f"images_tuple_points:\t{images_tuple_points}")
            else:
                images_tuple_points.append(event_data.index)
                images_tuple_points = sorted(images_tuple_points) # small to large
                help.verbose_print(f"images_tuple_points:\t{images_tuple_points}")
                # temp removal
                for point in images_tuple_points:
                    images_selected_state.pop(images_selected_state.index(point))
                # toggle overlapping repectively
                # a-b|b-a
                set_a = set(images_selected_state)
                set_b = set([x for x in range(images_tuple_points[0], images_tuple_points[1]+1, 1)])
                set_c = (set_a-set_b)|(set_b-set_a)
                images_selected_state = list(set_c)
                images_tuple_points = []

        help.verbose_print(f"images_selected_states:\t{images_selected_state}")
    else:
        images_selected_state = []
        download_folder_type, img_name = extract_name_and_extention(gallery_comp[event_data.index]['name'])

        # if image name is not in the global dictionary --- then reload the gallery before loading the tags
        temp_all_images_dict_keys = list(all_images_dict.keys())
        if "searched" in temp_all_images_dict_keys:
            temp_all_images_dict_keys.remove("searched")

        ### POPULATE all categories for selected image
        if not all_images_dict:
            raise ValueError('radio button not pressed i.e. image type button')

        # load/re-load selected image
        reload_selected_image_dict(download_folder_type, img_name)

        artist_comp_checkboxgroup = gr.update(choices=selected_image_dict[img_name]["artist"])
        character_comp_checkboxgroup = gr.update(choices=selected_image_dict[img_name]["character"])
        species_comp_checkboxgroup = gr.update(choices=selected_image_dict[img_name]["species"])
        general_comp_checkboxgroup = gr.update(choices=selected_image_dict[img_name]["general"])
        meta_comp_checkboxgroup = gr.update(choices=selected_image_dict[img_name]["meta"])
        rating_comp_checkboxgroup = gr.update(choices=selected_image_dict[img_name]["rating"])

    only_selected_state_object = dict()
    for index in images_selected_state:
        only_selected_state_object[index] = extract_name_and_extention(gallery_comp[index]['name']) # returns index -> [ext, img_id]
    help.verbose_print(f"only_selected_state_object:\t{only_selected_state_object}")

    return gr.update(value=img_name), artist_comp_checkboxgroup, character_comp_checkboxgroup, species_comp_checkboxgroup, \
           general_comp_checkboxgroup, meta_comp_checkboxgroup, rating_comp_checkboxgroup, images_selected_state, only_selected_state_object, \
           images_tuple_points

def is_csv_dict_empty(stats_load_file):
    tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                 settings_json["tag_count_list_folder"])
    global artist_csv_dict, character_csv_dict, species_csv_dict, general_csv_dict, meta_csv_dict, rating_csv_dict, tags_csv_dict
    if "artist" in stats_load_file:
        value = len(list(artist_csv_dict.keys()))
        if (value == 0):
            artist_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "artist.csv"))
        return [copy.deepcopy(artist_csv_dict), value]
    elif "character" in stats_load_file:
        value = len(list(character_csv_dict.keys()))
        if (value == 0):
            character_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "character.csv"))
        return [copy.deepcopy(character_csv_dict), value]
    elif "species" in stats_load_file:
        value = len(list(species_csv_dict.keys()))
        if (value == 0):
            species_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "species.csv"))
        return [copy.deepcopy(species_csv_dict), value]
    elif "general" in stats_load_file:
        value = len(list(general_csv_dict.keys()))
        if (value == 0):
            general_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "general.csv"))
        return [copy.deepcopy(general_csv_dict), value]
    elif "meta" in stats_load_file:
        value = len(list(meta_csv_dict.keys()))
        if (value == 0):
            meta_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "meta.csv"))
        return [copy.deepcopy(meta_csv_dict), value]
    elif "rating" in stats_load_file:
        value = len(list(rating_csv_dict.keys()))
        if (value == 0):
            rating_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "rating.csv"))
        return [copy.deepcopy(rating_csv_dict), value]
    elif "tags" in stats_load_file:
        value = len(list(tags_csv_dict.keys()))
        if (value == 0):
            tags_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "tags.csv"))
        return [copy.deepcopy(tags_csv_dict), value]

def run_stats(stats_run_options, stats_load_file):
    csv_table, size = is_csv_dict_empty(stats_load_file)

    help.verbose_print(f"stats_run_options:\t\t{stats_run_options}")
    help.verbose_print(f"stats_load_file:\t\t{stats_load_file}")

    dataframe = None
    show_list = None
    if "frequency table" in stats_run_options:
        show_list = sorted(csv_table.items(), key=lambda x: x[1], reverse=True)
        dataframe = gr.update(visible=True, label=stats_run_options, max_rows=size,
                              value=show_list)
    elif "inverse freq table" in stats_run_options:
        total_sum = sum(csv_table.values())
        normalized_dict = {key: value / total_sum for key, value in csv_table.items()}
        show_list = sorted(normalized_dict.items(), key=lambda x: x[1], reverse=True)
        dataframe = gr.update(visible=True, label=stats_run_options, max_rows=size,
                              value=show_list)
    # verbose_print(f"show_list:\t\t{show_list}")
    return dataframe

### Search a set of images
def filter_images_by_tags(input_tags, allowed_image_types):
    global all_images_dict
    # clear searched dict
    del all_images_dict["searched"]
    all_images_dict["searched"] = {}
    # remove possible checked searched flag
    if "searched" in allowed_image_types:
        allowed_image_types.remove("searched")

    input_tags_list = input_tags.split(" ")#[tag.strip() for tag in input_tags.split(',')]
    positive_tags = [str(tag) for tag in input_tags_list if not tag.startswith('-')]
    negative_tags = [str(tag[1:]) for tag in input_tags_list if tag.startswith('-')]

    if allowed_image_types is None:
        allowed_image_types = all_images_dict.keys()

    filtered_images = {ext: {} for ext in allowed_image_types}

    for ext, images in all_images_dict.items():
        if ext in allowed_image_types:
            for image_id, tags in images.items():
                if all(tag in tags for tag in positive_tags) and not any(tag in tags for tag in negative_tags):
                    filtered_images[str(ext)][str(image_id)] = tags
    all_images_dict["searched"] = copy.deepcopy(filtered_images)
    help.verbose_print(f"===============================")

def search_tags(tag_search_textbox, global_search_opts, sort_images, sort_option):
    # update SEARCHED in global dictionary
    filter_images_by_tags(tag_search_textbox, global_search_opts)
    # return updated gallery
    images = update_search_gallery(sort_images, sort_option)
    return gr.update(value=images, visible=True)

def add_to_csv_dictionaries(string_category, tag, count=1):
    global artist_csv_dict, character_csv_dict, species_csv_dict, general_csv_dict, meta_csv_dict, rating_csv_dict, tags_csv_dict
    artist_csv_dict, character_csv_dict, species_csv_dict, \
    general_csv_dict, meta_csv_dict, rating_csv_dict, \
    tags_csv_dict = help.update_all_csv_dictionaries(copy.deepcopy(artist_csv_dict),copy.deepcopy(character_csv_dict),
                                                     copy.deepcopy(species_csv_dict),copy.deepcopy(general_csv_dict),
                                                     copy.deepcopy(meta_csv_dict),copy.deepcopy(rating_csv_dict),copy.deepcopy(tags_csv_dict),
                                                     string_category,tag,"+", count)

def remove_to_csv_dictionaries(string_category, tag, count=1):
    global artist_csv_dict, character_csv_dict, species_csv_dict, general_csv_dict, meta_csv_dict, rating_csv_dict, tags_csv_dict
    artist_csv_dict, character_csv_dict, species_csv_dict, \
    general_csv_dict, meta_csv_dict, rating_csv_dict, \
    tags_csv_dict = help.update_all_csv_dictionaries(copy.deepcopy(artist_csv_dict),copy.deepcopy(character_csv_dict),
                                                     copy.deepcopy(species_csv_dict),copy.deepcopy(general_csv_dict),
                                                     copy.deepcopy(meta_csv_dict),copy.deepcopy(rating_csv_dict),copy.deepcopy(tags_csv_dict),
                                                     string_category,tag,"-", count)

def get_insert_last_tags_name(string_category, ext, img_id, new_tag):
    global selected_image_dict
    del selected_image_dict

    # reload the categories for the selected_image_dict
    reload_selected_image_dict(ext, img_id)

    # temporarily remove the new tag if it is added already
    if new_tag in selected_image_dict[img_id][string_category]:
        index = (selected_image_dict[img_id][string_category]).index(new_tag)
        del selected_image_dict[img_id][string_category][index]

    # list of orderings
    temp_category_list = [selected_image_dict[img_id]["artist"], selected_image_dict[img_id]["character"], selected_image_dict[img_id]["species"], selected_image_dict[img_id]["general"], selected_image_dict[img_id]["meta"], selected_image_dict[img_id]["rating"]]
    category_order_dict = {"artist": 0, "character": 1, "species": 2, "general": 3, "meta": 4, "rating": 5}

    # determine the initial dictionary number
    current_dict_num = category_order_dict[string_category]

    # collect tag name which came before the new tag
    temp_tag_name = None
    # while category is empty check the previous one
    while(current_dict_num >= 0):
        if len(temp_category_list[current_dict_num]) > 0:
            # get name at end of category list
            temp_tag_name = temp_category_list[current_dict_num][-1]
            # break
            break
        current_dict_num -= 1

    # re-add new tag if not present
    if not new_tag in selected_image_dict[img_id][string_category]:
        selected_image_dict[img_id][string_category].append(new_tag)
    return temp_tag_name

# this method only effects ONE category at a time
# selected_image_dict has the form:
#     id -> {categories: [tags]}
#     type -> ext
def add_tag_changes(tag_string, apply_to_all_type_select_checkboxgroup, img_id, multi_select_ckbx_state, only_selected_state_object, images_selected_state):
    global auto_complete_config
    tag_list = tag_string.replace(" ", "").split(",")
    img_id = str(img_id)

    global all_images_dict
    global selected_image_dict

    global all_tags_ever_dict

    # find type of selected image
    temp_ext = None
    temp_all_images_dict_keys = list(all_images_dict.keys())
    if "searched" in temp_all_images_dict_keys:
        temp_all_images_dict_keys.remove("searched")
    for each_key in temp_all_images_dict_keys:
        if img_id in list(all_images_dict[each_key]):
            temp_ext = each_key
            break
    # reload the categories for the selected_image_dict
    if len(images_selected_state) == 0 and not multi_select_ckbx_state[0]:
        reload_selected_image_dict(temp_ext, img_id)

    # updates selected image ONLY when it ( IS ) specified AND its TYPE is specified for edits in "apply_to_all_type_select_checkboxgroup"
    if img_id and len(img_id) > 0 and selected_image_dict and (not apply_to_all_type_select_checkboxgroup or len(apply_to_all_type_select_checkboxgroup) == 0):
        # find image in searched : id
        if (selected_image_dict["type"] in list(all_images_dict['searched'].keys())) and (img_id in list(all_images_dict["searched"][selected_image_dict["type"]].keys())):
            for tag in tag_list:
                if not tag in all_images_dict["searched"][selected_image_dict["type"]][img_id]:
                    # get last tag in category
                    last_tag = get_insert_last_tags_name(categories_map[all_tags_ever_dict[tag]], selected_image_dict["type"], img_id, tag) # i.e. the tag before the new one
                    help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                    # get its index on the global list
                    glob_index = 0
                    if last_tag:
                        glob_index = (all_images_dict["searched"][selected_image_dict["type"]][img_id]).index(last_tag)
                        glob_index += 1 # puts the pointer at end of category list
                    all_images_dict["searched"][selected_image_dict["type"]][img_id].insert(glob_index, tag)

                    glob_index = (all_images_dict[selected_image_dict["type"]][img_id]).index(last_tag)
                    all_images_dict[selected_image_dict["type"]][img_id].insert(glob_index, tag)

                    if not img_id in auto_complete_config[selected_image_dict["type"]]:
                        auto_complete_config[selected_image_dict["type"]][img_id] = []
                    auto_complete_config[selected_image_dict["type"]][img_id].append(['+', tag, (glob_index)])

                    # create or increment category table AND frequency table for (all) tags
                    add_to_csv_dictionaries(categories_map[all_tags_ever_dict[tag]], tag) # add
        elif img_id in list(all_images_dict[selected_image_dict["type"]].keys()): # find image in ( TYPE ) : id
            for tag in tag_list:
                if not tag in all_images_dict[selected_image_dict["type"]][img_id]:
                    # get last tag in category
                    last_tag = get_insert_last_tags_name(categories_map[all_tags_ever_dict[tag]], selected_image_dict["type"], img_id, tag) # i.e. the tag before the new one
                    help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                    # get its index on the global list
                    glob_index = 0
                    if last_tag:
                        glob_index = (all_images_dict[selected_image_dict["type"]][img_id]).index(last_tag)
                        glob_index += 1  # puts the pointer at end of category list
                    all_images_dict[selected_image_dict["type"]][img_id].insert(glob_index, tag)

                    if not img_id in auto_complete_config[selected_image_dict["type"]]:
                        auto_complete_config[selected_image_dict["type"]][img_id] = []
                    auto_complete_config[selected_image_dict["type"]][img_id].append(['+', tag, (glob_index)])

                    # create or increment category table AND frequency table for (all) tags
                    add_to_csv_dictionaries(categories_map[all_tags_ever_dict[tag]], tag) # add
    if len(apply_to_all_type_select_checkboxgroup) > 0:
        if "searched" in apply_to_all_type_select_checkboxgroup: # edit searched and then all the instances of the respective types
            if multi_select_ckbx_state[0]:
                ##### returns index -> [ext, img_id]
                for index in images_selected_state:
                    ext, img_id = only_selected_state_object[index]
                    if ext in apply_to_all_type_select_checkboxgroup:
                        if img_id in list(all_images_dict["searched"][ext].keys()):
                            for tag in tag_list:
                                if not tag in all_images_dict["searched"][ext][img_id]:  # add tag
                                    # get last tag in category
                                    last_tag = get_insert_last_tags_name(categories_map[all_tags_ever_dict[tag]], ext, img_id,
                                                                         tag)  # i.e. the tag before the new one
                                    help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                                    # get its index on the global list
                                    glob_index = 0
                                    if last_tag:
                                        glob_index = (all_images_dict["searched"][ext][img_id]).index(last_tag)
                                        glob_index += 1  # puts the pointer at end of category list

                                    help.verbose_print(f"tag:\t\t{tag}")

                                    all_images_dict["searched"][ext][img_id].insert(glob_index, tag)

                                    all_images_dict[ext][img_id].insert(glob_index, tag)

                                    if not img_id in auto_complete_config[ext]:
                                        auto_complete_config[ext][img_id] = []
                                    auto_complete_config[ext][img_id].append(['+', tag, (glob_index)])

                                    # create or increment category table AND frequency table for (all) tags
                                    add_to_csv_dictionaries(categories_map[all_tags_ever_dict[tag]], tag)  # add
            else:
                for key_type in list(all_images_dict["searched"].keys()):
                    for img_id in list(all_images_dict["searched"][key_type].keys()):
                        for tag in tag_list:
                            if not tag in all_images_dict["searched"][key_type][img_id]: # add tag
                                # get last tag in category
                                last_tag = get_insert_last_tags_name(categories_map[all_tags_ever_dict[tag]], key_type, img_id, tag)  # i.e. the tag before the new one
                                help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                                # get its index on the global list
                                glob_index = 0
                                if last_tag:
                                    glob_index = (all_images_dict["searched"][key_type][img_id]).index(last_tag)
                                    glob_index += 1  # puts the pointer at end of category list

                                help.verbose_print(f"tag:\t\t{tag}")

                                all_images_dict["searched"][key_type][img_id].insert(glob_index, tag)

                                all_images_dict[key_type][img_id].insert(glob_index, tag)

                                if not img_id in auto_complete_config[key_type]:
                                    auto_complete_config[key_type][img_id] = []
                                auto_complete_config[key_type][img_id].append(['+', tag, (glob_index)])

                                # create or increment category table AND frequency table for (all) tags
                                add_to_csv_dictionaries(categories_map[all_tags_ever_dict[tag]], tag) # add
        else:
            if multi_select_ckbx_state[0]:
                ##### returns index -> [ext, img_id]
                for index in images_selected_state:
                    ext, img_id = only_selected_state_object[index]
                    if ext in apply_to_all_type_select_checkboxgroup:
                        if img_id in list(all_images_dict[ext].keys()):
                            for tag in tag_list:
                                if not tag in all_images_dict[ext][img_id]:
                                    # get last tag in category
                                    last_tag = get_insert_last_tags_name(categories_map[all_tags_ever_dict[tag]], ext, img_id,
                                                                         tag)  # i.e. the tag before the new one
                                    help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                                    # get its index on the global list
                                    glob_index = 0
                                    if last_tag:
                                        glob_index = (all_images_dict[ext][img_id]).index(last_tag)
                                        glob_index += 1  # puts the pointer at end of category list

                                    all_images_dict[ext][img_id].insert(glob_index, tag)

                                    if not img_id in auto_complete_config[ext]:
                                        auto_complete_config[ext][img_id] = []
                                    auto_complete_config[ext][img_id].append(['+', tag, (glob_index)])

                                    if "searched" in all_images_dict and ext in all_images_dict[
                                        "searched"] and img_id in all_images_dict["searched"][ext]:
                                        all_images_dict["searched"][ext][img_id].insert(glob_index, tag)

                                    # create or increment category table AND frequency table for (all) tags
                                    add_to_csv_dictionaries(categories_map[all_tags_ever_dict[tag]], tag)  # add
            else:
                for key_type in apply_to_all_type_select_checkboxgroup:
                    for img_id in list(all_images_dict[key_type].keys()):
                        for tag in tag_list:
                            if not tag in all_images_dict[key_type][img_id]:
                                # get last tag in category
                                last_tag = get_insert_last_tags_name(categories_map[all_tags_ever_dict[tag]], key_type, img_id, tag)  # i.e. the tag before the new one
                                help.verbose_print(f"LAST TAG IS:\t{last_tag}")

                                # get its index on the global list
                                glob_index = 0
                                if last_tag:
                                    glob_index = (all_images_dict[key_type][img_id]).index(last_tag)
                                    glob_index += 1  # puts the pointer at end of category list

                                all_images_dict[key_type][img_id].insert(glob_index, tag)

                                if not img_id in auto_complete_config[key_type]:
                                    auto_complete_config[key_type][img_id] = []
                                auto_complete_config[key_type][img_id].append(['+', tag, (glob_index)])

                                if "searched" in all_images_dict and key_type in all_images_dict["searched"] and img_id in all_images_dict["searched"][key_type]:
                                    all_images_dict["searched"][key_type][img_id].insert(glob_index, tag)

                                # create or increment category table AND frequency table for (all) tags
                                add_to_csv_dictionaries(categories_map[all_tags_ever_dict[tag]], tag) # add

    # find type of selected image
    temp_ext = None
    temp_all_images_dict_keys = list(all_images_dict.keys())
    if "searched" in temp_all_images_dict_keys:
        temp_all_images_dict_keys.remove("searched")
    for each_key in temp_all_images_dict_keys:
        if img_id in list(all_images_dict[each_key]):
            temp_ext = each_key
            break
    # reload the categories for the selected_image_dict
    reload_selected_image_dict(temp_ext, img_id)

    img_artist_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['artist'], value=[])
    img_character_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['character'], value=[])
    img_species_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['species'], value=[])
    img_general_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['general'], value=[])
    img_meta_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['meta'], value=[])
    img_rating_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['rating'], value=[])

    return img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group, \
           img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group

def remove_tag_changes(category_tag_checkbox_group, apply_to_all_type_select_checkboxgroup, img_id, multi_select_ckbx_state, only_selected_state_object, images_selected_state):
    global auto_complete_config
    global all_images_dict
    global selected_image_dict

    global all_tags_ever_dict

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
    temp_all_images_dict_keys = list(all_images_dict.keys())
    if "searched" in temp_all_images_dict_keys:
        temp_all_images_dict_keys.remove("searched")
    for each_key in temp_all_images_dict_keys:
        if img_id in list(all_images_dict[each_key]):
            temp_ext = each_key
            break
    # reload the categories for the selected_image_dict
    if len(images_selected_state) == 0 and not multi_select_ckbx_state[0]:
        reload_selected_image_dict(temp_ext, img_id)

    category_component = None
    # updates selected image ONLY when it ( IS ) specified AND its TYPE is specified for edits in "apply_to_all_type_select_checkboxgroup"
    if img_id and len(img_id) > 0 and selected_image_dict and selected_image_dict["type"] in apply_to_all_type_select_checkboxgroup:
        # update info for selected image
        for tag in tag_list:
            if tag in selected_image_dict[img_id][categories_map[all_tags_ever_dict[tag]]]:
                while tag in selected_image_dict[img_id][categories_map[all_tags_ever_dict[tag]]]:
                    selected_image_dict[img_id][categories_map[all_tags_ever_dict[tag]]].remove(tag)
        # update info for category components
        img_artist_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['artist'], value=[])
        img_character_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['character'], value=[])
        img_species_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['species'], value=[])
        img_general_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['general'], value=[])
        img_meta_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['meta'], value=[])
        img_rating_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['rating'], value=[])
        # help.verbose_print(
        #     f"selected_image_dict[img_id][string_category]:\t\t{selected_image_dict[img_id][string_category]}")
    elif img_id and len(img_id) > 0 and selected_image_dict and (not apply_to_all_type_select_checkboxgroup or len(apply_to_all_type_select_checkboxgroup) == 0):
        # update info for selected image
        for tag in tag_list:
            if tag in selected_image_dict[img_id][categories_map[all_tags_ever_dict[tag]]]:
                while tag in selected_image_dict[img_id][categories_map[all_tags_ever_dict[tag]]]:
                    selected_image_dict[img_id][categories_map[all_tags_ever_dict[tag]]].remove(tag)
        # update info for category components
        img_artist_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['artist'], value=[])
        img_character_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['character'], value=[])
        img_species_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['species'], value=[])
        img_general_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['general'], value=[])
        img_meta_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['meta'], value=[])
        img_rating_tag_checkbox_group = gr.update(choices=selected_image_dict[img_id]['rating'], value=[])
        # help.verbose_print(
        #     f"selected_image_dict[img_id][string_category]:\t\t{selected_image_dict[img_id][string_category]}")

        # find image in searched : id
        if (selected_image_dict["type"] in list(all_images_dict['searched'].keys())) and (img_id in list(all_images_dict["searched"][selected_image_dict["type"]].keys())):
            for tag in tag_list:
                if tag in all_images_dict["searched"][selected_image_dict["type"]][img_id]:
                    while tag in all_images_dict["searched"][selected_image_dict["type"]][img_id]:
                        all_images_dict["searched"][selected_image_dict["type"]][img_id].remove(tag)

                    while tag in all_images_dict[selected_image_dict["type"]][img_id]:
                        all_images_dict[selected_image_dict["type"]][img_id].remove(tag)

                        if not img_id in auto_complete_config[selected_image_dict["type"]]:
                            auto_complete_config[selected_image_dict["type"]][img_id] = []
                        auto_complete_config[selected_image_dict["type"]][img_id].append(['-', tag])

                    # create or increment category table AND frequency table for (all) tags
                    remove_to_csv_dictionaries(categories_map[all_tags_ever_dict[tag]], tag) # remove
        elif img_id in list(all_images_dict[selected_image_dict["type"]].keys()):  # find image in ( TYPE ) : id
            for tag in tag_list:
                if tag in all_images_dict[selected_image_dict["type"]][img_id]:
                    while tag in all_images_dict[selected_image_dict["type"]][img_id]:
                        all_images_dict[selected_image_dict["type"]][img_id].remove(tag)

                        if not img_id in auto_complete_config[selected_image_dict["type"]]:
                            auto_complete_config[selected_image_dict["type"]][img_id] = []
                        auto_complete_config[selected_image_dict["type"]][img_id].append(['-', tag])

                    # create or increment category table AND frequency table for (all) tags
                    remove_to_csv_dictionaries(categories_map[all_tags_ever_dict[tag]], tag) # remove

    if len(apply_to_all_type_select_checkboxgroup) > 0:
        if "searched" in apply_to_all_type_select_checkboxgroup:  # edit searched and then all the instances of the respective types
            if multi_select_ckbx_state[0]:
                ##### returns index -> [ext, img_id]
                for index in images_selected_state:
                    ext, img_id = only_selected_state_object[index]
                    if ext in apply_to_all_type_select_checkboxgroup:
                        if img_id in list(all_images_dict["searched"][ext].keys()):
                            for tag in tag_list:
                                if tag in all_images_dict["searched"][ext][img_id]:  # remove tag
                                    while tag in all_images_dict["searched"][ext][img_id]:
                                        all_images_dict["searched"][ext][img_id].remove(tag)

                                    while tag in all_images_dict[ext][img_id]:
                                        all_images_dict[ext][img_id].remove(tag)

                                        if not img_id in auto_complete_config[ext]:
                                            auto_complete_config[ext][img_id] = []
                                        auto_complete_config[ext][img_id].append(['-', tag])

                                    # create or increment category table AND frequency table for (all) tags
                                    remove_to_csv_dictionaries(categories_map[all_tags_ever_dict[tag]], tag)  # remove
            else:
                for key_type in list(all_images_dict["searched"].keys()):
                    for img_id in list(all_images_dict["searched"][key_type].keys()):
                        for tag in tag_list:
                            if tag in all_images_dict["searched"][key_type][img_id]:  # remove tag
                                while tag in all_images_dict["searched"][key_type][img_id]:
                                    all_images_dict["searched"][key_type][img_id].remove(tag)

                                while tag in all_images_dict[key_type][img_id]:
                                    all_images_dict[key_type][img_id].remove(tag)

                                    if not img_id in auto_complete_config[key_type]:
                                        auto_complete_config[key_type][img_id] = []
                                    auto_complete_config[key_type][img_id].append(['-', tag])

                                # create or increment category table AND frequency table for (all) tags
                                remove_to_csv_dictionaries(categories_map[all_tags_ever_dict[tag]], tag) # remove
        else:
            if multi_select_ckbx_state[0]:
                ##### returns index -> [ext, img_id]
                for index in images_selected_state:
                    ext, img_id = only_selected_state_object[index]
                    if ext in apply_to_all_type_select_checkboxgroup:
                        if img_id in list(all_images_dict[ext].keys()):
                            for tag in tag_list:
                                if tag in all_images_dict[ext][img_id]:
                                    while tag in all_images_dict[ext][img_id]:
                                        all_images_dict[ext][img_id].remove(tag)

                                        if not img_id in auto_complete_config[ext]:
                                            auto_complete_config[ext][img_id] = []
                                        auto_complete_config[ext][img_id].append(['-', tag])

                                    if "searched" in all_images_dict and ext in all_images_dict[
                                        "searched"] and img_id in all_images_dict["searched"][ext]:
                                        while tag in all_images_dict["searched"][ext][img_id]:
                                            all_images_dict["searched"][ext][img_id].remove(tag)

                                    # create or increment category table AND frequency table for (all) tags
                                    remove_to_csv_dictionaries(categories_map[all_tags_ever_dict[tag]], tag)  # remove
            else:
                for key_type in apply_to_all_type_select_checkboxgroup:
                    for img_id in list(all_images_dict[key_type].keys()):
                        for tag in tag_list:
                            if tag in all_images_dict[key_type][img_id]:
                                while tag in all_images_dict[key_type][img_id]:
                                    all_images_dict[key_type][img_id].remove(tag)

                                    if not img_id in auto_complete_config[key_type]:
                                        auto_complete_config[key_type][img_id] = []
                                    auto_complete_config[key_type][img_id].append(['-', tag])

                                if "searched" in all_images_dict and key_type in all_images_dict["searched"] and img_id in all_images_dict["searched"][key_type]:
                                    while tag in all_images_dict["searched"][key_type][img_id]:
                                        all_images_dict["searched"][key_type][img_id].remove(tag)

                                # create or increment category table AND frequency table for (all) tags
                                remove_to_csv_dictionaries(categories_map[all_tags_ever_dict[tag]], tag) # remove

    return img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group, \
           img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group

def get_category_name(tag):
    global all_tags_ever_dict
    if tag in all_tags_ever_dict:
        return categories_map[all_tags_ever_dict[tag]]
    else:
        return None

### if "searched" is selected in apply_to_all_type_select_checkboxgroup, then all SEARCHED images will be deleted!
def remove_images(apply_to_all_type_select_checkboxgroup, image_id, sort_images, sort_option, multi_select_ckbx_state, only_selected_state_object, images_selected_state):
    global all_images_dict
    global selected_image_dict
    image_id = str(image_id)

    if not "searched" in apply_to_all_type_select_checkboxgroup:
        if multi_select_ckbx_state[0] and len(apply_to_all_type_select_checkboxgroup) > 0:
            ##### returns index -> [ext, img_id]
            for index in images_selected_state:
                ext, img_id = only_selected_state_object[index]
                if ext in apply_to_all_type_select_checkboxgroup:
                    # iterate over all the tags for each image
                    for tag in all_images_dict[ext][img_id]:
                        category_key = get_category_name(tag)
                        if category_key:
                            # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
                            # edit csv dictionaries
                            remove_to_csv_dictionaries(category_key, tag)  # remove
                    del all_images_dict[ext][img_id]
                del only_selected_state_object[index]
            images_selected_state = []
        elif multi_select_ckbx_state[0] and len(images_selected_state) == 1:
            ##### returns index -> [ext, img_id]
            for index in images_selected_state:
                ext, img_id = only_selected_state_object[index]
                # iterate over all the tags for each image
                for tag in all_images_dict[ext][img_id]:
                    category_key = get_category_name(tag)
                    if category_key:
                        # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
                        # edit csv dictionaries
                        remove_to_csv_dictionaries(category_key, tag)  # remove
                del all_images_dict[ext][img_id]
                del only_selected_state_object[index]
            images_selected_state = []
        else:
            # remove single image ONLY
            if image_id and (selected_image_dict is not None):
                image_type = selected_image_dict["type"]
                if image_id in list(all_images_dict[image_type].keys()):
                    # remove tag count from csvs
                    category_keys = list(selected_image_dict[image_id].keys())
                    for category_key in category_keys:
                        for tag in selected_image_dict[image_id][category_key]:
                            # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
                            # edit csv dictionaries
                            remove_to_csv_dictionaries(category_key, tag) # remove
                    # delete image from dictionary
                    del all_images_dict[selected_image_dict["type"]][image_id]
                if (len(list(all_images_dict["searched"].keys())) > 0) and (image_id in list(all_images_dict["searched"][selected_image_dict["type"]].keys())):
                    del all_images_dict["searched"][selected_image_dict["type"]][image_id]
    else:
        if multi_select_ckbx_state[0]:
            ##### returns index -> [ext, img_id]
            for index in images_selected_state:
                ext, img_id = only_selected_state_object[index]
                if ext in apply_to_all_type_select_checkboxgroup:
                    # delete searched images and use the global dictionary to update the CSVs before deleting those as well
                    del all_images_dict["searched"][ext][img_id]
                    # iterate over all the tags for each image
                    for tag in all_images_dict[ext][img_id]:
                        category_key = get_category_name(tag)
                        if category_key:
                            # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
                            # edit csv dictionaries
                            remove_to_csv_dictionaries(category_key, tag)  # remove
                    del all_images_dict[ext][img_id]
                del only_selected_state_object[index]
            images_selected_state = []
        else:
            # remove all images that are "searched"
            for key_type in list(all_images_dict["searched"].keys()):
                if key_type in apply_to_all_type_select_checkboxgroup:
                    for img_id in list(all_images_dict["searched"][key_type].keys()):
                        # delete searched images and use the global dictionary to update the CSVs before deleting those as well
                        del all_images_dict["searched"][key_type][img_id]
                        # iterate over all the tags for each image
                        for tag in all_images_dict[key_type][img_id]:
                            category_key = get_category_name(tag)
                            if category_key:
                                # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
                                # edit csv dictionaries
                                remove_to_csv_dictionaries(category_key, tag) # remove
                        del all_images_dict[key_type][img_id]

    category_comp1 = gr.update(choices=[], value=[])
    category_comp2 = gr.update(choices=[], value=[])
    category_comp3 = gr.update(choices=[], value=[])
    category_comp4 = gr.update(choices=[], value=[])
    category_comp5 = gr.update(choices=[], value=[])
    category_comp6 = gr.update(choices=[], value=[])

    # gallery update
    images = update_search_gallery(sort_images, sort_option)
    gallery = gr.update(value=images, visible=True)
    # textbox update
    id_box = gr.update(value="")
    return category_comp1, category_comp2, category_comp3, category_comp4, category_comp5, category_comp6, gallery, id_box, only_selected_state_object, images_selected_state

def csv_persist_to_disk():
    tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                 settings_json["tag_count_list_folder"])
    # update csv stats files
    global artist_csv_dict, character_csv_dict, species_csv_dict, general_csv_dict, meta_csv_dict, rating_csv_dict, tags_csv_dict
    help.write_tags_to_csv(artist_csv_dict, os.path.join(tag_count_dir, "artist.csv"))
    help.write_tags_to_csv(character_csv_dict, os.path.join(tag_count_dir, "character.csv"))
    help.write_tags_to_csv(species_csv_dict, os.path.join(tag_count_dir, "species.csv"))
    help.write_tags_to_csv(general_csv_dict, os.path.join(tag_count_dir, "general.csv"))
    help.write_tags_to_csv(meta_csv_dict, os.path.join(tag_count_dir, "meta.csv"))
    help.write_tags_to_csv(rating_csv_dict, os.path.join(tag_count_dir, "rating.csv"))
    help.write_tags_to_csv(tags_csv_dict, os.path.join(tag_count_dir, "tags.csv"))

def save_tag_changes():
    global auto_complete_config
    # do a full save of all tags
    full_path_downloads = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                       settings_json["downloaded_posts_folder"])
    if not all_images_dict or not "png" in all_images_dict:
        raise ValueError('radio button not pressed i.e. image type button')

    help.verbose_print(f"++++++++++++++++++++++++++")
    temp_list = list(all_images_dict.keys())
    help.verbose_print(f"temp_list:\t\t{temp_list}")
    # if NONE: save self (selected_image)
    # if temp_list

    if "searched" in temp_list:
        temp_list.remove("searched")
        help.verbose_print(f"removing searched key")
        help.verbose_print(f"temp_list:\t\t{temp_list}")
    for ext in temp_list:
        full_path_gallery_type = os.path.join(full_path_downloads, settings_json[f"{ext}_folder"])
        for img_id in list(all_images_dict[ext]):
            full_path = os.path.join(full_path_gallery_type, f"{img_id}.txt")
            temp_tag_string = ",".join(all_images_dict[ext][img_id])
            help.write_tags_to_text_file(temp_tag_string, full_path)  # update img txt file
    # persist csv changes
    csv_persist_to_disk()

    add_current_images()
    auto_config_path = os.path.join(cwd, "auto_configs")
    temp_config_path = os.path.join(auto_config_path, auto_complete_config_name)
    help.update_JSON(auto_complete_config, temp_config_path)
    # display stats
    png_cnt, jpg_cnt, gif_cnt, total_imgs = get_saved_image_count()
    help.verbose_print(f"total_imgs:\t{total_imgs}")
    help.verbose_print(f"png_cnt:\t{png_cnt}")
    help.verbose_print(f"jpg_cnt:\t{jpg_cnt}")
    help.verbose_print(f"gif_cnt:\t{gif_cnt}")
    help.verbose_print(f"SAVE COMPLETE")

def save_image_changes():
    global auto_complete_config
    full_path_downloads = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                       settings_json["downloaded_posts_folder"])
    if not all_images_dict or not "png" in all_images_dict:
        raise ValueError('radio button not pressed i.e. image type button')
    help.verbose_print(f"++++++++++++++++++++++++++")
    temp_list = list(all_images_dict.keys())
    help.verbose_print(f"temp_list:\t\t{temp_list}")
    if "searched" in temp_list:
        temp_list.remove("searched")
        help.verbose_print(f"removing searched key")
        help.verbose_print(f"temp_list:\t\t{temp_list}")

    # persist csv changes
    csv_persist_to_disk()

    temp = '\\' if help.is_windows() else '/'
    for ext in temp_list:
        full_path_gallery_type = os.path.join(full_path_downloads, settings_json[f"{ext}_folder"])
        # type select
        images = [name.split(temp)[-1].split(".")[0] for name in glob.glob(os.path.join(full_path_gallery_type, f"*.{ext}"))] # getting the names of the files w.r.t. the directory
        for img_id in images:
            if not img_id in list(all_images_dict[ext]):
                # delete img & txt files
                os.remove(os.path.join(full_path_gallery_type, f"{img_id}.{ext}"))
                os.remove(os.path.join(full_path_gallery_type, f"{img_id}.txt"))
                if img_id in list(auto_complete_config[ext].keys()):
                    del auto_complete_config[ext][img_id]

    add_current_images()
    auto_config_path = os.path.join(cwd, "auto_configs")
    temp_config_path = os.path.join(auto_config_path, auto_complete_config_name)
    help.update_JSON(auto_complete_config, temp_config_path)
    # display stats
    png_cnt, jpg_cnt, gif_cnt, total_imgs = get_saved_image_count()
    help.verbose_print(f"total_imgs:\t{total_imgs}")
    help.verbose_print(f"png_cnt:\t{png_cnt}")
    help.verbose_print(f"jpg_cnt:\t{jpg_cnt}")
    help.verbose_print(f"gif_cnt:\t{gif_cnt}")
    help.verbose_print(f"SAVE COMPLETE")

def force_reload_images_and_csvs():
    global all_images_dict
    # clear searched dict
    if "searched" in all_images_dict:
        del all_images_dict["searched"]
        all_images_dict["searched"] = {}

    full_path_downloads = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                       settings_json["downloaded_posts_folder"])
    if not all_images_dict or len(all_images_dict.keys()) == 0:
        all_images_dict = help.merge_dict(os.path.join(full_path_downloads, settings_json[f"png_folder"]),
                                          os.path.join(full_path_downloads, settings_json[f"jpg_folder"]),
                                          os.path.join(full_path_downloads, settings_json[f"gif_folder"]))

    # populate the timekeeping dictionary
    initialize_posts_timekeeper()

    tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                 settings_json["tag_count_list_folder"])
    global is_csv_loaded
    is_csv_loaded = True
    global artist_csv_dict, character_csv_dict, species_csv_dict, general_csv_dict, meta_csv_dict, rating_csv_dict, tags_csv_dict
    artist_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "artist.csv"))
    character_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "character.csv"))
    species_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "species.csv"))
    general_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "general.csv"))
    meta_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "meta.csv"))
    rating_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "rating.csv"))
    tags_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "tags.csv"))


def load_images_and_csvs():
    global is_csv_loaded, all_images_dict
    if not is_csv_loaded or (not all_images_dict or len(all_images_dict.keys()) == 0):
        # clear searched dict
        if "searched" in all_images_dict:
            del all_images_dict["searched"]
            all_images_dict["searched"] = {}

        full_path_downloads = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                           settings_json["downloaded_posts_folder"])
        if not all_images_dict or len(all_images_dict.keys()) == 0:
            all_images_dict = help.merge_dict(os.path.join(full_path_downloads, settings_json[f"png_folder"]),
                                              os.path.join(full_path_downloads, settings_json[f"jpg_folder"]),
                                              os.path.join(full_path_downloads, settings_json[f"gif_folder"]))

        # populate the timekeeping dictionary
        initialize_posts_timekeeper()

        tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                     settings_json["tag_count_list_folder"])
        is_csv_loaded = True
        global artist_csv_dict, character_csv_dict, species_csv_dict, general_csv_dict, meta_csv_dict, rating_csv_dict, tags_csv_dict
        artist_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "artist.csv"))
        character_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "character.csv"))
        species_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "species.csv"))
        general_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "general.csv"))
        meta_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "meta.csv"))
        rating_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "rating.csv"))
        tags_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(tag_count_dir, "tags.csv"))

def remove_from_all(file_path, apply_to_all_type_select_checkboxgroup):
    global auto_complete_config
    # gather the tags
    all_tags = help.get_text_file_data(file_path, 1)
    all_tags = [x.rstrip('\n') for x in all_tags]
    help.verbose_print(f"all_tags:\t{all_tags}")

    # load the csvs if not already loaded and the image dictionaries
    load_images_and_csvs()

    all_keys_temp = list(all_images_dict.keys())
    search_flag = False
    all_keys_temp.remove("searched")
    if "searched" in apply_to_all_type_select_checkboxgroup:
        search_flag = True

    # update the csvs and global dictionaries
    searched_keys_temp = list(all_images_dict["searched"].keys())
    for tag in all_tags:
        category_key = get_category_name(tag)
        if category_key:
            # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
            # edit csv dictionaries
            remove_to_csv_dictionaries(category_key, tag) # remove
        # update all the image text files
        searched_ids_list = list(all_images_dict["searched"].keys())
        for img_type in all_keys_temp:
            searched_img_id_keys_temp = None
            if img_type in searched_ids_list:
                searched_img_id_keys_temp = list(all_images_dict["searched"][img_type].keys())
            else:
                searched_img_id_keys_temp = list(all_images_dict[img_type].keys())

            for every_image in list(all_images_dict[img_type].keys()):
                if tag in all_images_dict[img_type][every_image]:
                    while tag in all_images_dict[img_type][every_image]:
                        all_images_dict[img_type][every_image].remove(tag)
                        if search_flag and img_type in searched_keys_temp and every_image in searched_img_id_keys_temp:
                            if img_type in searched_ids_list:
                                all_images_dict["searched"][img_type][every_image].remove(tag)

                        if not every_image in auto_complete_config[img_type]:
                            auto_complete_config[img_type][every_image] = []
                        auto_complete_config[img_type][every_image].append(['-', tag])
    # persist changes
    csv_persist_to_disk()
    full_path_downloads = os.path.join(os.path.join(cwd, settings_json["batch_folder"]), settings_json["downloaded_posts_folder"])

    for ext in all_keys_temp:
        for img_id in list(all_images_dict[ext].keys()):
            full_path_gallery_type = os.path.join(full_path_downloads, settings_json[f"{ext}_folder"])
            full_path = os.path.join(full_path_gallery_type, f"{img_id}.txt")
            temp_tag_string = ",".join(all_images_dict[ext][img_id])
            help.write_tags_to_text_file(temp_tag_string, full_path)  # update img txt file

    add_current_images()
    auto_config_path = os.path.join(cwd, "auto_configs")
    temp_config_path = os.path.join(auto_config_path, auto_complete_config_name)
    help.update_JSON(auto_complete_config, temp_config_path)

    help.verbose_print("Done")

def replace_from_all(file_path, apply_to_all_type_select_checkboxgroup):
    global auto_complete_config
    # gather the (keyword, tag/s) pairs
    all_tags = help.get_text_file_data(file_path, 2)

    for i in range(0, len(all_tags)):
        all_tags[i][0] = all_tags[i][0].rstrip('\n')
        for j in range(0, len(all_tags[i][1])):
            all_tags[i][1][j] = all_tags[i][1][j].rstrip('\n')

    help.verbose_print(f"all_tags:\t{all_tags}")

    # load the csvs if not already loaded and the image dictionaries
    load_images_and_csvs()

    all_keys_temp = list(all_images_dict.keys())
    search_flag = False
    all_keys_temp.remove("searched")
    if "searched" in apply_to_all_type_select_checkboxgroup:
        search_flag = True

    # update the csvs
    searched_keys_temp = list(all_images_dict["searched"].keys())
    for tag, replacement_tags in all_tags:
        category_key = get_category_name(tag)
        if category_key:
            help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}\tand\treplacement_tags:\t{replacement_tags}")
            # edit csv dictionaries
            remove_to_csv_dictionaries(category_key, tag) # remove
        for replacement_tag in replacement_tags:
            category_key = get_category_name(replacement_tag)
            # "SKIP" (do not add into csvs) if None
            if category_key:
                add_to_csv_dictionaries(category_key, replacement_tag) # add
        # update all the image text files
        searched_ids_list = list(all_images_dict["searched"].keys())
        for img_type in all_keys_temp:
            searched_img_id_keys_temp = None
            if img_type in searched_ids_list:
                searched_img_id_keys_temp = list(all_images_dict["searched"][img_type].keys())
            else:
                searched_img_id_keys_temp = list(all_images_dict[img_type].keys())

            for every_image in list(all_images_dict[img_type].keys()):
                if tag in all_images_dict[img_type][every_image]:
                    # get index of keyword
                    index = (all_images_dict[img_type][every_image]).index(tag)
                    all_images_dict[img_type][every_image].remove(tag) ############ consider repeats present
                    if search_flag and img_type in searched_keys_temp and every_image in searched_img_id_keys_temp:
                        if img_type in searched_ids_list:
                            all_images_dict["searched"][img_type][every_image].remove(tag)

                    if not every_image in auto_complete_config[img_type]:
                        auto_complete_config[img_type][every_image] = []
                    auto_complete_config[img_type][every_image].append(['-', tag])

                    for i in range(0, len(replacement_tags)):
                        all_images_dict[img_type][every_image].insert((index + i), replacement_tags[i])
                        if search_flag and img_type in searched_keys_temp and every_image in searched_img_id_keys_temp:
                            if img_type in searched_ids_list:
                                all_images_dict["searched"][img_type][every_image].insert((index + i), replacement_tags[i])

                        if not every_image in auto_complete_config[img_type]:
                            auto_complete_config[img_type][every_image] = []
                        auto_complete_config[img_type][every_image].append(['+', replacement_tags[i], (index + i)])
    # persist changes
    csv_persist_to_disk()
    full_path_downloads = os.path.join(os.path.join(cwd, settings_json["batch_folder"]), settings_json["downloaded_posts_folder"])
    for ext in all_keys_temp:
        for img_id in list(all_images_dict[ext].keys()):
            full_path_gallery_type = os.path.join(full_path_downloads, settings_json[f"{ext}_folder"])
            full_path = os.path.join(full_path_gallery_type, f"{img_id}.txt")
            temp_tag_string = ",".join(all_images_dict[ext][img_id])
            help.write_tags_to_text_file(temp_tag_string, full_path)  # update img txt file

    add_current_images()
    auto_config_path = os.path.join(cwd, "auto_configs")
    temp_config_path = os.path.join(auto_config_path, auto_complete_config_name)
    help.update_JSON(auto_complete_config, temp_config_path)

    help.verbose_print("Done")

def prepend_with_keyword(keyword_search_text, prepend_text, prepend_option, apply_to_all_type_select_checkboxgroup):
    global auto_complete_config
    if not prepend_text or prepend_text == "":
        raise ValueError('REPLACEMENT TEXT and/or TAG/S MUST BE SPECIFIED!\n'
                         'tags can be removed with the text file and/or manually in the preview gallery tab.')

    prepend_tags = (prepend_text.replace(" ", "")).split(",")

    # load the csvs if not already loaded and the image dictionaries
    load_images_and_csvs()

    all_keys_temp = list(all_images_dict.keys())
    search_flag = False
    all_keys_temp.remove("searched")
    if "searched" in apply_to_all_type_select_checkboxgroup:
        search_flag = True

    # update the csvs
    if keyword_search_text and not keyword_search_text == "":
        category_key = get_category_name(keyword_search_text)
        if category_key:
            help.verbose_print(f"category_key:\t{category_key}\tand\tkeyword_search_text:\t{keyword_search_text}\tand\tprepend_tags:\t{prepend_tags}")
            # edit csv dictionaries
            # add_to_csv_dictionaries(category_key, keyword_search_text) # add
    for prepend_tag in prepend_tags:
        category_key = get_category_name(prepend_tag)
        # "SKIP" (do not add into csvs) if None
        if category_key:
            add_to_csv_dictionaries(category_key, prepend_tag) # add
    # update all the image text files
    searched_keys_temp = list(all_images_dict["searched"].keys())
    for img_type in all_keys_temp:
        searched_img_id_keys_temp = list(all_images_dict["searched"][img_type].keys())
        for every_image in list(all_images_dict[img_type].keys()):
            if keyword_search_text and not keyword_search_text == "":
                if keyword_search_text in all_images_dict[img_type][every_image]:
                    # get index of keyword
                    index = (all_images_dict[img_type][every_image]).index(keyword_search_text)
                    if prepend_option == "End":
                        index += 1
                    for i in range(0, len(prepend_tags)):
                        all_images_dict[img_type][every_image].insert((index + i), prepend_tags[i])
                        if search_flag and img_type in searched_keys_temp and every_image in searched_img_id_keys_temp:
                            all_images_dict["searched"][img_type][every_image].insert((index + i), prepend_tags[i])

                        if not every_image in auto_complete_config[img_type]:
                            auto_complete_config[img_type][every_image] = []
                        auto_complete_config[img_type][every_image].append(['+', prepend_tags[i], (index + i)])
            else:
                if prepend_option == "Start":
                    for i in range(0, len(prepend_tags)):
                        all_images_dict[img_type][every_image].insert(i, prepend_tags[i])
                        if search_flag and img_type in searched_keys_temp and every_image in searched_img_id_keys_temp:
                            all_images_dict["searched"][img_type][every_image].insert(i, prepend_tags[i])

                        if not every_image in auto_complete_config[img_type]:
                            auto_complete_config[img_type][every_image] = []
                        auto_complete_config[img_type][every_image].append(['+', prepend_tags[i], (i)])
                else:
                    for i in range(0, len(prepend_tags)):
                        all_images_dict[img_type][every_image].append(prepend_tags[i])
                        if search_flag and img_type in searched_keys_temp and every_image in searched_img_id_keys_temp:
                            all_images_dict["searched"][img_type][every_image].append(prepend_tags[i])

                        if not every_image in auto_complete_config[img_type]:
                            auto_complete_config[img_type][every_image] = []
                        auto_complete_config[img_type][every_image].append(['+', prepend_tags[i], (all_images_dict[img_type][every_image])-1])
    # persist changes
    csv_persist_to_disk()
    full_path_downloads = os.path.join(os.path.join(cwd, settings_json["batch_folder"]), settings_json["downloaded_posts_folder"])
    for ext in all_keys_temp:
        for img_id in list(all_images_dict[ext].keys()):
            full_path_gallery_type = os.path.join(full_path_downloads, settings_json[f"{ext}_folder"])
            full_path = os.path.join(full_path_gallery_type, f"{img_id}.txt")
            temp_tag_string = ",".join(all_images_dict[ext][img_id])
            help.write_tags_to_text_file(temp_tag_string, full_path)  # update img txt file

    add_current_images()
    auto_config_path = os.path.join(cwd, "auto_configs")
    temp_config_path = os.path.join(auto_config_path, auto_complete_config_name)
    help.update_JSON(auto_complete_config, temp_config_path)

    help.verbose_print("Done")

def check_to_reload_auto_complete_config(optional_path=None):
    global auto_complete_config, auto_complete_config_name
    temp_config_path = ""
    if not optional_path or optional_path == "":
        if not settings_json["batch_folder"] in auto_complete_config_name:
            auto_config_path = os.path.join(cwd, "auto_configs")
            auto_complete_config_name = f"auto_complete_{settings_json['batch_folder']}.json"

            temp_config_path = os.path.join(auto_config_path, auto_complete_config_name)
            if not os.path.exists(auto_config_path):
                os.makedirs(auto_config_path)
            # load if data present / create if file not yet created
            auto_complete_config = help.load_session_config(temp_config_path)
    else:
        if not settings_json["batch_folder"] in optional_path:
            help.eprint("CURRENT LOADED BATCH FOLDER NOT PRESENT IN SPECIFIED PATH!!!")
            auto_config_path = os.path.join(cwd, "auto_configs")
            temp = '\\' if help.is_windows() else '/'
            auto_complete_config_name = optional_path.split(temp)[-1]

            temp_config_path = os.path.join(auto_config_path, auto_complete_config_name)
            if not os.path.exists(auto_config_path):
                os.makedirs(auto_config_path)
            # load if data present / create if file not yet created
            auto_complete_config = help.load_session_config(temp_config_path)

    # if empty add default entries
    if not auto_complete_config:
        auto_complete_config = {'png': {}, 'jpg': {}, 'gif': {}}
        help.update_JSON(auto_complete_config, temp_config_path)

def filter_out():
    global all_images_dict
    global auto_complete_config
    temp_key_list = list(all_images_dict.keys())
    temp_tag_freq_table = {}

    if "searched" in temp_key_list:
        for ext in list(all_images_dict["searched"].keys()):
            for img_id in list(all_images_dict["searched"][ext].keys()):
                if not img_id in list(auto_complete_config[ext].keys()):
                    # generate frequency table for images being removed
                    # no frequency table here to prevent duplicates
                    # delete entry
                    del all_images_dict["searched"][ext][img_id]
        temp_key_list.remove("searched")

    for ext in temp_key_list:
        for img_id in list(all_images_dict[ext].keys()):
            if not img_id in list(auto_complete_config[ext].keys()):
                # generate frequency table for images being removed
                for tag in all_images_dict[ext][img_id]:
                    if not tag in list(temp_tag_freq_table.keys()):
                        temp_tag_freq_table[tag] = 1
                    else:
                        temp_tag_freq_table[tag] += 1
                # delete entry
                del all_images_dict[ext][img_id]

    # remove all tags from the csvs
    for tag in list(temp_tag_freq_table.keys()):
        category_key = get_category_name(tag)
        if category_key:
            # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
            # edit csv dictionaries
            remove_to_csv_dictionaries(category_key, tag, temp_tag_freq_table[tag])
    #persist
    csv_persist_to_disk()

###
# update_per_image -> ['-', tag] or ['+', tag, index]
###
def apply_stack_changes(progress=gr.Progress()):
    global all_images_dict
    global auto_complete_config
    temp_key_list = list(all_images_dict.keys())
    temp_tag_freq_table = {}

    if "searched" in temp_key_list:
        # clear searched dict
        del all_images_dict["searched"]
        all_images_dict["searched"] = {}
        temp_key_list.remove("searched")

    for ext in temp_key_list:
        valid_images = list(auto_complete_config[ext].keys())
        progress(0, desc="Applying Tag Filters...")
        for i in progress.tqdm(range(0,len(valid_images),1), desc=f"{ext}:\tTag Filtering Progress"):
            img_id = valid_images[i]

            for update in auto_complete_config[ext][img_id]:
                if '-' in update: # remove
                    tag = update[-1]
                    # remove tag
                    all_images_dict[ext][img_id].remove(tag)
                    if not tag in list(temp_tag_freq_table.keys()):
                        temp_tag_freq_table[tag] = -1
                    else:
                        temp_tag_freq_table[tag] -= 1
                else: # add
                    tag = update[1]
                    index = update[-1]
                    # add tag
                    all_images_dict[ext][img_id].insert(index, tag)
                    if not tag in list(temp_tag_freq_table.keys()):
                        temp_tag_freq_table[tag] = 1
                    else:
                        temp_tag_freq_table[tag] += 1

        # remove invalid images
        ext_all_images = list(all_images_dict[ext].keys())
        progress(0, desc="Applying Image Filters...")
        for i in progress.tqdm(range(len(ext_all_images)-1, -1, -1), desc=f"{ext}:\tImage Filtering Progress"):
            img_id = ext_all_images[i]

            if not img_id in valid_images:
                # remove tags
                for tag in all_images_dict[ext][img_id]:
                    if not tag in list(temp_tag_freq_table.keys()):
                        temp_tag_freq_table[tag] = -1
                    else:
                        temp_tag_freq_table[tag] -= 1
                # remove image
                del all_images_dict[ext][img_id]

    # create an add and remove frequency table
    positive_table = {}
    negative_table = {}
    for tag in list(temp_tag_freq_table.keys()):
        if temp_tag_freq_table[tag] > 0:
            positive_table[tag] = temp_tag_freq_table[tag]
        elif temp_tag_freq_table[tag] < 0:
            negative_table[tag] = abs(temp_tag_freq_table[tag]) # make positive
    # add to csvs
    for tag in list(positive_table.keys()):
        category_key = get_category_name(tag)
        if category_key:
            # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
            add_to_csv_dictionaries(category_key, tag, positive_table[tag])
    # remove to csvs
    for tag in list(negative_table.keys()):
        category_key = get_category_name(tag)
        if category_key:
            # help.verbose_print(f"category_key:\t{category_key}\tand\ttag:\t{tag}")
            remove_to_csv_dictionaries(category_key, tag, negative_table[tag])

    #persist
    csv_persist_to_disk()
    full_path_downloads = os.path.join(os.path.join(cwd, settings_json["batch_folder"]), settings_json["downloaded_posts_folder"])
    for ext in list(all_images_dict.keys()):
        ext_all_images = list(all_images_dict[ext].keys())
        progress(0, desc="Saving Changes...")
        for i in progress.tqdm(range(0, len(ext_all_images), 1), desc=f"{ext}:\tSaving Changes Progress"):
            img_id = ext_all_images[i]
            full_path_gallery_type = os.path.join(full_path_downloads, settings_json[f"{ext}_folder"])
            full_path = os.path.join(full_path_gallery_type, f"{img_id}.txt")
            temp_tag_string = ",".join(all_images_dict[ext][img_id])
            help.write_tags_to_text_file(temp_tag_string, full_path)  # update img txt file

    # display stats
    png_cnt, jpg_cnt, gif_cnt, total_imgs = get_saved_image_count()
    help.verbose_print(f"total_imgs:\t{total_imgs}")
    help.verbose_print(f"png_cnt:\t{png_cnt}")
    help.verbose_print(f"jpg_cnt:\t{jpg_cnt}")
    help.verbose_print(f"gif_cnt:\t{gif_cnt}")
    help.verbose_print("Done")
    return gr.update(interactive=False, visible=False)

def auto_config_apply(images_full_change_dict_textbox, progress=gr.Progress()):
    global auto_complete_config
    if len(images_full_change_dict_textbox) > 0 and auto_complete_config and ((len(list(auto_complete_config['png'].keys())) > 0) or (len(list(auto_complete_config['jpg'].keys())) > 0) or (len(list(auto_complete_config['gif'].keys())) > 0)): # if file is empty DO NOT RUN
        # load correct config
        check_to_reload_auto_complete_config(images_full_change_dict_textbox)

        # load the csvs if not already loaded and the image dictionaries
        load_images_and_csvs()

        # filter out invalid images & update CSVs
        # filter_out()

        # apply every in order image change & remove invalid images & update CSVs & save image changes
        return apply_stack_changes(progress)
    else:
        raise ValueError('no path name specified | no config created | config empty')

def download_repos(repo_download_releases_only, repo_download_checkbox_group, release_assets_checkbox_group, repo_download_radio):
    help.download_repos(repo_download_releases_only, repo_download_checkbox_group, release_assets_checkbox_group, repo_download_radio)

def reload_release_options(repo_download_releases_only):
    if repo_download_releases_only:
        # make visible the radio options & hide the repo_download_checkbox_group options, repo_specific_release_options, and button
        repo_download_checkbox_group = gr.update(visible=False)
        release_options_radio = gr.update(visible=False)
        repo_download_button = gr.update(visible=False)
        release_assets_checkbox_group = gr.update(visible=False)
        repo_download_radio = gr.update(visible=True)
        return repo_download_checkbox_group, repo_download_radio, release_options_radio, repo_download_button, release_assets_checkbox_group
    else:
        # make visible the repo_download_checkbox_group options & button and hide the radio options & repo_specific_release_options
        repo_download_checkbox_group = gr.update(visible=True)
        release_options_radio = gr.update(value=[], visible=False)
        repo_download_button = gr.update(visible=True)
        repo_download_radio = gr.update(visible=False)
        release_assets_checkbox_group = gr.update(visible=False)
        return repo_download_checkbox_group, repo_download_radio, release_options_radio, repo_download_button, release_assets_checkbox_group

def get_repo_releases(repo_download_radio, event_data: gr.SelectData):
    global repo_release_urls
    repo_release_urls = {}
    release_options_radio_list, repo_release_urls = help.get_repo_releases(event_data)
    release_options_radio = gr.update(choices=release_options_radio_list, visible=True, value=[])
    return release_options_radio

def get_repo_assets(release_options_radio, event_data: gr.SelectData):
    global repo_release_urls
    # get header text
    header_text = (event_data.value)
    # get assets available
    help.verbose_print(f"repo_release_urls[header_text]:\t{repo_release_urls[header_text]}")
    all_assets = repo_release_urls[header_text]
    help.verbose_print(f"all_assets:\t{all_assets}")

    repo_download_button = gr.update(visible=True)
    release_assets_checkbox_group = gr.update(choices=all_assets, visible=True)
    return repo_download_button, release_assets_checkbox_group

def download_models(model_download_types, model_download_checkbox_group, tagging_model_download_types, nested_model_links_checkbox_group):
    global auto_tag_models
    auto_tag_models = help.download_models(model_download_types, model_download_checkbox_group, tagging_model_download_types, nested_model_links_checkbox_group)
    model_download_types = gr.update(value=None)
    tagging_model_download_types = gr.update(value=None)
    nested_model_links_checkbox_group = gr.update(value=None)
    return model_download_types, tagging_model_download_types, nested_model_links_checkbox_group

def show_model_downloads_options(model_download_types, event_data: gr.SelectData):
    model_download_checkbox_group = gr.update(choices=help.get_model_names(event_data.value), visible=True)
    model_download_button = gr.update(visible=True)
    nested_model_links_checkbox_group = gr.update(visible=True)
    return model_download_checkbox_group, model_download_button, nested_model_links_checkbox_group

def show_nested_fluffyrock_models(nested_model_links_checkbox_group):
    model_download_checkbox_group = gr.update(visible=True)
    model_download_button = gr.update(visible=True)
    nested_model_links_checkbox_group = gr.update(visible=True, choices=help.get_nested_fluffyrock_models(nested_model_links_checkbox_group))
    return model_download_checkbox_group, model_download_button, nested_model_links_checkbox_group

def set_ckbx_state(select_multiple_images_checkbox, multi_select_ckbx_state): # UI boolean component, JSON boolean component wrapped in a list
    multi_select_ckbx_state = [select_multiple_images_checkbox]
    return multi_select_ckbx_state

def make_visible():
    return gr.update(visible=True)

def load_model(model_name, use_cpu, event_data: gr.SelectData):
    global autotagmodel
    if autotagmodel is None:
        folder_path = os.path.join(cwd, settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, settings_json["png_folder"])
        tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                             settings_json["tag_count_list_folder"])
        autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir)
        help.check_requirements()

    model_path = ""
    model_name = ""
    if "Z3D" in event_data.value:
        model_path = os.path.join(os.getcwd(), 'Z3D-E621-Convnext')
        model_name = "Z3D-E621-Convnext.onnx"
    elif "fluff" in (event_data.value).lower():
        model_path = os.path.join(os.getcwd(), 'Fluffusion-AutoTag')
        model_name = "Fluffusion-AutoTag.pb"

    autotagmodel.load_model(model_dir=model_path, model_name=model_name, use_cpu=use_cpu)
    help.verbose_print(f"model loaded using cpu={use_cpu}")

# def re_load_model(model_name, use_cpu):
#     global autotagmodel
#     if autotagmodel is None:
#         folder_path = os.path.join(cwd, settings_json["batch_folder"])
#         folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
#         folder_path = os.path.join(folder_path, settings_json["png_folder"])
#         tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
#                                              settings_json["tag_count_list_folder"])
#         autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir)
#         help.check_requirements()
#
#     autotagmodel.load_model(model_name=model_name, use_cpu=use_cpu)
#     help.verbose_print(f"model reloaded using cpu={use_cpu}")

def set_threshold(threshold):
    global autotagmodel, all_predicted_confidences, all_predicted_tags
    if autotagmodel is None:
        folder_path = os.path.join(cwd, settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, settings_json["png_folder"])
        tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                             settings_json["tag_count_list_folder"])
        autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir)
        help.check_requirements()

    temp_confids = None
    temp_tags = None
    if len(all_predicted_tags) > 0:
        temp_confids = copy.deepcopy(all_predicted_confidences)
        temp_tags = copy.deepcopy(all_predicted_tags)
        keys = list(temp_confids.keys())
        for key in keys:
            if temp_confids[key] <= (float(threshold) / 100.0):
                del temp_confids[key]
                temp_tags.remove(key)

    autotagmodel.set_threshold(thresh=threshold)
    help.verbose_print(f"new threshold set:\t{(float(threshold) / 100.0)}")
    return gr.update(value=temp_confids), gr.update(choices=temp_tags)

def load_images(images_path, image_mode_choice_state):
    global autotagmodel
    if autotagmodel is None:
        folder_path = os.path.join(cwd, settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, settings_json["png_folder"])
        tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                             settings_json["tag_count_list_folder"])
        autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir)
        help.check_requirements()
    image_mode_choice_state = ""
    if images_path:
        help.verbose_print(f"images_path:\t{images_path}")

        if isinstance(images_path, list) and len(images_path) > 1:
            names = []
            for path in images_path:
                help.verbose_print(f"path:\t{path}")
                help.verbose_print(f"path.name:\t{path.name}")
                names.append(path.name)
            autotagmodel.set_data(train_data_dir=names, single_image=False)
            image_mode_choice_state = 'Batch'
        else:
            if isinstance(images_path, list):
                images_path = images_path[0]
            help.verbose_print(f"images_path:\t{images_path}")
            help.verbose_print(f"images_path.name:\t{images_path.name}")

            autotagmodel.set_data(train_data_dir=images_path.name, single_image=True)
            image_mode_choice_state = 'Single'
    help.verbose_print(f"images loaded")
    return image_mode_choice_state

def update_image_mode(image_mode_choice_dropdown, event_data: gr.SelectData):
    global autotagmodel
    if autotagmodel is None:
        folder_path = os.path.join(cwd, settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, settings_json["png_folder"])
        tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                             settings_json["tag_count_list_folder"])
        autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir)
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

def make_menus_visible(crop_or_resize_radio):
    if crop_or_resize_radio.lower() == 'crop':
        return gr.update(visible=True), gr.update(visible=True)
    else:
        return gr.update(visible=False, value=None), gr.update(visible=False, value=None)
def set_square_size(square_image_edit_slider):
    global autotagmodel
    if autotagmodel is None:
        folder_path = os.path.join(cwd, settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, settings_json["png_folder"])
        tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                             settings_json["tag_count_list_folder"])
        autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir)
        help.check_requirements()
    autotagmodel.set_image_size(crop_size=square_image_edit_slider)
    help.verbose_print(f"new crop/resize dim/s set")
def set_crop_or_resize(crop_or_resize_radio):
    global autotagmodel
    if autotagmodel is None:
        folder_path = os.path.join(cwd, settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, settings_json["png_folder"])
        tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                             settings_json["tag_count_list_folder"])
        autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir)
        help.check_requirements()
    help.verbose_print(f"set crop or resize")
    if autotagmodel:
        autotagmodel.set_crop_or_resize(crop_or_resize_radio)
def set_landscape_square_crop(landscape_crop_dropdown, event_data: gr.SelectData):
    global autotagmodel
    if autotagmodel is None:
        folder_path = os.path.join(cwd, settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, settings_json["png_folder"])
        tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                             settings_json["tag_count_list_folder"])
        autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir)
        help.check_requirements()
    help.verbose_print(f"set landscape crop")
    if autotagmodel:
        autotagmodel.set_landscape_square_crop(event_data.value)
def set_portrait_square_crop(portrait_crop_dropdown, event_data: gr.SelectData):
    global autotagmodel
    if autotagmodel is None:
        folder_path = os.path.join(cwd, settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, settings_json["png_folder"])
        tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                             settings_json["tag_count_list_folder"])
        autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir)
        help.check_requirements()
    help.verbose_print(f"set portrait crop")
    if autotagmodel:
        autotagmodel.set_portrait_square_crop(event_data.value)
def set_write_tag_opts(event_data: gr.SelectData):
    global autotagmodel
    if autotagmodel is None:
        folder_path = os.path.join(cwd, settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, settings_json["png_folder"])
        tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                             settings_json["tag_count_list_folder"])
        autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir)
        help.check_requirements()
    autotagmodel.set_write_tag_opts(event_data.value)
    help.verbose_print(f"set write opts:\t{event_data.value}")
def set_use_tag_opts_radio(event_data: gr.SelectData):
    global autotagmodel
    if autotagmodel is None:
        folder_path = os.path.join(cwd, settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, settings_json["png_folder"])
        tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                             settings_json["tag_count_list_folder"])
        autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir)
        help.check_requirements()
    autotagmodel.set_use_tag_opts(event_data.value)
    help.verbose_print(f"set use opts:\t{event_data.value}")
def set_image_with_tag_path_textbox(image_with_tag_path_textbox):
    global autotagmodel
    if autotagmodel is None:
        folder_path = os.path.join(cwd, settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, settings_json["png_folder"])
        tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                             settings_json["tag_count_list_folder"])
        autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir)
        help.check_requirements()
    help.verbose_print(f"setting path to data origin")
    autotagmodel.set_image_with_tag_path_textbox(image_with_tag_path_textbox)
def set_copy_mode_ckbx(copy_mode_ckbx):
    global autotagmodel
    if autotagmodel is None:
        folder_path = os.path.join(cwd, settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, settings_json["png_folder"])
        tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                             settings_json["tag_count_list_folder"])
        autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir)
        help.check_requirements()
    autotagmodel.set_copy_mode_ckbx(copy_mode_ckbx)
    help.verbose_print(f"set copy")

def interrogate_images(image_mode_choice_state, confidence_threshold_slider):
    global all_tags_ever_dict
    global autotagmodel, all_predicted_confidences, all_predicted_tags
    generate_all_dirs()

    folder_path = os.path.join(cwd, settings_json["batch_folder"])
    folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
    folder_path = os.path.join(folder_path, settings_json["png_folder"])
    tag_count_dir = os.path.join(os.path.join(cwd, settings_json["batch_folder"]),
                                 settings_json["tag_count_list_folder"])

    if autotagmodel is None:
        autotagmodel = autotag.AutoTag(dest_folder=folder_path, tag_folder=tag_count_dir)
        help.check_requirements()
    image_confidence_values = None
    image_generated_tags = None
    image_preview_pil = None
    help.verbose_print(f"image_mode_choice_state:\t{image_mode_choice_state}")

    if 'single' == image_mode_choice_state.lower():
        autotagmodel.interrogate(single_image=True, all_tags_ever_dict=all_tags_ever_dict)
        image_confidence_values, image_generated_tags, image_preview_pil = autotagmodel.get_predictions(True)
    else:
        autotagmodel.interrogate(single_image=False, all_tags_ever_dict=all_tags_ever_dict)
        _, _, _ = autotagmodel.get_predictions(False)

    if image_confidence_values is None and image_generated_tags is None and image_preview_pil is None:
        return gr.update(value={}), gr.update(choices=[]), gr.update(value=None)

    all_predicted_confidences = image_confidence_values
    all_predicted_tags = image_generated_tags

    temp_confids = copy.deepcopy(all_predicted_confidences)
    temp_tags = copy.deepcopy(all_predicted_tags)
    help.verbose_print(f"getting results")
    help.verbose_print(f"Removing NON-E6 tags")

    keys = list(temp_confids.keys())
    for key in keys:
        if not key in all_tags_ever_dict or image_confidence_values[key] <= (float(confidence_threshold_slider)/100.0):
            del temp_confids[key]
            temp_tags.remove(key)

    if image_preview_pil is not None:
        print("UPDATING IMAGE PREVIEW")
        image_preview_pil = np.array(image_preview_pil)#[0]
        image_preview_pil = image_preview_pil[:, :, ::-1] # BGR -> RGB
        image_preview_pil = Image.fromarray(np.uint8(image_preview_pil))#*255#cm.gist_earth()
        image_preview_pil = gr.update(value=image_preview_pil)
    else:
        image_preview_pil = gr.update()

    # force reload csvs and global image dictionaries
    force_reload_images_and_csvs()

    return gr.update(value=temp_confids), gr.update(choices=temp_tags), image_preview_pil

# also creates an empty tag file for the image file if there isn't one already
def save_custom_images(image_mode_choice_state, image_with_tag_path_textbox, copy_mode_ckbx):
    global autotagmodel, all_predicted_confidences, all_predicted_tags
    generate_all_dirs()

    all_paths = None
    try:
        all_paths = autotagmodel.get_dataset().get_image_paths()
    except AttributeError:
        all_paths = glob.glob(os.path.join(image_with_tag_path_textbox, f"*.jpg")) + \
                    glob.glob(os.path.join(image_with_tag_path_textbox, f"*.png")) + \
                    glob.glob(os.path.join(image_with_tag_path_textbox, f"*.gif"))

    help.verbose_print(f"all image paths to save:\t{all_paths}")
    help.verbose_print(f"image_with_tag_path_textbox:\t{image_with_tag_path_textbox}")
    images_path = all_paths
    if (image_with_tag_path_textbox is None or not len(image_with_tag_path_textbox) > 0 or (images_path is None or not len(images_path) > 0)):
        raise ValueError("Cannot complete Operation without completing fields: (write tag options / use tag options / path to files / images_path)")

    if copy_mode_ckbx: # caches images for gallery tab & persists to disk where the others are located
        temp = '\\' if help.is_windows() else '/'
        folder_path = os.path.join(cwd, settings_json["batch_folder"])
        folder_path = os.path.join(folder_path, settings_json["downloaded_posts_folder"])
        folder_path = os.path.join(folder_path, settings_json["png_folder"])
        if image_mode_choice_state.lower() == 'single':
            images_path = images_path[0]
            name = (images_path).split(temp)[-1]
            help.copy_over_imgs(os.path.join(image_with_tag_path_textbox, name), os.path.join(folder_path, name), 'single')
        else:
            help.copy_over_imgs(image_with_tag_path_textbox, folder_path, 'batch')
    image_confidence_values = {}
    image_generated_tags = []
    image_preview_pil = None
    image_generated_tags_prompt_builder_textbox = ""
    return gr.update(value=image_confidence_values), gr.update(choices=image_generated_tags), gr.update(value=image_preview_pil), gr.update(value=image_generated_tags_prompt_builder_textbox)

def save_custom_tags(image_mode_choice_state, image_with_tag_path_textbox, any_selected_tags):
    global autotagmodel, all_predicted_tags
    generate_all_dirs()

    all_paths = autotagmodel.get_dataset().get_image_paths()
    images_path = all_paths
    if (image_with_tag_path_textbox is None or not len(image_with_tag_path_textbox) > 0 or (
            images_path is None or not len(images_path) > 0)):
        raise ValueError("Cannot complete Operation without completing fields: (write tag options / use tag options / path to files / images_path)")

    if image_mode_choice_state.lower() == 'single':
        autotagmodel.save_tags(single_image=True, any_selected_tags=any_selected_tags, all_tags_ever_dict=all_tags_ever_dict)
    elif image_mode_choice_state.lower() == 'batch':
        autotagmodel.save_tags(single_image=False, any_selected_tags=any_selected_tags, all_tags_ever_dict=all_tags_ever_dict)

    image_confidence_values = {}
    image_generated_tags = []
    image_preview_pil = None
    image_generated_tags_prompt_builder_textbox = ""
    return gr.update(value=image_confidence_values), gr.update(choices=image_generated_tags), gr.update(value=image_preview_pil), gr.update(value=image_generated_tags_prompt_builder_textbox)

def prompt_string_builder(use_tag_opts_radio, any_selected_tags, threshold):
    global all_predicted_tags, all_predicted_confidences
    use_tag_opts = ['Use All', 'Use All above Threshold', 'Manually Select']

    image_generated_tags_prompt_builder_textbox = gr.update(value="")
    if (all_predicted_tags is not None and all_predicted_confidences is not None) and \
            (len(all_predicted_tags) > 0 and len(all_predicted_confidences) > 0):
        if use_tag_opts_radio is not None and len(use_tag_opts_radio) > 0:
            if use_tag_opts_radio in use_tag_opts[1]:
                temp_confids = None
                temp_tags = None
                if len(all_predicted_tags) > 0:
                    temp_confids = copy.deepcopy(all_predicted_confidences)
                    temp_tags = copy.deepcopy(all_predicted_tags)
                    keys = list(temp_confids.keys())
                    for key in keys:
                        if temp_confids[key] <= (float(threshold) / 100.0):
                            del temp_confids[key]
                            temp_tags.remove(key)
                image_generated_tags_prompt_builder_textbox.update(value=", ".join(temp_tags))
            elif use_tag_opts_radio in use_tag_opts[0]:
                image_generated_tags_prompt_builder_textbox.update(value=", ".join(copy.deepcopy(all_predicted_tags)))
            elif use_tag_opts_radio in use_tag_opts[2]:
                image_generated_tags_prompt_builder_textbox.update(value=", ".join(any_selected_tags))
    return image_generated_tags_prompt_builder_textbox

def unload_component(value=None):
    return gr.update(value=value)

def refresh_model_list():
    if not "Z3D-E621-Convnext" in auto_tag_models and os.path.exists(os.path.join(os.getcwd(), 'Z3D-E621-Convnext')) \
            and os.path.exists(
        os.path.join(os.path.join(os.getcwd(), 'Z3D-E621-Convnext'), 'Z3D-E621-Convnext.onnx')):
        auto_tag_models.append('Z3D-E621-Convnext')
    if not "Fluffusion-AutoTag" in auto_tag_models and os.path.exists(
            os.path.join(os.getcwd(), 'Fluffusion-AutoTag')) \
            and os.path.exists(
        os.path.join(os.path.join(os.getcwd(), 'Fluffusion-AutoTag'), 'Fluffusion-AutoTag.pb')):
        auto_tag_models.append('Fluffusion-AutoTag')
    model_choice_dropdown = gr.update(choices=auto_tag_models)
    return model_choice_dropdown

def gen_tags_list(reference_model_tags_file):
    help.convert_to_list_file(reference_model_tags_file)
    help.verbose_print(f"done")

def gen_tags_diff_list(reference_model_tags_file):
    df_keep = pd.read_csv(reference_model_tags_file)
    first_column_keep = df_keep.iloc[:, 0]
    first_column_keep = first_column_keep.iloc[1:]
    set_keep = set(first_column_keep)

    tags_current_path = os.path.join(os.getcwd(), str(settings_json["batch_folder"]), str(settings_json["tag_count_list_folder"]), "tags.csv")
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

'''
##################################################################################################################################
#######################################################     GUI BLOCKS     #######################################################
##################################################################################################################################
'''

def build_ui():
    with gr.Blocks(css=f"{css_.preview_hide_rule} {css_.refresh_aspect_btn_rule} {css_.trim_row_length} {css_.trim_markdown_length} "
                       f"{css_.thumbnail_colored_border_css} {css_.refresh_models_btn_rule}"
                       f"{css_.green_button_css} {css_.red_button_css}") as demo:# {css_.gallery_fix_height}
        with gr.Tab("General Config"):
            with gr.Row():
                config_save_var0 = gr.Button(value="Apply & Save Settings", variant='primary')
            gr.Markdown(md_.general_config)
            with gr.Row():
                with gr.Column():
                    batch_folder = gr.Textbox(lines=1, label='Path to Batch Directory', value=settings_json["batch_folder"])
                with gr.Column():
                    resized_img_folder = gr.Textbox(lines=1, label='Path to Resized Images', value=settings_json["resized_img_folder"])
                with gr.Column():
                    proxy_value = ""
                    if not "proxy_url" in settings_json:
                        settings_json["proxy_url"] = proxy_value
                    proxy_url_textbox = gr.Textbox(lines=1, label='(Optional Proxy URL)', value=settings_json["proxy_url"])
            with gr.Row():
                tag_sep = gr.Textbox(lines=1, label='Tag Seperator/Delimeter', value=settings_json["tag_sep"])
                tag_order_format = gr.Textbox(lines=1, label='Tag ORDER', value=settings_json["tag_order_format"])
                prepend_tags = gr.Textbox(lines=1, label='Prepend Tags', value=settings_json["prepend_tags"])
                append_tags = gr.Textbox(lines=1, label='Append Tags', value=settings_json["append_tags"])
            with gr.Row():
                with gr.Column():
                    img_ext = gr.Dropdown(choices=img_extensions, label='Image Extension', value=settings_json["img_ext"])
                with gr.Column():
                    method_tag_files = gr.Radio(choices=method_tag_files_opts, label='Resized Img Tag Handler', value=settings_json["method_tag_files"])
                with gr.Column():
                    settings_path = gr.Textbox(lines=1, label='Path/Name to \"NEW\" JSON (REQUIRED)', value=config_name)
                create_new_config_checkbox = gr.Checkbox(label="Create NEW Config", value=False)
                temp = '\\' if help.is_windows() else '/'
                quick_json_select = gr.Dropdown(choices=sorted([(each_settings_file.split(temp)[-1]) for each_settings_file in glob.glob(os.path.join(cwd, f"*.json"))]), label='JSON Select',
                                      value=config_name)
                load_json_file_button = gr.Button(value="Load from JSON", variant='secondary')
        with gr.Tab("Stats Config"):
            with gr.Row():
                config_save_var1 = gr.Button(value="Apply & Save Settings", variant='primary')
            gr.Markdown(md_.stats_config)
            with gr.Row():
                min_score = gr.Slider(minimum=0, maximum=10000, step=1, label='Filter: Min Score', value=settings_json["min_score"])
            with gr.Row():
                min_fav_count = gr.Slider(minimum=0, maximum=10000, step=1, label='Filter: Min Fav Count', value=settings_json["min_fav_count"])
            with gr.Row():
                with gr.Column():
                    min_year = gr.Slider(minimum=2000, maximum=2050, step=1, label='Filter: Min Year', value=int(settings_json["min_year"]))
                    min_month = gr.Slider(minimum=1, maximum=12, step=1, label='Filter: Min Month',
                                     value=int(settings_json["min_month"]))
                    min_day = gr.Slider(minimum=1, maximum=31, step=1, label='Filter: Min Day',
                                     value=int(settings_json["min_day"]))
            with gr.Row():
                min_area = gr.Slider(minimum=1, maximum=1000000, step=1, label='Filter: Min Area', value=settings_json["min_area"], info='ONLY images with LxW > this value will be downloaded')
            with gr.Row():
                top_n = gr.Slider(minimum=0, maximum=10000, step=1, label='Filter: Top N', value=settings_json["top_n"], info='ONLY the top N images will be downloaded')
            with gr.Row():
                min_short_side = gr.Slider(minimum=1, maximum=100000, step=1, label='Resize Param: Min Short Side', value=settings_json["min_short_side"], info='ANY image\'s length or width that falls (ABOVE) this number will be resized')
        with gr.Tab("Checkbox Config"):
            with gr.Row():
                config_save_var2 = gr.Button(value="Apply & Save Settings", variant='primary')
            with gr.Row():
                with gr.Column():
                    gr.Markdown(md_.collect)
                    collect_checkbox_group_var = gr.CheckboxGroup(choices=collect_checkboxes, label='Collect Checkboxes', value=help.grab_pre_selected(settings_json, collect_checkboxes))
                with gr.Column():
                    gr.Markdown(md_.download)
                    download_checkbox_group_var = gr.CheckboxGroup(choices=download_checkboxes, label='Download Checkboxes', value=help.grab_pre_selected(settings_json, download_checkboxes))
                with gr.Column():
                    gr.Markdown(md_.resize)
                    resize_checkbox_group_var = gr.CheckboxGroup(choices=resize_checkboxes, label='Resize Checkboxes', value=help.grab_pre_selected(settings_json, resize_checkboxes))
        with gr.Tab("Required Tags Config"):
            with gr.Row():
                config_save_var3 = gr.Button(value="Apply & Save Settings", variant='primary')
            with gr.Row():
                with gr.Column():
                    required_tags = gr.Textbox(lines=1, label='Press Enter to ADD tag/s (E.g. tag1    or    tag1, tag2, ..., etc.)', value="")
                    remove_button_required = gr.Button(value="Remove Checked Tags", variant='secondary')
                with gr.Column():
                    file_all_tags_list_required = gr.File(file_count="multiple", file_types=["file"], label="Select ALL files with Tags to be parsed and Added")
                    parse_button_required = gr.Button(value="Parse/Add Tags", variant='secondary')
            with gr.Row():
                required_tags_group_var = gr.CheckboxGroup(choices=required_tags_list, label='ALL Required Tags', value=[])
        with gr.Tab("Blacklist Tags Config"):
            with gr.Row():
                config_save_var4 = gr.Button(value="Apply & Save Settings", variant='primary')
            with gr.Row():
                with gr.Column():
                    blacklist = gr.Textbox(lines=1, label='Press Enter to ADD tag/s (E.g. tag1    or    tag1, tag2, ..., etc.)', value="")
                    remove_button_blacklist = gr.Button(value="Remove Checked Tags", variant='secondary')
                with gr.Column():
                    file_all_tags_list_blacklist = gr.File(file_count="multiple", file_types=["file"], label="Select ALL files with Tags to be parsed and Added")
                    parse_button_blacklist = gr.Button(value="Parse/Add Tags", variant='secondary')
            with gr.Row():
                blacklist_group_var = gr.CheckboxGroup(choices=blacklist_tags, label='ALL Blacklisted Tags', value=[])
        with gr.Tab("Additional Components Config"):
            gr.Markdown(md_.add_comps_config)
            with gr.Row():
                config_save_var5 = gr.Button(value="Apply & Save Settings", variant='primary')
            with gr.Row():
                with gr.Column():
                    skip_posts_file = gr.Textbox(lines=1, label='Path to file w/ multiple id/md5 to skip',
                                             value=settings_json["skip_posts_file"])
                    skip_posts_type = gr.Radio(choices=["id","md5"], label='id/md5 skip', value=settings_json["skip_posts_type"])
                with gr.Column():
                    save_searched_list_path = gr.Textbox(lines=1, label='id/md5 list to file path', value=settings_json["save_searched_list_path"])
                    save_searched_list_type = gr.Radio(choices=["id", "md5", "None"], label='Save id/md5 list to file', value=settings_json["save_searched_list_type"])
            with gr.Row():
                with gr.Column():
                    apply_filter_to_listed_posts = gr.Checkbox(label='Apply Filters to Collected Posts',
                                                   value=settings_json["apply_filter_to_listed_posts"])
                    collect_from_listed_posts_type = gr.Radio(choices=["id", "md5"], label='id/md5 collect',
                                                          value=settings_json["collect_from_listed_posts_type"])
                    collect_from_listed_posts_file = gr.Textbox(lines=1, label='Path to file w/ multiple id/md5 to collect',
                                                            value=settings_json["collect_from_listed_posts_file"])
            with gr.Row():
                downloaded_posts_folder = gr.Textbox(lines=1, label='Path for downloaded posts',
                                                 value=settings_json["downloaded_posts_folder"])
                png_folder = gr.Textbox(lines=1, label='Path for png data', value=settings_json["png_folder"])
                jpg_folder = gr.Textbox(lines=1, label='Path for jpg data', value=settings_json["jpg_folder"])
                webm_folder = gr.Textbox(lines=1, label='Path for webm data', value=settings_json["webm_folder"])
                gif_folder = gr.Textbox(lines=1, label='Path for gif data', value=settings_json["gif_folder"])
                swf_folder = gr.Textbox(lines=1, label='Path for swf data', value=settings_json["swf_folder"])
            with gr.Row():
                download_remove_tag_file_button = gr.Button(value="(Optional) Download Negative Tags File", variant='secondary')
            with gr.Row():
                reference_model_tags_file = gr.Textbox(lines=1, label='Path to model tags file')
                gen_tags_list_button = gr.Button(value="Generate Tag/s List", variant='secondary')
                gen_tags_diff_list_button = gr.Button(value="Generate Tag/s Diff List", variant='secondary')
            with gr.Row():
                save_filename_type = gr.Radio(choices=["id","md5"], label='Select Filename Type', value=settings_json["save_filename_type"])
                remove_tags_list = gr.Textbox(lines=1, label='Path to remove tags file', value=settings_json["remove_tags_list"])
                replace_tags_list = gr.Textbox(lines=1, label='Path to replace tags file', value=settings_json["replace_tags_list"])
                tag_count_list_folder = gr.Textbox(lines=1, label='Path to tag count file', value=settings_json["tag_count_list_folder"])
            with gr.Row():
                remove_now_button = gr.Button(value="Remove Now", variant='primary')
                replace_now_button = gr.Button(value="Replace Now", variant='primary')
            with gr.Row():
                keyword_search_text = gr.Textbox(lines=1, label='Keyword/Tag to Search (Optional)')
                prepend_text = gr.Textbox(lines=1, label='Text to Prepend')
                prepend_option = gr.Radio(choices=["Start", "End"], label='Prepend/Append Text To:', value="Start")
            with gr.Row():
                prepend_now_button = gr.Button(value="Prepend/Append Now", variant='primary')
        with gr.Tab("Run Tab"):
            gr.Markdown(md_.run)
            with gr.Row():
                with gr.Column():
                    basefolder = gr.Textbox(lines=1, label='Root Output Dir Path', value=cwd)
                    numcpu = gr.Slider(minimum=1, maximum=mp.cpu_count(), step=1, label='Worker Threads', value=int(mp.cpu_count()/2))
            with gr.Row():
                with gr.Column():
                   phaseperbatch = gr.Checkbox(label='Completes all phases per batch', value=True)
                with gr.Column():
                   keepdb = gr.Checkbox(label='Keep e6 db data', value=False)
                with gr.Column():
                    cachepostsdb = gr.Checkbox(label='cache e6 posts file when multiple batches', value=False)
            with gr.Row():
                postscsv = gr.Textbox(lines=1, label='Path to e6 posts csv', value="")
                tagscsv = gr.Textbox(lines=1, label='Path to e6 tags csv', value="")
                postsparquet = gr.Textbox(lines=1, label='Path to e6 posts parquet', value="")
                tagsparquet = gr.Textbox(lines=1, label='Path to e6 tags parquet', value="")
            with gr.Row():
                images_full_change_dict_textbox = gr.Textbox(lines=1, label='Path to Image Full Change Log JSON (Optional)',
                                                         value=os.path.join(auto_config_path, f"auto_complete_{settings_json['batch_folder']}.json"))
                images_full_change_dict_run_button = gr.Button(value="(POST-PROCESSING only) Apply Auto-Config Update Changes", variant='secondary')
            with gr.Row():
                run_button = gr.Button(value="Run", variant='primary')
            with gr.Row():
                progress_bar_textbox_collect = gr.Textbox(interactive=False, visible=False)
            with gr.Row():
                progress_bar_textbox_download = gr.Textbox(interactive=False, visible=False)
            with gr.Row():
                progress_bar_textbox_resize = gr.Textbox(interactive=False, visible=False)
            with gr.Accordion("Batch Run"):
                with gr.Row():
                    temp = '\\' if help.is_windows() else '/'
                    all_json_files_checkboxgroup = gr.CheckboxGroup(choices=sorted([(each_settings_file.split(temp)[-1]) for each_settings_file in glob.glob(os.path.join(cwd, f"*.json"))]),
                                                                label='Select to Run', value=[])
                with gr.Row():
                    run_button_batch = gr.Button(value="Batch Run", variant='primary')
                with gr.Row():
                    progress_run_batch = gr.Textbox(interactive=False, visible=False)
        with gr.Tab("Image Preview Gallery"):
            gr.Markdown(md_.preview)
            with gr.Row():
                with gr.Column():
                    with gr.Row():
                        with gr.Column(elem_id="trim_row_length"):
                            gr.Markdown("""Reload Gallery""", elem_id="trim_markdown_length")
                            refresh_symbol = '\U0001f504'  # 🔄
                            refresh_aspect_btn = gr.Button(value=refresh_symbol, variant="variant", elem_id="refresh_aspect_btn")
                        download_folder_type = gr.Radio(choices=file_extn_list, label='Select Filename Type')# webm, swf not yet supported
                        img_id_textbox = gr.Textbox(label="Image ID", interactive=False, lines=1, value="")
                    with gr.Row():
                        tag_search_textbox = gr.Textbox(label="Search Tags (E.G. tag1 -tag2 shows images with tag1 but without tag2)", lines=1, value="")
                    with gr.Row():
                        with gr.Column(min_width=50, scale=3):
                            apply_to_all_type_select_checkboxgroup = gr.CheckboxGroup(choices=["png", "jpg", "gif", "searched"], label=f'Apply\'s to ALL of {["png", "jpg", "gif", "searched"]} type', value=[])
                        with gr.Column(min_width=50, scale=1):
                            select_multiple_images_checkbox = gr.Checkbox(label="Multi-Select", value=False, info="Click Image/s")
                        with gr.Column(min_width=50, scale=1):
                            select_between_images_checkbox = gr.Checkbox(label="Shift-Select", value=False, info="Selects All Between Two Images")
                    with gr.Row():
                        apply_datetime_sort_ckbx = gr.Checkbox(label="Sort", value=False, info="Image/s by date")
                        apply_datetime_choice_menu = gr.Dropdown(label="Sort Order", choices=["new-to-old", "old-to-new"], value="", info="Image/s by date")
                    with gr.Row():
                        tag_remove_button = gr.Button(value="Remove Selected Tag/s", variant='primary')
                        tag_save_button = gr.Button(value="Save Tag Changes", variant='primary')
                    with gr.Row():
                        image_remove_button = gr.Button(value="Remove Selected Image/s", variant='primary')
                        image_save_ids_button = gr.Button(value="Save Image Changes", variant='primary')
                    with gr.Row():
                        tag_add_textbox = gr.Textbox(label="Enter Tag/s here", lines=1, value="", info="Press Enter to ADD tag/s (E.g. tag1 or tag1, tag2, ..., etc.)")
                    img_artist_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Artist Tag/s', value=[])
                    img_character_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Character Tag/s', value=[])
                    img_species_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Species Tag/s', value=[])
                    img_general_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='General Tag/s', value=[])
                    img_meta_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Meta Tag/s', value=[])
                    img_rating_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Rating Tag/s', value=[])
                gallery_comp = gr.Gallery(visible=False, elem_id="gallery_id").style(columns=[3], object_fit="contain", height="auto")
        with gr.Tab("Data Stats"):
            with gr.Row():
                stats_run_options = gr.Dropdown(label="Run Method", choices=["frequency table", "inverse freq table"])
                stats_load_file = gr.Dropdown(label="Meta Tag Category", choices=["tags", "artist", "character", "species", "general", "meta", "rating"])
                stats_run_button = gr.Button(value="Run Stats", variant='primary')
            with gr.Row():
                stats_selected_data = gr.Dataframe(interactive=False, label="Dataframe Table", visible=False,
                                               headers=["Tag Category", "Count"], datatype=["str", "number"], max_cols=2,
                                               type="array")
        with gr.Tab("Download Extra/s: Model/s & Code Repos"):
            gr.Markdown(md_.extra)
            with gr.Column():
                repo_download_options = ["Kohya_ss LORA Trainer", "Auto-Tagging Model", "AUTO1111 WEBUI", "InvokeAI", "ComfyUI", "comfy-plasma"]

                repo_download_releases_only = gr.Checkbox(label='Download ONLY Releases', value=False)
                repo_download_checkbox_group = gr.CheckboxGroup(choices=repo_download_options, label='Repository Downloads', value=[])
                repo_download_options_no_auto1111 = ["Kohya_ss LORA Trainer", "Auto-Tagging Model", "InvokeAI", "AUTO1111 WEBUI"]
                repo_download_radio = gr.Radio(choices=repo_download_options_no_auto1111, label='Repository Downloads', visible=False)
                release_options_radio = gr.Radio(choices=[], label='Repository Downloads by Release', visible=False)
                release_assets_checkbox_group = gr.CheckboxGroup(choices=[], label='Repository Release Downloads', value=[], visible=False)
                repo_download_button = gr.Button(value="Download Repo/s", variant='primary')
            with gr.Column():
                model_download_options = ["Fluffusion", "FluffyRock"]
                tagging_model_download_options = ["Zack3D AutoTagging Model"]

                model_download_types = gr.Dropdown(choices=model_download_options, label='Diffusion Model Selection')
                tagging_model_download_types = gr.Dropdown(choices=tagging_model_download_options, label='AutoTagging Model Selection')
                model_download_checkbox_group = gr.CheckboxGroup(choices=[], label='Select ALL Code Repositories to Download', value=[], visible=False)
                nested_model_links_checkbox_group = gr.CheckboxGroup(choices=[], label='Specific Model Versions', value=[],
                                                                 visible=False)
                model_download_button = gr.Button(value="Download Model/s", variant='primary', visible=False)
        with gr.Tab("Add Custom Dataset"):
            gr.Markdown(md_.custom)
            image_modes = ['Single', 'Batch']
            if not "Z3D-E621-Convnext" in auto_tag_models and os.path.exists(os.path.join(os.getcwd(), 'Z3D-E621-Convnext')) \
                and os.path.exists(os.path.join(os.path.join(os.getcwd(), 'Z3D-E621-Convnext'), 'Z3D-E621-Convnext.onnx')):
                auto_tag_models.append('Z3D-E621-Convnext')
            if not "Fluffusion-AutoTag" in auto_tag_models and os.path.exists(os.path.join(os.getcwd(), 'Fluffusion-AutoTag')) \
                and os.path.exists(os.path.join(os.path.join(os.getcwd(), 'Fluffusion-AutoTag'), 'Fluffusion-AutoTag.pb')):
                auto_tag_models.append('Fluffusion-AutoTag')

            write_tag_opts = ['Overwrite', 'Merge', 'Pre-pend', 'Append']
            use_tag_opts = ['Use All', 'Use All above Threshold', 'Manually Select']
            with gr.Row():
                with gr.Column():
                    with gr.Row():
                        with gr.Tab("Single"):
                            file_upload_button_single = gr.File(label=f"{image_modes[0]} Image Mode", file_count="single",
                                                            interactive=True, file_types=["image"], visible=True, type="file")
                        with gr.Tab("Batch"):
                            file_upload_button_batch = gr.File(label=f"{image_modes[1]} Image Mode", file_count="directory",
                                                           interactive=True, visible=True, type="file")
                    with gr.Row():
                        with gr.Column(elem_id="trim_row_length"):
                            cpu_only_ckbx = gr.Checkbox(label="cpu", info="Use cpu only", value=True)
                        with gr.Column(elem_id="trim_row_length"):
                            gr.Markdown("""Refresh""", elem_id="trim_markdown_length")
                            refresh_symbol = '\U0001f504'  # 🔄
                            refresh_models_btn = gr.Button(value=refresh_symbol, variant="variant", elem_id="refresh_models_btn")
                        model_choice_dropdown = gr.Dropdown(choices=auto_tag_models, label="Model Selection")
                        crop_or_resize_radio = gr.Radio(label="Preprocess Options", choices=['Crop','Resize'], value='Resize')
                    with gr.Row():
                        landscape_crop_dropdown = gr.Dropdown(choices=['left', 'mid', 'right'], label="Landscape Crop", info="Mandatory", visible=False)
                        portrait_crop_dropdown = gr.Dropdown(choices=['top', 'mid', 'bottom'], label="Portrait Crop", info="Mandatory", visible=False)
                    # with gr.Row():
                    #     square_image_edit_slider = gr.Slider(minimum=0, maximum=3000, step=1, label='Crop/Resize Square Image Size', info='Length or Width', value=448, visible=True, interactive=True)
                    with gr.Row():
                        confidence_threshold_slider = gr.Slider(minimum=0, maximum=100, step=1, label='Confidence Threshold', value=75, visible=True, interactive=True)
                    with gr.Row():
                        interrogate_button = gr.Button(value="Interrogate", variant='primary')
                    with gr.Row():
                        image_with_tag_path_textbox = gr.Textbox(label="Path to Image Folder", info="Folder should contain both tag & image files", interactive=True)
                    with gr.Row():
                        with gr.Column(min_width=50, scale=1):
                            copy_mode_ckbx = gr.Checkbox(label="Copy", info="Copy To Tag Editor")
                        with gr.Column(min_width=50, scale=2):
                            save_custom_images_button = gr.Button(value="Save/Add Images", variant='primary')
                        with gr.Column(min_width=50, scale=2):
                            save_custom_tags_button = gr.Button(value="Save/Add Tags", variant='primary')
                    with gr.Row():
                        write_tag_opts_dropdown = gr.Dropdown(label="Write Tag Options", choices=write_tag_opts)
                        use_tag_opts_radio = gr.Dropdown(label="Use Tag Options", choices=use_tag_opts)
                with gr.Tab("Tag/s Preview"):
                    with gr.Column():
                        image_confidence_values = gr.Label(label="Tag/s Confidence/s", visible=True, value={})
                        image_generated_tags = gr.CheckboxGroup(label="Generated Tag/s", choices=[], visible=True, interactive=True)
                        image_generated_tags_prompt_builder_textbox = gr.Textbox(label="Prompt String", value="", visible=True, interactive=False)
                with gr.Tab("Image Preview"):
                    with gr.Column():
                        image_preview_pil = gr.Image(label=f"Image Preview", interactive=False, visible=True, type="pil")

        '''
        ##################################################################################################################################
        ####################################################     EVENT HANDLER/S     #####################################################
        ##################################################################################################################################
        '''

        image_mode_choice_state = gr.State("") # state of image mode for autotag model represented as a string
        images_selected_state = gr.JSON([], visible=False) # JSON list of image ids in the gallery
        multi_select_ckbx_state = gr.JSON([False], visible=False) # JSON boolean component wrapped in a list
        only_selected_state_object = gr.State(dict()) # state of image mappings represented by index -> [ext, img_id]
        images_tuple_points = gr.JSON([], visible=False) # JSON list of all images selected given by two points: a-b|b-a


        gen_tags_list_button.click(fn=gen_tags_list, inputs=[reference_model_tags_file], outputs=[])
        gen_tags_diff_list_button.click(fn=gen_tags_diff_list, inputs=[reference_model_tags_file], outputs=[])

        refresh_models_btn.click(fn=refresh_model_list, inputs=[], outputs=[model_choice_dropdown])

        refresh_aspect_btn.click(fn=force_reload_show_gallery,
                             inputs=[download_folder_type, apply_datetime_sort_ckbx, apply_datetime_choice_menu],
                             outputs=[gallery_comp])

        image_generated_tags.change(fn=prompt_string_builder,
                                inputs=[use_tag_opts_radio, image_generated_tags, confidence_threshold_slider],
                                outputs=[image_generated_tags_prompt_builder_textbox])

        save_custom_tags_button.click(fn=save_custom_tags,
                                  inputs=[image_mode_choice_state, image_with_tag_path_textbox, image_generated_tags],
                                  outputs=[image_confidence_values, image_generated_tags, image_preview_pil, image_generated_tags_prompt_builder_textbox])

        save_custom_images_button.click(fn=save_custom_images,
                                    inputs=[image_mode_choice_state, image_with_tag_path_textbox, copy_mode_ckbx],
                                    outputs=[image_confidence_values, image_generated_tags, image_preview_pil, image_generated_tags_prompt_builder_textbox])
        interrogate_button.click(unload_component, None, image_preview_pil)\
            .then(unload_component, gr.State([]), image_generated_tags)\
            .then(unload_component, gr.State(""), image_generated_tags_prompt_builder_textbox).then(fn=interrogate_images,
                                                                             inputs=[image_mode_choice_state,
                                                                                     confidence_threshold_slider],
                                                                             outputs=[image_confidence_values,
                                                                                      image_generated_tags,
                                                                                      image_preview_pil],
                                                                             show_progress=True).then(fn=prompt_string_builder,
                                                                              inputs=[use_tag_opts_radio, image_generated_tags, confidence_threshold_slider],
                                                                              outputs=[image_generated_tags_prompt_builder_textbox])
        crop_or_resize_radio.change(fn=make_menus_visible, inputs=[crop_or_resize_radio], outputs=[landscape_crop_dropdown, portrait_crop_dropdown])
        model_choice_dropdown.select(fn=load_model, inputs=[model_choice_dropdown, cpu_only_ckbx], outputs=[])
        # cpu_only_ckbx.change(fn=re_load_model, inputs=[model_choice_dropdown, cpu_only_ckbx], outputs=[])
        confidence_threshold_slider.change(fn=set_threshold,
                                       inputs=[confidence_threshold_slider],
                                       outputs=[image_confidence_values, image_generated_tags]).then(fn=prompt_string_builder,
                                                                             inputs=[use_tag_opts_radio, image_generated_tags, confidence_threshold_slider],
                                                                             outputs=[image_generated_tags_prompt_builder_textbox])
        file_upload_button_single.upload(fn=load_images, inputs=[file_upload_button_single, image_mode_choice_state], outputs=[image_mode_choice_state])
        file_upload_button_batch.upload(fn=load_images, inputs=[file_upload_button_batch, image_mode_choice_state], outputs=[image_mode_choice_state])
        crop_or_resize_radio.change(fn=set_crop_or_resize, inputs=[crop_or_resize_radio], outputs=[])
        landscape_crop_dropdown.select(fn=set_landscape_square_crop, inputs=[landscape_crop_dropdown], outputs=[])
        portrait_crop_dropdown.select(fn=set_portrait_square_crop, inputs=[portrait_crop_dropdown], outputs=[])
        # square_image_edit_slider.change(fn=set_square_size, inputs=[square_image_edit_slider], outputs=[])
        write_tag_opts_dropdown.select(fn=set_write_tag_opts, inputs=[], outputs=[])
        use_tag_opts_radio.select(fn=set_use_tag_opts_radio, inputs=[], outputs=[]).then(fn=prompt_string_builder,
                                                                              inputs=[use_tag_opts_radio, image_generated_tags, confidence_threshold_slider],
                                                                              outputs=[image_generated_tags_prompt_builder_textbox])
        image_with_tag_path_textbox.change(fn=set_image_with_tag_path_textbox, inputs=[image_with_tag_path_textbox], outputs=[])
        copy_mode_ckbx.change(fn=set_copy_mode_ckbx, inputs=[copy_mode_ckbx], outputs=[])

        download_remove_tag_file_button.click(help.download_negative_tags_file, None, None)
        tagging_model_download_types.select(fn=make_visible, inputs=[], outputs=[model_download_button])

        release_options_radio.select(fn=get_repo_assets, inputs=[release_options_radio], outputs=[repo_download_button, release_assets_checkbox_group])
        repo_download_radio.select(fn=get_repo_releases, inputs=[repo_download_radio], outputs=[release_options_radio])
        repo_download_releases_only.change(fn=reload_release_options, inputs=[repo_download_releases_only],
                                       outputs=[repo_download_checkbox_group, repo_download_radio, release_options_radio, repo_download_button, release_assets_checkbox_group])

        repo_download_button.click(fn=download_repos, inputs=[repo_download_releases_only, repo_download_checkbox_group, release_assets_checkbox_group, repo_download_radio], outputs=[])

        model_download_types.select(fn=show_model_downloads_options, inputs=[model_download_types],
                                outputs=[model_download_checkbox_group, model_download_button, nested_model_links_checkbox_group])

        model_download_checkbox_group.change(fn=show_nested_fluffyrock_models, inputs=[model_download_checkbox_group],
                                outputs=[model_download_checkbox_group, model_download_button, nested_model_links_checkbox_group])

        model_download_button.click(fn=download_models, inputs=[model_download_types, model_download_checkbox_group, tagging_model_download_types, nested_model_links_checkbox_group],
                                outputs=[model_download_types, tagging_model_download_types, nested_model_links_checkbox_group])

        images_full_change_dict_run_button.click(fn=make_run_visible,inputs=[],outputs=[progress_bar_textbox_collect]).then(fn=auto_config_apply,
            inputs=[images_full_change_dict_textbox], outputs=[progress_bar_textbox_collect])

        remove_now_button.click(fn=remove_from_all, inputs=[remove_tags_list, apply_to_all_type_select_checkboxgroup], outputs=[])
        replace_now_button.click(fn=replace_from_all, inputs=[replace_tags_list, apply_to_all_type_select_checkboxgroup], outputs=[])
        prepend_now_button.click(fn=prepend_with_keyword, inputs=[keyword_search_text, prepend_text, prepend_option, apply_to_all_type_select_checkboxgroup], outputs=[])

        image_remove_button.click(fn=remove_images, inputs=[apply_to_all_type_select_checkboxgroup, img_id_textbox, apply_datetime_sort_ckbx,
                            apply_datetime_choice_menu, multi_select_ckbx_state, only_selected_state_object, images_selected_state],
                              outputs=[img_artist_tag_checkbox_group,img_character_tag_checkbox_group,
                                       img_species_tag_checkbox_group,img_general_tag_checkbox_group,
                                       img_meta_tag_checkbox_group,img_rating_tag_checkbox_group,gallery_comp,
                                       img_id_textbox, only_selected_state_object, images_selected_state]).then(fn=reset_gallery, inputs=[],
                              outputs=[gallery_comp]).then(fn=show_searched_gallery, inputs=[download_folder_type, apply_datetime_sort_ckbx, apply_datetime_choice_menu],
                              outputs=[gallery_comp])

        image_save_ids_button.click(fn=save_image_changes, inputs=[], outputs=[])

        stats_run_button.click(fn=run_stats, inputs=[stats_run_options, stats_load_file], outputs=[stats_selected_data])

        tag_remove_button.click(fn=remove_tag_changes, inputs=[img_artist_tag_checkbox_group, apply_to_all_type_select_checkboxgroup,
                img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state],
                outputs=[img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group,
                                           img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group]).then(fn=remove_tag_changes,
                inputs=[img_character_tag_checkbox_group, apply_to_all_type_select_checkboxgroup,
                img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state],
                outputs=[img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group,
                                           img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group]).then(fn=remove_tag_changes,
                inputs=[img_species_tag_checkbox_group, apply_to_all_type_select_checkboxgroup,
                img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state],
                outputs=[img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group,
                                           img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group]).then(fn=remove_tag_changes,
                inputs=[img_general_tag_checkbox_group, apply_to_all_type_select_checkboxgroup,
                img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state],
                outputs=[img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group,
                                           img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group]).then(fn=remove_tag_changes,
                inputs=[img_meta_tag_checkbox_group, apply_to_all_type_select_checkboxgroup,
                img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state],
                outputs=[img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group,
                                           img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group]).then(fn=remove_tag_changes,
                inputs=[img_rating_tag_checkbox_group, apply_to_all_type_select_checkboxgroup,
                img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state],
                outputs=[img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group,
                                           img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group])

        tag_add_textbox.submit(fn=add_tag_changes, inputs=[tag_add_textbox, apply_to_all_type_select_checkboxgroup,
                                img_id_textbox, multi_select_ckbx_state, only_selected_state_object, images_selected_state],
                                  outputs=[img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group,
                                           img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group])

        tag_save_button.click(fn=save_tag_changes,inputs=[], outputs=[]).then(fn=reset_gallery, inputs=[], outputs=[gallery_comp]).then(fn=show_searched_gallery,
                            inputs=[download_folder_type, apply_datetime_sort_ckbx, apply_datetime_choice_menu], outputs=[gallery_comp]).then(fn=clear_categories, inputs=[],
                            outputs=[img_artist_tag_checkbox_group,img_character_tag_checkbox_group,img_species_tag_checkbox_group,
                                     img_general_tag_checkbox_group,img_meta_tag_checkbox_group,img_rating_tag_checkbox_group,img_id_textbox])

        tag_search_textbox.submit(fn=search_tags, inputs=[tag_search_textbox, apply_to_all_type_select_checkboxgroup, apply_datetime_sort_ckbx,
                                                      apply_datetime_choice_menu],
                        outputs=[gallery_comp]).then(fn=reset_selected_img, inputs=[img_id_textbox],
                        outputs=[img_id_textbox, img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group, img_general_tag_checkbox_group,
                                img_meta_tag_checkbox_group, img_rating_tag_checkbox_group])

        select_multiple_images_checkbox.change(fn=set_ckbx_state,
                                           inputs=[select_multiple_images_checkbox, multi_select_ckbx_state],
                                           outputs=[multi_select_ckbx_state])
        download_folder_type.change(fn=show_gallery, inputs=[download_folder_type, apply_datetime_sort_ckbx, apply_datetime_choice_menu], outputs=[gallery_comp]).then(fn=reset_selected_img, inputs=[img_id_textbox],
                        outputs=[img_id_textbox, img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group, img_general_tag_checkbox_group,
                                img_meta_tag_checkbox_group, img_rating_tag_checkbox_group])

        # there is a networking "delay" bug for the below feature to work (do NOT click on the same image after selected) i.e. click on a different image before going back to that one
        gallery_comp.select(fn=get_img_tags,
        inputs=[gallery_comp, select_multiple_images_checkbox, images_selected_state, select_between_images_checkbox, images_tuple_points],
        outputs=[img_id_textbox, img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group,
                 img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group, images_selected_state,
                 only_selected_state_object, images_tuple_points]).then(None,
        inputs=[images_selected_state, multi_select_ckbx_state], outputs=None, _js=js_.js_do_everything)

        load_json_file_button.click(fn=change_config, inputs=[quick_json_select,settings_path], outputs=[batch_folder,resized_img_folder,
                tag_sep,tag_order_format,prepend_tags,append_tags,img_ext,method_tag_files,min_score,min_fav_count,
                min_year,min_month,min_day,min_area,top_n,min_short_side,collect_checkbox_group_var,
                download_checkbox_group_var,resize_checkbox_group_var,required_tags_group_var,blacklist_group_var,skip_posts_file,
                skip_posts_type,collect_from_listed_posts_file,collect_from_listed_posts_type,
                apply_filter_to_listed_posts,save_searched_list_type,save_searched_list_path,downloaded_posts_folder,
                png_folder,jpg_folder,webm_folder,gif_folder,swf_folder,save_filename_type,remove_tags_list,
                replace_tags_list,tag_count_list_folder,all_json_files_checkboxgroup,quick_json_select,proxy_url_textbox, settings_path]).then(fn=check_to_reload_auto_complete_config, inputs=[], outputs=[])

        config_save_var0.click(fn=config_save_button,
                          inputs=[batch_folder,resized_img_folder,tag_sep,tag_order_format,prepend_tags,append_tags,
                                  img_ext,method_tag_files,min_score,min_fav_count,min_area,top_n,
                                  min_short_side,skip_posts_file,
                                  skip_posts_type,collect_from_listed_posts_file,collect_from_listed_posts_type,
                                  apply_filter_to_listed_posts,save_searched_list_type,save_searched_list_path,
                                  downloaded_posts_folder,png_folder,jpg_folder,webm_folder,gif_folder,swf_folder,
                                  save_filename_type,remove_tags_list,replace_tags_list,tag_count_list_folder,min_month,
                                  min_day,min_year,collect_checkbox_group_var,download_checkbox_group_var,resize_checkbox_group_var,create_new_config_checkbox,settings_path,proxy_url_textbox
                                  ],
                          outputs=[all_json_files_checkboxgroup, quick_json_select]
                          ).then(fn=check_to_reload_auto_complete_config, inputs=[], outputs=[])
        config_save_var1.click(fn=config_save_button,
                          inputs=[batch_folder,resized_img_folder,tag_sep,tag_order_format,prepend_tags,append_tags,
                                  img_ext,method_tag_files,min_score,min_fav_count,min_area,top_n,
                                  min_short_side,skip_posts_file,
                                  skip_posts_type,collect_from_listed_posts_file,collect_from_listed_posts_type,
                                  apply_filter_to_listed_posts,save_searched_list_type,save_searched_list_path,
                                  downloaded_posts_folder,png_folder,jpg_folder,webm_folder,gif_folder,swf_folder,
                                  save_filename_type,remove_tags_list,replace_tags_list,tag_count_list_folder,min_month,
                                  min_day,min_year,collect_checkbox_group_var,download_checkbox_group_var,resize_checkbox_group_var,create_new_config_checkbox,settings_path,proxy_url_textbox
                                  ],
                          outputs=[]
                          ).then(fn=check_to_reload_auto_complete_config, inputs=[], outputs=[])
        config_save_var2.click(fn=config_save_button,
                          inputs=[batch_folder,resized_img_folder,tag_sep,tag_order_format,prepend_tags,append_tags,
                                  img_ext,method_tag_files,min_score,min_fav_count,min_area,top_n,
                                  min_short_side,skip_posts_file,
                                  skip_posts_type,collect_from_listed_posts_file,collect_from_listed_posts_type,
                                  apply_filter_to_listed_posts,save_searched_list_type,save_searched_list_path,
                                  downloaded_posts_folder,png_folder,jpg_folder,webm_folder,gif_folder,swf_folder,
                                  save_filename_type,remove_tags_list,replace_tags_list,tag_count_list_folder,min_month,
                                  min_day,min_year,collect_checkbox_group_var,download_checkbox_group_var,resize_checkbox_group_var,create_new_config_checkbox,settings_path,proxy_url_textbox
                                  ],
                          outputs=[]
                          ).then(fn=check_to_reload_auto_complete_config, inputs=[], outputs=[])
        config_save_var3.click(fn=config_save_button,
                          inputs=[batch_folder,resized_img_folder,tag_sep,tag_order_format,prepend_tags,append_tags,
                                  img_ext,method_tag_files,min_score,min_fav_count,min_area,top_n,
                                  min_short_side,skip_posts_file,
                                  skip_posts_type,collect_from_listed_posts_file,collect_from_listed_posts_type,
                                  apply_filter_to_listed_posts,save_searched_list_type,save_searched_list_path,
                                  downloaded_posts_folder,png_folder,jpg_folder,webm_folder,gif_folder,swf_folder,
                                  save_filename_type,remove_tags_list,replace_tags_list,tag_count_list_folder,min_month,
                                  min_day,min_year,collect_checkbox_group_var,download_checkbox_group_var,resize_checkbox_group_var,create_new_config_checkbox,settings_path,proxy_url_textbox
                                  ],
                          outputs=[]
                          ).then(fn=check_to_reload_auto_complete_config, inputs=[], outputs=[])
        config_save_var4.click(fn=config_save_button,
                          inputs=[batch_folder,resized_img_folder,tag_sep,tag_order_format,prepend_tags,append_tags,
                                  img_ext,method_tag_files,min_score,min_fav_count,min_area,top_n,
                                  min_short_side,skip_posts_file,
                                  skip_posts_type,collect_from_listed_posts_file,collect_from_listed_posts_type,
                                  apply_filter_to_listed_posts,save_searched_list_type,save_searched_list_path,
                                  downloaded_posts_folder,png_folder,jpg_folder,webm_folder,gif_folder,swf_folder,
                                  save_filename_type,remove_tags_list,replace_tags_list,tag_count_list_folder,min_month,
                                  min_day,min_year,collect_checkbox_group_var,download_checkbox_group_var,resize_checkbox_group_var,create_new_config_checkbox,settings_path,proxy_url_textbox
                                  ],
                          outputs=[]
                          ).then(fn=check_to_reload_auto_complete_config, inputs=[], outputs=[])
        config_save_var5.click(fn=config_save_button,
                          inputs=[batch_folder,resized_img_folder,tag_sep,tag_order_format,prepend_tags,append_tags,
                                  img_ext,method_tag_files,min_score,min_fav_count,min_area,top_n,
                                  min_short_side,skip_posts_file,
                                  skip_posts_type,collect_from_listed_posts_file,collect_from_listed_posts_type,
                                  apply_filter_to_listed_posts,save_searched_list_type,save_searched_list_path,
                                  downloaded_posts_folder,png_folder,jpg_folder,webm_folder,gif_folder,swf_folder,
                                  save_filename_type,remove_tags_list,replace_tags_list,tag_count_list_folder,min_month,
                                  min_day,min_year,collect_checkbox_group_var,download_checkbox_group_var,resize_checkbox_group_var,create_new_config_checkbox,settings_path,proxy_url_textbox
                                  ],
                          outputs=[]
                          ).then(fn=check_to_reload_auto_complete_config, inputs=[], outputs=[])

        run_button.click(fn=run_script,inputs=[basefolder,settings_path,numcpu,phaseperbatch,keepdb,cachepostsdb,postscsv,tagscsv,postsparquet,tagsparquet],
                     outputs=[]).then(fn=make_run_visible,inputs=[],outputs=[progress_bar_textbox_collect]).then(fn=data_collect, inputs=[],
                     outputs=[progress_bar_textbox_collect]).then(fn=make_run_visible,inputs=[],outputs=[progress_bar_textbox_download]).then(fn=data_download, inputs=[],
                     outputs=[progress_bar_textbox_download]).then(fn=make_run_visible,inputs=[],outputs=[progress_bar_textbox_resize]).then(fn=data_resize, inputs=[resize_checkbox_group_var],
                     outputs=[progress_bar_textbox_resize]).then(fn=end_connection,inputs=[],outputs=[])

        run_button_batch.click(fn=make_run_visible,inputs=[],outputs=[progress_run_batch]).then(fn=run_script_batch,
                     inputs=[basefolder,settings_path,numcpu,phaseperbatch,keepdb,cachepostsdb,postscsv,tagscsv,postsparquet,tagsparquet,all_json_files_checkboxgroup,images_full_change_dict_textbox],
                     outputs=[progress_run_batch])

        required_tags.submit(fn=textbox_handler_required, inputs=[required_tags], outputs=[required_tags,required_tags_group_var])
        blacklist.submit(fn=textbox_handler_blacklist, inputs=[blacklist], outputs=[blacklist,blacklist_group_var])

        remove_button_required.click(fn=check_box_group_handler_required, inputs=[required_tags_group_var], outputs=[required_tags_group_var])
        remove_button_blacklist.click(fn=check_box_group_handler_blacklist, inputs=[blacklist_group_var], outputs=[blacklist_group_var])

        parse_button_required.click(fn=parse_file_required, inputs=[file_all_tags_list_required], outputs=[required_tags_group_var])
        parse_button_blacklist.click(fn=parse_file_blacklist, inputs=[file_all_tags_list_blacklist], outputs=[blacklist_group_var])
    return demo

def load_tags_csv(proxy_url=None):
    # check to update the tags csv
    help.check_to_update_csv(proxy_url=proxy_url)
    # get newest
    current_list_of_csvs = help.sort_csv_files_by_date(os.getcwd())
    # load
    data = pd.read_csv(current_list_of_csvs[0], index_col='name')
    data_columns_dict = data.to_dict()
    all_tags_ever_dict = data_columns_dict['category']
    del data
    return all_tags_ever_dict

def UI(**kwargs):
    # Show the interface
    launch_kwargs = {}
    if not kwargs.get('username', None) == '':
        launch_kwargs['auth'] = (
            kwargs.get('username', None),
            kwargs.get('password', None),
        )
    if kwargs.get('server_port', 0) > 0:
        launch_kwargs['server_port'] = kwargs.get('server_port', 0)
    if kwargs.get('share', True):
        launch_kwargs['share'] = True

    print(launch_kwargs)
    demo.queue().launch(**launch_kwargs)

if __name__ == "__main__":
    # init client & server connection
    HOST = "127.0.0.1"

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--username', type=str, default='', help='Username for authentication'
    )
    parser.add_argument(
        '--password', type=str, default='', help='Password for authentication'
    )
    parser.add_argument(
        '--server_port',
        type=int,
        default=0,
        help='Port to run the server listener on',
    )
    parser.add_argument(
        '--share',
        action='store_true',
        help='Share live gradio link',
    )
    parser.add_argument(
        '--proxy_url',
        type=str,
        default=None,
        help='(Optional) Proxy URL for downloading tags.csv.gz file',
    )

    args = parser.parse_args()

    '''
    ##################################################################################################################################
    #############################################     PRIMARY VARIABLE DECLARATIONS     ##############################################
    ##################################################################################################################################
    '''

    # set local path
    cwd = os.getcwd()
    categories_map = {0: 'general', 1: 'artist', 2: 'rating', 3: 'copyright', 4: 'character', 5: 'species',
                      6: 'invalid',
                      7: 'meta', 8: 'lore'}

    # options
    img_extensions = ["png", "jpg", "same_as_original"]
    method_tag_files_opts = ["relocate", "copy"]
    collect_checkboxes = ["include_tag_file", "include_explicit_tag", "include_questionable_tag", "include_safe_tag",
                          "include_png", "include_jpg", "include_gif", "include_webm", "include_swf",
                          "include_explicit",
                          "include_questionable", "include_safe"]
    download_checkboxes = ["skip_post_download", "reorder_tags", "replace_underscores", "remove_parentheses", "do_sort"]
    resize_checkboxes = ["skip_resize", "delete_original"]
    file_extn_list = ["png", "jpg", "gif"]

    ### assume settings.json at the root dir of repo

    # session config
    global config_name, auto_complete_config_name
    config_name = "settings.json"

    global is_csv_loaded
    is_csv_loaded = False
    global artist_csv_dict, character_csv_dict, species_csv_dict, general_csv_dict, meta_csv_dict, rating_csv_dict, tags_csv_dict  # load on dropdown click - stats / radio click - gallery (always do BOOL check)
    artist_csv_dict = {}
    character_csv_dict = {}
    species_csv_dict = {}
    general_csv_dict = {}
    meta_csv_dict = {}
    rating_csv_dict = {}
    tags_csv_dict = {}
    # ignore the first line in the csv file
    global selected_image_dict  # set on every click ::  # id -> {categories: tag/s}, type -> string
    selected_image_dict = None  ### key:category, value:tag_list
    global all_images_dict  # load on radio click - gallery (always do BOOL check)
    all_images_dict = {}  ### add images by key:id, value:selected_image_dict

    global settings_json
    settings_json = help.load_session_config(os.path.join(cwd, config_name))

    global required_tags_list
    required_tags_list = help.get_list(settings_json["required_tags"], settings_json["tag_sep"])
    for tag in required_tags_list:
        if len(tag) == 0:
            required_tags_list.remove(tag)

    global blacklist_tags
    blacklist_tags = help.get_list(settings_json["blacklist"], " | ")
    for tag in blacklist_tags:
        if len(tag) == 0:
            blacklist_tags.remove(tag)

    help.verbose_print(f"{settings_json}")
    help.verbose_print(f"json key count: {len(settings_json)}")

    # UPDATE json with new key, value pairs
    if not "min_date" in settings_json:
        settings_json["min_year"] = 2000
    elif isinstance(settings_json["min_date"], str) and "-" in settings_json["min_date"]:
        settings_json["min_year"] = int(settings_json["min_date"].split("-")[0])
    else:
        settings_json["min_year"] = int(settings_json["min_date"])

    if not "min_month" in settings_json:
        settings_json["min_month"] = 1
    elif isinstance(settings_json["min_date"], str) and "-" in settings_json["min_date"]:
        settings_json["min_month"] = help.from_padded(settings_json["min_date"].split("-")[1])

    if not "min_day" in settings_json:
        settings_json["min_day"] = 1
    elif isinstance(settings_json["min_date"], str) and settings_json["min_date"].count("-") > 1:
        settings_json["min_day"] = help.from_padded(settings_json["min_date"].split("-")[-1])

    help.update_JSON(settings_json, config_name)

    global blacklist_images_dict
    global whitelist_images_all_changes_dict
    global auto_complete_config
    # load if data present / create if file not yet created
    auto_config_path = os.path.join(cwd, "auto_configs")
    auto_complete_config_name = f"auto_complete_{settings_json['batch_folder']}.json"
    temp_config_path = os.path.join(auto_config_path, auto_complete_config_name)
    if not os.path.exists(auto_config_path):
        os.makedirs(auto_config_path)
    auto_complete_config = help.load_session_config(temp_config_path)

    if not auto_complete_config:
        auto_complete_config = {'png': {}, 'jpg': {}, 'gif': {}}
        help.update_JSON(auto_complete_config, temp_config_path)

    global repo_release_urls
    repo_release_urls = {}

    global image_creation_times
    image_creation_times = {}

    global all_tags_ever_dict
    all_tags_ever_dict = {}

    global autotagmodel
    autotagmodel = None

    global auto_tag_models
    auto_tag_models = []

    global all_predicted_confidences
    global all_predicted_tags
    all_predicted_confidences = {}
    all_predicted_tags = []

    help.verbose_print(f"EVERYTHING INITIALIZING")
    help.verbose_print(f"Initial check to download & load tags CSV")
    all_tags_ever_dict = load_tags_csv(proxy_url=args.proxy_url)

    demo = build_ui()

    UI(
        username=args.username,
        password=args.password,
        server_port=args.server_port,
        share=args.share,
    )

