import gradio as gr

import md_constants as md_

class Gallery_tab:
    def __init__(self, file_extn_list, categories_map):
        self.file_extn_list = file_extn_list
        self.categories_map = categories_map

    def get_tab(self):
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
                                                                         choices=["new-to-old", "old-to-new"], value="",
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
                            tag_remove_button = gr.Button(value="Remove Selected Tag/s", variant='primary')
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
                                    choices=list(self.categories_map.values()), multiselect=True)
                            with gr.Column(min_width=50, scale=1):
                                tag_effects_gallery_dropdown = gr.Dropdown(label="Tag Selector Effect/s",
                                                                           choices=tag_selection_list)

                        img_artist_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Artist Tag/s', value=[])
                        img_character_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Character Tag/s',
                                                                            value=[])
                        img_species_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Species Tag/s', value=[])
                        img_general_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='General Tag/s', value=[])
                        img_meta_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Meta Tag/s', value=[])
                        img_rating_tag_checkbox_group = gr.CheckboxGroup(choices=[], label='Rating Tag/s', value=[])
                gallery_comp = gr.Gallery(visible=False, elem_id="gallery_id", columns=3, object_fit="contain",
                                          height=1032)
        return [refresh_aspect_btn, download_folder_type, img_id_textbox, tag_search_textbox,
                tag_search_suggestion_dropdown, apply_to_all_type_select_checkboxgroup,
                select_multiple_images_checkbox, select_between_images_checkbox, apply_datetime_sort_ckbx,
                apply_datetime_choice_menu, image_remove_button, image_save_ids_button, send_img_from_gallery_dropdown,
                batch_send_from_gallery_checkbox, send_img_from_gallery_button, tag_remove_button, tag_save_button,
                tag_add_textbox, tag_add_suggestion_dropdown, category_filter_gallery_dropdown,
                tag_effects_gallery_dropdown, img_artist_tag_checkbox_group, img_character_tag_checkbox_group,
                img_species_tag_checkbox_group, img_general_tag_checkbox_group, img_meta_tag_checkbox_group,
                img_rating_tag_checkbox_group, gallery_comp]