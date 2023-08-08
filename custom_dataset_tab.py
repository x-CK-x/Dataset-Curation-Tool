import gradio as gr
import os
import copy

import md_constants as md_


class Custom_dataset_tab:
    def __init__(self, categories_map, auto_tag_models):
        self.categories_map = categories_map
        self.auto_tag_models = auto_tag_models

    def get_tab(self):
        with gr.Tab("Add Custom Dataset"):
            gr.Markdown(md_.custom)
            image_modes = ['Single', 'Batch']
            if not "Z3D-E621-Convnext" in self.auto_tag_models and os.path.exists(
                    os.path.join(os.getcwd(), 'Z3D-E621-Convnext')) \
                    and os.path.exists(
                os.path.join(os.path.join(os.getcwd(), 'Z3D-E621-Convnext'), 'Z3D-E621-Convnext.onnx')):
                self.auto_tag_models.append('Z3D-E621-Convnext')
            if not "Fluffusion-AutoTag" in self.auto_tag_models and os.path.exists(
                    os.path.join(os.getcwd(), 'Fluffusion-AutoTag')) \
                    and os.path.exists(
                os.path.join(os.path.join(os.getcwd(), 'Fluffusion-AutoTag'), 'Fluffusion-AutoTag.pb')):
                self.auto_tag_models.append('Fluffusion-AutoTag')

            write_tag_opts = ['Overwrite', 'Merge', 'Pre-pend', 'Append']
            use_tag_opts = ['Use All', 'Use All above Threshold', 'Manually Select']
            tag_selection_list = ["(Category) Select Any", "(Category) Clear Any", "(Category) Invert Any",
                                  "Select All", "Clear All", "Invert All"]
            tab_selection = ["Image Default Editor", "Image Crop Editor", "Image Sketch Editor",
                             "Image Color Sketch Editor"]
            with gr.Row():
                with gr.Column():
                    with gr.Accordion(label="Image Settings", visible=True, open=True):
                        with gr.Row():
                            with gr.Tab("Single"):
                                file_upload_button_single = gr.File(label=f"{image_modes[0]} Image Mode",
                                                                    file_count="single",
                                                                    interactive=True, file_types=["image"],
                                                                    visible=True, type="file")
                            with gr.Tab("Batch"):
                                file_upload_button_batch = gr.File(label=f"{image_modes[1]} Image Mode",
                                                                   file_count="directory",
                                                                   interactive=True, visible=True, type="file")
                            with gr.Tab("Non-Interact Batch"):
                                gallery_images_batch = gr.File(label=f"(Non-Interact) {image_modes[1]} Image Mode",
                                                               file_count="multiple",
                                                               interactive=False, visible=True, type="file")
                            with gr.Tab("Image Preview"):
                                with gr.Column():
                                    image_preview_pil = gr.Image(label=f"Image Preview", interactive=False,
                                                                 visible=True, type="pil", height=840)

                        send_img_from_autotag_dropdown = gr.Dropdown(label="Image to Tab Selector",
                                                                     choices=tab_selection)
                        send_img_from_autotag_button = gr.Button(value="Send Image to (Other) Tab", variant='primary')

                    with gr.Accordion(label="Model Settings", visible=True, open=True):
                        with gr.Row():
                            with gr.Column(elem_id="trim_row_length"):
                                cpu_only_ckbx = gr.Checkbox(label="cpu", info="Use cpu only", value=True)
                            with gr.Column(elem_id="trim_row_length"):
                                gr.Markdown("""Refresh""", elem_id="trim_markdown_length")
                                refresh_symbol = '\U0001f504'  # 🔄
                                refresh_models_btn = gr.Button(value=refresh_symbol, variant="variant",
                                                               elem_id="refresh_models_btn")
                            model_choice_dropdown = gr.Dropdown(choices=self.auto_tag_models, label="Model Selection")
                            crop_or_resize_radio = gr.Radio(label="Preprocess Options", choices=['Crop', 'Resize'],
                                                            value='Resize')
                        with gr.Row():
                            landscape_crop_dropdown = gr.Dropdown(choices=['left', 'mid', 'right'],
                                                                  label="Landscape Crop", info="Mandatory",
                                                                  visible=False)
                            portrait_crop_dropdown = gr.Dropdown(choices=['top', 'mid', 'bottom'],
                                                                 label="Portrait Crop", info="Mandatory", visible=False)
                        # with gr.Row():
                        #     square_image_edit_slider = gr.Slider(minimum=0, maximum=3000, step=1, label='Crop/Resize Square Image Size', info='Length or Width', value=448, visible=True, interactive=True)
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
                            with gr.Column(min_width=50, scale=2):
                                save_custom_images_button = gr.Button(value="Save/Add Images", variant='primary')
                            with gr.Column(min_width=50, scale=2):
                                save_custom_tags_button = gr.Button(value="Save/Add Tags", variant='primary')
                        with gr.Row():
                            write_tag_opts_dropdown = gr.Dropdown(label="Write Tag Options", choices=write_tag_opts)
                            use_tag_opts_radio = gr.Dropdown(label="Use Tag Options", choices=use_tag_opts)
                    with gr.Accordion(label="Tag/s Options", visible=True, open=True):
                        image_generated_tags_prompt_builder_textbox = gr.Textbox(label="Prompt String", value="",
                                                                                 visible=True, interactive=False)
                        image_generated_tags = gr.CheckboxGroup(label="Generated Tag/s", choices=[], visible=True,
                                                                interactive=True)
                        with gr.Row():
                            with gr.Column(min_width=50, scale=3):
                                tag_effects_dropdown = gr.Dropdown(label="Tag Selector Effect/s",
                                                                   choices=tag_selection_list)
                            with gr.Column(min_width=50, scale=1):
                                category_filter_batch_checkbox = gr.Checkbox(label="Enable Filter on Batch Mode")
                        with gr.Row():
                            category_filter_dropdown = gr.Dropdown(label="Filter by Category (Multi-Select Enabled)",
                                                                   choices=list(self.categories_map.values()),
                                                                   multiselect=True)
                with gr.Column():
                    with gr.Tab("Tag/s Preview"):
                        with gr.Accordion(label="Tag/s Probabilities", visible=True, open=True):
                            with gr.Column():
                                image_confidence_values = gr.Label(label="Tag/s Confidence/s", visible=True, value={})
                        #         gr.Accordion(label="SAM-HQ Bounding Box Crop", visible=True, open=False)
                        #         gr.Accordion(label="SAM-HQ Segmentation Crop", visible=True, open=False)
                        #         gr.Accordion(label="Upscale", visible=True, open=False)
                        #         gr.Accordion(label="Denoise/Unglaze", visible=True, open=False)
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
                                video_clear_button = gr.ClearButton(label="Clear")
                                with gr.Row():
                                    video_output_dir = gr.Textbox(label="(Optional) Output Folder Path",
                                                                  value=os.getcwd())
                                    convert_video_button = gr.Button(value="Convert Video", variant='primary')
                        with gr.Accordion(label="Gallery Preview", visible=True, open=False):
                            with gr.Column():
                                video_frames_gallery = gr.Gallery(label=f"Video Frame/s Gallery", interactive=False,
                                                                  visible=True, columns=3, object_fit="contain",
                                                                  height=780)
                    # with gr.Tab("UMAP Viewer"):
                    #     with gr.Column():
                    #         gr.Textbox(label="Testing", value="")
                    #         gr.Image(label=f"Image Preview", interactive=False, visible=True, type="pil", height=730)
                    # with gr.Tab("Grad Cam Viewer"):
                    #     with gr.Column():
                    #         gr.Textbox(label="Testing", value="")
                    #         gr.Image(label=f"Image Preview", interactive=False, visible=True, type="pil", height=730)
        return [file_upload_button_single, file_upload_button_batch, gallery_images_batch, image_preview_pil,
                send_img_from_autotag_dropdown, send_img_from_autotag_button, cpu_only_ckbx, refresh_models_btn,
                model_choice_dropdown, crop_or_resize_radio, landscape_crop_dropdown, portrait_crop_dropdown,
                confidence_threshold_slider, interrogate_button, image_with_tag_path_textbox, copy_mode_ckbx,
                save_custom_images_button, save_custom_tags_button, write_tag_opts_dropdown, use_tag_opts_radio,
                image_generated_tags_prompt_builder_textbox, image_generated_tags, tag_effects_dropdown,
                category_filter_batch_checkbox, category_filter_dropdown, image_confidence_values, video_input,
                video_input_button, video_clear_button, video_output_dir, convert_video_button, video_frames_gallery,
                copy.deepcopy(self.auto_tag_models)]