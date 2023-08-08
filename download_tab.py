import glob
import os
import multiprocessing as mp

import gradio as gr

import helper_functions as help
import md_constants as md_

class Download_tab:
    def __init__(self, settings_json, cwd, categories_map, img_extensions, method_tag_files_opts, collect_checkboxes,
                 download_checkboxes, resize_checkboxes, file_extn_list, config_name, required_tags_list,
                 blacklist_tags, auto_config_path):
        self.settings_json = settings_json
        self.cwd = cwd
        self.categories_map = categories_map
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

    def get_tab(self):
        with gr.Tab("Downloading Image/s"):
            config_save_var = gr.Button(value="Apply & Save Settings", variant='primary')
            with gr.Accordion("Edit Requirements for General Download INFO", visible=True, open=True):
                gr.Markdown(md_.general_config)
                with gr.Row():
                    with gr.Column(min_width=50, scale=2):
                        batch_folder = gr.Textbox(lines=1, label='Path to Batch Directory', value=self.settings_json["batch_folder"])
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
                        tag_sep = gr.Textbox(lines=1, label='Tag Separator/Delimeter', value=self.settings_json["tag_sep"])
                    with gr.Column(min_width=50, scale=2):
                        tag_order_format = gr.Textbox(lines=1, label='Tag ORDER', value=self.settings_json["tag_order_format"])
                    with gr.Column(min_width=50, scale=2):
                        prepend_tags = gr.Textbox(lines=1, label='Prepend Tags', value=self.settings_json["prepend_tags"])
                    with gr.Column(min_width=50, scale=2):
                        append_tags = gr.Textbox(lines=1, label='Append Tags', value=self.settings_json["append_tags"])
                with gr.Row():
                    with gr.Column():
                        img_ext = gr.Dropdown(choices=self.img_extensions, label='Image Extension', value=self.settings_json["img_ext"])
                    with gr.Column():
                        method_tag_files = gr.Radio(choices=self.method_tag_files_opts, label='Resized Img Tag Handler', value=self.settings_json["method_tag_files"])
                    with gr.Column():
                        settings_path = gr.Textbox(lines=1, label='Path/Name to \"NEW\" JSON (REQUIRED)', value=self.config_name)
                    create_new_config_checkbox = gr.Checkbox(label="Create NEW Config", value=False)
                    temp = '\\' if help.is_windows() else '/'
                    quick_json_select = gr.Dropdown(choices=sorted([(each_settings_file.split(temp)[-1]) for each_settings_file in glob.glob(os.path.join(self.cwd, f"*.json"))]), label='JSON Select',
                                          value=self.config_name, interactive=True)
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
                    top_n = gr.Slider(minimum=0, maximum=10000, step=1, label='Filter: Top N', value=self.settings_json["top_n"], info='ONLY the top N images will be downloaded')
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
            with gr.Accordion("Edit Requirements for Required Tags", visible=True, open=False):
                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            with gr.Column(min_width=50, scale=3):
                                required_tags_textbox = gr.Textbox(lines=1, label='Press Enter/Space to ADD tag/s', value="")
                            with gr.Column(min_width=50, scale=2):
                                tag_required_suggestion_dropdown = gr.Dropdown(label="Tag Suggestions", choices=[], interactive=True, elem_id="required_dropdown")
                        required_tags_group_var = gr.CheckboxGroup(choices=self.required_tags_list, label='ALL Required Tags',
                                                                   value=[])
                    with gr.Column():
                        file_all_tags_list_required = gr.File(file_count="multiple", file_types=["file"], label="Select ALL files with Tags to be parsed and Added")
                with gr.Row():
                    remove_button_required = gr.Button(value="Remove Checked Tags", variant='secondary')
                    parse_button_required = gr.Button(value="Parse/Add Tags", variant='secondary')
            with gr.Accordion("Edit Requirements for Blacklist Tags", visible=True, open=False):
                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            with gr.Column(min_width=50, scale=3):
                                blacklist_tags_textbox = gr.Textbox(lines=1, label='Press Enter/Space to ADD tag/s', value="")
                            with gr.Column(min_width=50, scale=2):
                                tag_blacklist_suggestion_dropdown = gr.Dropdown(label="Tag Suggestions", choices=[], interactive=True, elem_id="blacklist_dropdown")
                        blacklist_group_var = gr.CheckboxGroup(choices=self.blacklist_tags, label='ALL Blacklisted Tags',
                                                               value=[])
                    with gr.Column():
                        file_all_tags_list_blacklist = gr.File(file_count="multiple", file_types=["file"], label="Select ALL files with Tags to be parsed and Added")
                with gr.Row():
                    remove_button_blacklist = gr.Button(value="Remove Checked Tags", variant='secondary')
                    parse_button_blacklist = gr.Button(value="Parse/Add Tags", variant='secondary')
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
                    remove_tags_list = gr.Textbox(lines=1, label='Path to remove tags file', value=self.settings_json["remove_tags_list"])
                    replace_tags_list = gr.Textbox(lines=1, label='Path to replace tags file', value=self.settings_json["replace_tags_list"])
                    tag_count_list_folder = gr.Textbox(lines=1, label='Path to tag count file', value=self.settings_json["tag_count_list_folder"])
                with gr.Row():
                    remove_now_button = gr.Button(value="Remove Now", variant='primary')
                    replace_now_button = gr.Button(value="Replace Now", variant='primary')
                with gr.Row():
                    keyword_search_text = gr.Textbox(lines=1, label='Keyword/Tag to Search (Optional)')
                    prepend_text = gr.Textbox(lines=1, label='Text to Prepend')
                    prepend_option = gr.Radio(choices=["Start", "End"], label='Prepend/Append Text To:', value="Start")
                with gr.Row():
                    prepend_now_button = gr.Button(value="Prepend/Append Now", variant='primary')
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
                    postscsv = gr.Textbox(lines=1, label='Path to e6 posts csv', value="")
                    tagscsv = gr.Textbox(lines=1, label='Path to e6 tags csv', value="")
                    postsparquet = gr.Textbox(lines=1, label='Path to e6 posts parquet', value="")
                    tagsparquet = gr.Textbox(lines=1, label='Path to e6 tags parquet', value="")
                with gr.Row():
                    images_full_change_dict_textbox = gr.Textbox(lines=1, label='Path to Image Full Change Log JSON (Optional)',
                                                             value=os.path.join(self.auto_config_path, f"auto_complete_{self.settings_json['batch_folder']}.json"))
                    images_full_change_dict_run_button = gr.Button(value="(POST-PROCESSING only) Apply Auto-Config Update Changes", variant='secondary')

            with gr.Row():
                run_button = gr.Button(value="Run", variant='primary')
            with gr.Row():
                progress_bar_textbox_collect = gr.Textbox(interactive=False, visible=False)
            with gr.Row():
                progress_bar_textbox_download = gr.Textbox(interactive=False, visible=False)
            with gr.Row():
                progress_bar_textbox_resize = gr.Textbox(interactive=False, visible=False)
            with gr.Accordion("Batch Run", visible=True, open=False):
                with gr.Row():
                    temp = '\\' if help.is_windows() else '/'
                    all_json_files_checkboxgroup = gr.CheckboxGroup(choices=sorted([(each_settings_file.split(temp)[-1]) for each_settings_file in glob.glob(os.path.join(self.cwd, f"*.json"))]),
                                                                label='Select to Run', value=[])
                with gr.Row():
                    run_button_batch = gr.Button(value="Batch Run", variant='primary')
                with gr.Row():
                    progress_run_batch = gr.Textbox(interactive=False, visible=False)
        return [config_save_var, batch_folder, resized_img_folder, custom_csv_path_textbox, use_csv_custom_checkbox,
                proxy_url_textbox, tag_sep, tag_order_format, prepend_tags, append_tags, img_ext, method_tag_files,
                settings_path, create_new_config_checkbox, quick_json_select, min_score, min_fav_count, min_year,
                min_month, min_day, min_area, top_n, min_short_side, collect_checkbox_group_var,
                download_checkbox_group_var, resize_checkbox_group_var, required_tags_textbox,
                tag_required_suggestion_dropdown, required_tags_group_var, file_all_tags_list_required,
                remove_button_required, parse_button_required, blacklist_tags_textbox,
                tag_blacklist_suggestion_dropdown, blacklist_group_var, file_all_tags_list_blacklist,
                remove_button_blacklist, parse_button_blacklist, skip_posts_file, skip_posts_type,
                save_searched_list_path, save_searched_list_type, apply_filter_to_listed_posts,
                collect_from_listed_posts_type, collect_from_listed_posts_file, downloaded_posts_folder, png_folder,
                jpg_folder, webm_folder, gif_folder, swf_folder, download_remove_tag_file_button,
                reference_model_tags_file, gen_tags_list_button, gen_tags_diff_list_button, save_filename_type,
                remove_tags_list, replace_tags_list, tag_count_list_folder, remove_now_button, replace_now_button,
                keyword_search_text, prepend_text, prepend_option, prepend_now_button, basefolder, numcpu,
                phaseperbatch, keepdb, cachepostsdb, postscsv, tagscsv, postsparquet, tagsparquet,
                images_full_change_dict_textbox, images_full_change_dict_run_button, run_button,
                progress_bar_textbox_collect, progress_bar_textbox_download, progress_bar_textbox_resize,
                all_json_files_checkboxgroup, run_button_batch, progress_run_batch]
