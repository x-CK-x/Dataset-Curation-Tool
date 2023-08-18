import string
import gradio as gr
import os
import argparse
import pandas as pd
import datrie

from utils import css_constants as css_, helper_functions as help

'''
##################################################################################################################################
#######################################################     GUI BLOCKS     #######################################################
##################################################################################################################################
'''

def build_ui():
    from UI_tabs.download_tab import Download_tab
    from UI_tabs.gallery_tab import Gallery_tab
    from UI_tabs.stats_tab import Stats_tab
    from UI_tabs.extras_tab import Extras_tab
    from UI_tabs.custom_dataset_tab import Custom_dataset_tab
    from UI_tabs.image_editor_tab import Image_editor_tab
    from UI_tabs.advanced_settings_tab import Advanced_settings_tab

    global settings_json
    with gr.Blocks(css=f"{css_.preview_hide_rule} {css_.refresh_aspect_btn_rule} {css_.trim_row_length} {css_.trim_markdown_length} "
                       f"{css_.thumbnail_colored_border_css} {css_.refresh_models_btn_rule}"
                       f"{css_.green_button_css} {css_.red_button_css}") as demo:# {css_.gallery_fix_height}

        image_mode_choice_state = gr.State("") # state of image mode for autotag model represented as a string
        images_selected_state = gr.JSON([], visible=False) # JSON list of image ids in the gallery
        multi_select_ckbx_state = gr.JSON([False], visible=False) # JSON boolean component wrapped in a list
        only_selected_state_object = gr.State(dict()) # state of image mappings represented by index -> [ext, img_id]
        images_tuple_points = gr.JSON([], visible=False) # JSON list of all images selected given by two points: a-b|b-a
        initial_add_state = gr.State("")
        initial_add_state_tag = gr.State("")
        initial_required_state = gr.State("")
        initial_required_state_tag = gr.State("")
        initial_blacklist_state = gr.State("")
        initial_blacklist_state_tag = gr.State("")
        previous_search_state_text = gr.State("") # contains the previous full text of string
        current_search_state_placement_tuple = gr.State((0, "")) # contains the index of the word being edited & the word
        relevant_search_categories = gr.State([])
        relevant_add_categories = gr.State([])
        relevant_required_categories = gr.State([])
        relevant_blacklist_categories = gr.State([])

        ################################################################################################################
        # download tab init
        download_tab_manager = Download_tab(settings_json, cwd, categories_map, img_extensions, method_tag_files_opts,
                                            collect_checkboxes, download_checkboxes, resize_checkboxes, file_extn_list,
                                            config_name, required_tags_list, blacklist_tags, auto_config_path,
                                            initial_required_state,
                                            initial_required_state_tag, relevant_required_categories,
                                            initial_blacklist_state, initial_blacklist_state_tag,
                                            relevant_blacklist_categories, auto_complete_config
                                            )
        # get vars
        config_save_var, batch_folder, resized_img_folder, custom_csv_path_textbox, use_csv_custom_checkbox,\
        proxy_url_textbox, tag_sep, tag_order_format, prepend_tags, append_tags, img_ext, method_tag_files,\
        settings_path, create_new_config_checkbox, quick_json_select, min_score, min_fav_count, min_year,\
        min_month, min_day, min_area, top_n, min_short_side, collect_checkbox_group_var,\
        download_checkbox_group_var, resize_checkbox_group_var, required_tags_textbox,\
        tag_required_suggestion_dropdown, required_tags_group_var, file_all_tags_list_required,\
        remove_button_required, parse_button_required, blacklist_tags_textbox,\
        tag_blacklist_suggestion_dropdown, blacklist_group_var, file_all_tags_list_blacklist,\
        remove_button_blacklist, parse_button_blacklist, skip_posts_file, skip_posts_type,\
        save_searched_list_path, save_searched_list_type, apply_filter_to_listed_posts,\
        collect_from_listed_posts_type, collect_from_listed_posts_file, downloaded_posts_folder, png_folder,\
        jpg_folder, webm_folder, gif_folder, swf_folder, download_remove_tag_file_button,\
        reference_model_tags_file, gen_tags_list_button, gen_tags_diff_list_button, save_filename_type,\
        remove_tags_list, replace_tags_list, tag_count_list_folder, remove_now_button, replace_now_button,\
        keyword_search_text, prepend_text, prepend_option, prepend_now_button, basefolder, numcpu,\
        phaseperbatch, keepdb, cachepostsdb, postscsv, tagscsv, postsparquet, tagsparquet,\
        images_full_change_dict_textbox, images_full_change_dict_run_button, run_button,\
        progress_bar_textbox_collect, progress_bar_textbox_download, progress_bar_textbox_resize,\
        all_json_files_checkboxgroup, run_button_batch, progress_run_batch = \
            download_tab_manager.get_tab()

        ################################################################################################################
        # gallery tab init
        gallery_tab_manager = Gallery_tab(file_extn_list, categories_map, cwd, settings_json,
                                          multi_select_ckbx_state,
                                          only_selected_state_object, images_selected_state, image_mode_choice_state,
                                          previous_search_state_text, current_search_state_placement_tuple,
                                          relevant_search_categories, initial_add_state, initial_add_state_tag,
                                          relevant_add_categories, images_tuple_points, download_tab_manager,
                                          auto_complete_config_name, all_tags_ever_dict, trie, all_images_dict,
                                          selected_image_dict, artist_csv_dict, character_csv_dict, species_csv_dict,
                                          general_csv_dict, meta_csv_dict, rating_csv_dict, tags_csv_dict,
                                          image_creation_times, is_csv_loaded
                                          )
        # get vars
        refresh_aspect_btn, download_folder_type, img_id_textbox, tag_search_textbox,\
        tag_search_suggestion_dropdown, apply_to_all_type_select_checkboxgroup,\
        select_multiple_images_checkbox, select_between_images_checkbox, apply_datetime_sort_ckbx,\
        apply_datetime_choice_menu, image_remove_button, image_save_ids_button, send_img_from_gallery_dropdown,\
        batch_send_from_gallery_checkbox, send_img_from_gallery_button, tag_remove_button, tag_save_button,\
        tag_add_textbox, tag_add_suggestion_dropdown, category_filter_gallery_dropdown,\
        tag_effects_gallery_dropdown, img_artist_tag_checkbox_group, img_character_tag_checkbox_group,\
        img_species_tag_checkbox_group, img_general_tag_checkbox_group, img_meta_tag_checkbox_group,\
        img_rating_tag_checkbox_group, gallery_comp = \
            gallery_tab_manager.get_tab()
        # share object reference
        download_tab_manager.set_gallery_tab_manager(gallery_tab_manager)

        ################################################################################################################
        # stats tab init
        stats_tab_manager = Stats_tab(gallery_tab_manager)
        # get vars
        stats_run_options, stats_load_file, stats_run_button, stats_selected_data = stats_tab_manager.get_tab()

        ################################################################################################################
        # extras tab init
        extras_tab_manager = Extras_tab(repo_release_urls)
        # get vars
        repo_download_releases_only, repo_download_checkbox_group, repo_download_radio, release_options_radio,\
        release_assets_checkbox_group, repo_download_button, model_download_types,\
        tagging_model_download_types, model_download_checkbox_group, nested_model_links_checkbox_group,\
        model_download_button = \
            extras_tab_manager.get_tab()

        ################################################################################################################
        # custom dataset tab init
        custom_dataset_tab_manager = Custom_dataset_tab(categories_map, cwd, settings_json, gallery_tab_manager,
                                                        image_mode_choice_state, autotagmodel,
                                                        all_predicted_confidences, all_predicted_tags)
        # get vars
        file_upload_button_single, file_upload_button_batch, gallery_images_batch, image_preview_pil,\
        send_img_from_autotag_dropdown, send_img_from_autotag_button, cpu_only_ckbx, refresh_models_btn,\
        model_choice_dropdown, crop_or_resize_radio, landscape_crop_dropdown, portrait_crop_dropdown,\
        confidence_threshold_slider, interrogate_button, image_with_tag_path_textbox, copy_mode_ckbx,\
        save_custom_images_button, save_custom_tags_button, write_tag_opts_dropdown, use_tag_opts_radio,\
        image_generated_tags_prompt_builder_textbox, image_generated_tags, tag_effects_dropdown,\
        category_filter_batch_checkbox, category_filter_dropdown, image_confidence_values, video_input,\
        video_input_button, video_clear_button, video_output_dir, convert_video_button, video_frames_gallery,\
        auto_tag_models = \
            custom_dataset_tab_manager.get_tab()
        # share object reference
        gallery_tab_manager.set_file_upload_button_single(file_upload_button_single)
        gallery_tab_manager.set_custom_dataset_tab_manager(custom_dataset_tab_manager)
        extras_tab_manager.set_custom_dataset_tab_manager(custom_dataset_tab_manager)

        ################################################################################################################
        # image editor tab init
        image_editor_tab_manager = Image_editor_tab(gallery_tab_manager, all_images_dict, selected_image_dict,
                                                    all_tags_ever_dict, settings_json, cwd, file_upload_button_single,
                                                    gallery_images_batch, image_mode_choice_state,
                                                    custom_dataset_tab_manager)
        # get vars
        image_editor, send_img_from_default_editor_dropdown, send_img_from_default_editor_button,\
        image_editor_crop, send_img_from_crop_editor_dropdown, send_img_from_crop_editor_button,\
        image_editor_sketch, send_img_from_sketch_editor_dropdown, send_img_from_sketch_editor_button,\
        image_editor_color_sketch, send_img_from_color_editor_dropdown, send_img_from_color_editor_button = \
            image_editor_tab_manager.get_tab()
        # share object reference
        custom_dataset_tab_manager.set_image_editor_manager(image_editor_tab_manager)
        gallery_tab_manager.set_image_editor_tab_manager(image_editor_tab_manager)
        gallery_tab_manager.set_image_editor(image_editor)
        gallery_tab_manager.set_image_editor_crop(image_editor_crop)
        gallery_tab_manager.set_image_editor_sketch(image_editor_sketch)
        gallery_tab_manager.set_image_editor_color_sketch(image_editor_color_sketch)
        gallery_tab_manager.set_gallery_images_batch(gallery_images_batch)

        ################################################################################################################
        # advanced settings tab init
        advanced_settings_tab_manager = Advanced_settings_tab()
        # get vars
        total_suggestions_slider = advanced_settings_tab_manager.get_tab()
        # share object reference
        download_tab_manager.set_advanced_settings_tab_manager(advanced_settings_tab_manager)
        gallery_tab_manager.set_advanced_settings_tab_manager(advanced_settings_tab_manager)

        ################################################################################################################
        ################################################################################################################
        ################################################################################################################

        # initialize all tab manager event listeners
        download_tab_manager.get_event_listeners()
        gallery_tab_manager.get_event_listeners()
        stats_tab_manager.get_event_listeners()
        extras_tab_manager.get_event_listeners()
        custom_dataset_tab_manager.get_event_listeners()
        image_editor_tab_manager.get_event_listeners()

    return demo

def load_trie():
    # Add data to the trie
    global trie, all_tags_ever_dict
    for tag in all_tags_ever_dict.keys():
        trie[tag] = all_tags_ever_dict[tag][1]
    help.verbose_print(f"Done constructing Trie tree!")

def load_tags_csv(proxy_url=None):
    global settings_json
    data = None
    if ("use_csv_custom" in settings_json and settings_json["use_csv_custom"]) and \
            ("csv_custom_path" in settings_json and len(settings_json["csv_custom_path"]) > 0):
        try:
            data = pd.read_csv(settings_json["csv_custom_path"])
            # Check if there is a header
            if data.columns.str.contains('Unnamed').any():
                data = pd.read_csv(settings_json["csv_custom_path"], header=None, skiprows=1)
        except pd.errors.ParserError:
            print("File not found or is not a CSV")

        # take first three columns and name them
        data = data.iloc[:, :3]
        data.columns = ['name', 'category', 'post_count']
    else:
        # check to update the tags csv
        help.check_to_update_csv(proxy_url=proxy_url)
        # get newest
        current_list_of_csvs = help.sort_csv_files_by_date(os.getcwd())
        try:
            # load
            data = pd.read_csv(current_list_of_csvs[0], usecols=['name', 'category', 'post_count'])
        except pd.errors.ParserError:
            print("File not found or is not a CSV")

    # Convert 'name' column to string type
    data['name'] = data['name'].astype(str)
    # Remove rows where post_count equals 0
    data = data[data['post_count'] != 0]

    # Convert the DataFrame into a dictionary
    # where the key is 'name' and the values are lists of [category, post_count]
    global all_tags_ever_dict
    all_tags_ever_dict = data.set_index('name')[['category', 'post_count']].T.to_dict('list')

    # all_tags_ever_dict = copy.deepcopy(data_dict) # this is the part that takes the most time
    del data
    # del data_dict
    # return all_tags_ever_dict

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
    load_tags_csv(proxy_url=args.proxy_url)
    global trie
    trie = datrie.Trie(string.printable)
    load_trie()

    demo = build_ui()

    UI(
        username=args.username,
        password=args.password,
        server_port=args.server_port,
        share=args.share,
    )
