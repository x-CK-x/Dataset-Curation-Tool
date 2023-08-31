import gradio as gr
import os
import argparse

from utils import css_constants as css_, helper_functions as help
from utils.features.tag_suggestions.tag_suggest import Tag_Suggest
from utils.features.image_boards.image_board_manager import Image_Board

def build_ui():
    from UI_tabs.download_tab import Download_tab
    from UI_tabs.gallery_tab import Gallery_tab
    from UI_tabs.stats_tab import Stats_tab
    from UI_tabs.extras_tab import Extras_tab
    from UI_tabs.custom_dataset_tab import Custom_dataset_tab
    from UI_tabs.image_editor_tab import Image_editor_tab
    from UI_tabs.advanced_settings_tab import Advanced_settings_tab

    with gr.Blocks(css=f"{css_.preview_hide_rule} {css_.refresh_aspect_btn_rule} {css_.trim_row_length} {css_.trim_markdown_length} "
                       f"{css_.thumbnail_colored_border_css} {css_.refresh_models_btn_rule}"
                       f"{css_.green_button_css} {css_.red_button_css}") as demo:# {css_.gallery_fix_height}

        # set local path
        cwd = os.getcwd()
        # options
        img_extensions = ["png", "jpg", "same_as_original"]
        method_tag_files_opts = ["relocate", "copy"]
        collect_checkboxes = ["include_tag_file", "include_explicit_tag", "include_questionable_tag",
                              "include_safe_tag",
                              "include_png", "include_jpg", "include_gif", "include_webm", "include_swf",
                              "include_explicit",
                              "include_questionable", "include_safe"]
        download_checkboxes = ["skip_post_download", "reorder_tags", "replace_underscores", "remove_parentheses",
                               "do_sort"]
        resize_checkboxes = ["skip_resize", "delete_original"]
        file_extn_list = ["png", "jpg", "gif"]

        artist_csv_dict = {} ##################### eventually this will get migrated to the image_board_manager class!!!
        character_csv_dict = {} ##################### eventually this will get migrated to the image_board_manager class!!!
        species_csv_dict = {} ##################### eventually this will get migrated to the image_board_manager class!!!
        general_csv_dict = {} ##################### eventually this will get migrated to the image_board_manager class!!!
        meta_csv_dict = {} ##################### eventually this will get migrated to the image_board_manager class!!!
        rating_csv_dict = {} ##################### eventually this will get migrated to the image_board_manager class!!!
        tags_csv_dict = {} ##################### eventually this will get migrated to the image_board_manager class!!!


        all_predicted_confidences = {}
        all_predicted_tags = []
        repo_release_urls = {}
        autotagmodel = None
        selected_image_dict = None  ### key:category, value:tag_list  # set on every click ::  # id -> {categories: tag/s}, type -> string
        is_csv_loaded = False
        config_name = "settings.json"
        settings_json = help.load_session_config(os.path.join(cwd, config_name))

        image_board = Image_Board(config_path=os.path.join(cwd, "captioning", "image_boards", "e6.json"))

        required_tags_list = help.get_list(settings_json["required_tags"], settings_json["tag_sep"])

        for tag in required_tags_list:
            if len(tag) == 0:
                required_tags_list.remove(tag)
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


        all_images_dict = {}  ### add images by key:id, value:selected_image_dict
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
        image_creation_times = {}
        all_tags_ever_dict = {}

        help.verbose_print(f"EVERYTHING INITIALIZING")
        help.verbose_print(f"Initial check to download & load tags CSV")
        help.preprocess_csv(proxy_url=args.proxy_url, settings_json=settings_json,
                            all_tags_ever_dict=all_tags_ever_dict, invalid_categories=image_board.get_invalid_categories())
        all_tags_ever_dict = help.load_tags_csv_fast()

        #####################
        ### Gradio States ###
        #####################

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

        ##################################
        ### Tab Manager Initialization ###
        ##################################

        ################################################################################################################
        # download tab init
        download_tab_manager = Download_tab(settings_json, cwd, image_board, img_extensions, method_tag_files_opts,
                                            collect_checkboxes, download_checkboxes, resize_checkboxes, file_extn_list,
                                            config_name, required_tags_list, blacklist_tags, auto_config_path,
                                            initial_required_state,
                                            initial_required_state_tag, relevant_required_categories,
                                            initial_blacklist_state, initial_blacklist_state_tag,
                                            relevant_blacklist_categories, auto_complete_config
                                            )
        # render tab
        download_tab_manager.render_tab()

        ################################################################################################################
        # gallery tab init
        gallery_tab_manager = Gallery_tab(file_extn_list, image_board, cwd, multi_select_ckbx_state,
                                          only_selected_state_object, images_selected_state, image_mode_choice_state,
                                          previous_search_state_text, current_search_state_placement_tuple,
                                          relevant_search_categories, initial_add_state, initial_add_state_tag,
                                          relevant_add_categories, images_tuple_points, download_tab_manager,
                                          auto_complete_config_name, all_tags_ever_dict, all_images_dict,
                                          selected_image_dict, artist_csv_dict, character_csv_dict, species_csv_dict,
                                          general_csv_dict, meta_csv_dict, rating_csv_dict, tags_csv_dict,
                                          image_creation_times, is_csv_loaded
                                          )
        # render tab
        gallery_tab_manager.render_tab()
        # share object reference
        download_tab_manager.set_gallery_tab_manager(gallery_tab_manager)

        ################################################################################################################
        # stats tab init
        stats_tab_manager = Stats_tab(gallery_tab_manager)
        # render tab
        stats_tab_manager.render_tab()

        ################################################################################################################
        # extras tab init
        extras_tab_manager = Extras_tab(repo_release_urls)
        # render tab
        extras_tab_manager.render_tab()

        ################################################################################################################
        # custom dataset tab init
        custom_dataset_tab_manager = Custom_dataset_tab(image_board, cwd, download_tab_manager, gallery_tab_manager,
                                                        image_mode_choice_state, autotagmodel,
                                                        all_predicted_confidences, all_predicted_tags
                                                        )
        # render tab
        custom_dataset_tab_manager.render_tab()
        # share object reference
        gallery_tab_manager.set_custom_dataset_tab_manager(custom_dataset_tab_manager)
        extras_tab_manager.set_custom_dataset_tab_manager(custom_dataset_tab_manager)

        ################################################################################################################
        # image editor tab init
        image_editor_tab_manager = Image_editor_tab(gallery_tab_manager, download_tab_manager, cwd,
                                                    image_mode_choice_state, custom_dataset_tab_manager
                                                    )
        # render tab
        image_editor_tab_manager.render_tab()
        # share object reference
        custom_dataset_tab_manager.set_image_editor_manager(image_editor_tab_manager)
        gallery_tab_manager.set_image_editor_tab_manager(image_editor_tab_manager)

        ################################################################################################################
        # advanced settings tab init
        advanced_settings_tab_manager = Advanced_settings_tab()
        # render tab
        advanced_settings_tab_manager.render_tab()
        # share object reference
        download_tab_manager.set_advanced_settings_tab_manager(advanced_settings_tab_manager)
        gallery_tab_manager.set_advanced_settings_tab_manager(advanced_settings_tab_manager)

        ################################################################################################################
        ################################################################################################################
        ################################################################################################################

        # initialize tag suggestion feature
        tag_ideas = Tag_Suggest(all_tags_ever_dict, gallery_tab_manager, download_tab_manager)
        download_tab_manager.set_tag_ideas(tag_ideas)
        gallery_tab_manager.set_tag_ideas(tag_ideas)

        # initialize all tab manager event listeners
        download_tab_manager.get_event_listeners()
        gallery_tab_manager.get_event_listeners()
        stats_tab_manager.get_event_listeners()
        extras_tab_manager.get_event_listeners()
        custom_dataset_tab_manager.get_event_listeners()
        image_editor_tab_manager.get_event_listeners()
    return demo

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

    demo = build_ui()

    UI(
        username=args.username,
        password=args.password,
        server_port=args.server_port,
        share=args.share,
    )
