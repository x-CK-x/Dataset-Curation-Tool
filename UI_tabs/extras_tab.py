import gradio as gr

from utils import md_constants as md_, helper_functions as help


class Extras_tab:
    def __init__(self, repo_release_urls):
        self.repo_release_urls = repo_release_urls

        self.custom_dataset_tab_manager = None

    def set_custom_dataset_tab_manager(self, custom_dataset_tab_manager):
        self.custom_dataset_tab_manager = custom_dataset_tab_manager




    def make_visible(self):
        return gr.update(visible=True)

    def get_repo_assets(self, release_options_radio, event_data: gr.SelectData):
        # get header text
        header_text = (event_data.value)
        # get assets available
        help.verbose_print(f"self.repo_release_urls[header_text]:\t{self.repo_release_urls[header_text]}")
        all_assets = self.repo_release_urls[header_text]
        help.verbose_print(f"all_assets:\t{all_assets}")

        repo_download_button = gr.update(visible=True)
        release_assets_checkbox_group = gr.update(choices=all_assets, visible=True)
        return repo_download_button, release_assets_checkbox_group

    def get_repo_releases(self, repo_download_radio, event_data: gr.SelectData):
        self.repo_release_urls = {}
        release_options_radio_list, self.repo_release_urls = help.get_repo_releases(event_data)
        release_options_radio = gr.update(choices=release_options_radio_list, visible=True, value=[])
        return release_options_radio

    def reload_release_options(self, repo_download_releases_only):
        if repo_download_releases_only:
            # make visible the radio options & hide the repo_download_checkbox_group options, repo_specific_release_options, and button
            repo_download_checkbox_group = gr.update(visible=False)
            release_options_radio = gr.update(visible=False)
            repo_download_button = gr.update(visible=False)
            release_assets_checkbox_group = gr.update(visible=False)
            repo_download_radio = gr.update(visible=True)
        else:
            # make visible the repo_download_checkbox_group options & button and hide the radio options & repo_specific_release_options
            repo_download_checkbox_group = gr.update(visible=True)
            release_options_radio = gr.update(value=[], visible=False)
            repo_download_button = gr.update(visible=True)
            repo_download_radio = gr.update(visible=False)
            release_assets_checkbox_group = gr.update(visible=False)
        return repo_download_checkbox_group, repo_download_radio, release_options_radio, repo_download_button, release_assets_checkbox_group

    def download_repos(self, repo_download_releases_only, repo_download_checkbox_group, release_assets_checkbox_group,
                       repo_download_radio):
        help.download_repos(repo_download_releases_only, repo_download_checkbox_group, release_assets_checkbox_group,
                            repo_download_radio)

    def show_model_downloads_options(self, model_download_types, event_data: gr.SelectData):
        model_download_checkbox_group = gr.update(choices=help.get_model_names(event_data.value), visible=True)
        model_download_button = gr.update(visible=True)
        nested_model_links_checkbox_group = gr.update(visible=True)
        return model_download_checkbox_group, model_download_button, nested_model_links_checkbox_group

    def show_nested_fluffyrock_models(self, nested_model_links_checkbox_group):
        model_download_checkbox_group = gr.update(visible=True)
        model_download_button = gr.update(visible=True)
        nested_model_links_checkbox_group = gr.update(visible=True, choices=help.get_nested_fluffyrock_models(
            nested_model_links_checkbox_group))
        return model_download_checkbox_group, model_download_button, nested_model_links_checkbox_group

    def download_models(self, model_download_types, model_download_checkbox_group, tagging_model_download_types,
                        nested_model_links_checkbox_group):
        self.custom_dataset_tab_manager.auto_tag_models = help.download_models(model_download_types, model_download_checkbox_group,
                                               tagging_model_download_types, nested_model_links_checkbox_group)

        model_download_types = gr.update(value=None)
        tagging_model_download_types = gr.update(value=None)
        nested_model_links_checkbox_group = gr.update(value=None)

        file_upload_button_single = None
        file_upload_button_batch = None
        gallery_images_batch = None
        if tagging_model_download_types is not None and len(tagging_model_download_types) > 0:
            file_upload_button_single = gr.update(value=None)
            file_upload_button_batch = gr.update(value=None)
            gallery_images_batch = gr.update(value=None)

        return model_download_types, tagging_model_download_types, nested_model_links_checkbox_group, \
               file_upload_button_single, file_upload_button_batch, gallery_images_batch

    def render_tab(self):
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
                # SD model/s
                model_download_options = ["Fluffusion", "FluffyRock"]
                # Auto-Tag model/s
                tagging_model_download_options = ["Z3D-E621-Convnext",
                                                  "eva02-clip-vit-large-7704",
                                                  "eva02-vit-large-448-8046",
                                                  "experimental_efficientnetv2_m_8035"]

                model_download_types = gr.Dropdown(choices=model_download_options, label='Diffusion Model Selection', value=None)
                tagging_model_download_types = gr.Dropdown(choices=tagging_model_download_options, label='AutoTagging Model Selection', multiselect=True, value=None)
                model_download_checkbox_group = gr.CheckboxGroup(choices=[], label='Select ALL Code Repositories to Download', value=[], visible=False)
                nested_model_links_checkbox_group = gr.CheckboxGroup(choices=[], label='Specific Model Versions', value=[],
                                                                 visible=False)
                model_download_button = gr.Button(value="Download Model/s", variant='primary', visible=False)

        self.repo_download_releases_only = repo_download_releases_only
        self.repo_download_checkbox_group = repo_download_checkbox_group
        self.repo_download_radio = repo_download_radio
        self.release_options_radio = release_options_radio
        self.release_assets_checkbox_group = release_assets_checkbox_group
        self.repo_download_button = repo_download_button
        self.model_download_types = model_download_types
        self.tagging_model_download_types = tagging_model_download_types
        self.model_download_checkbox_group = model_download_checkbox_group
        self.nested_model_links_checkbox_group = nested_model_links_checkbox_group
        self.model_download_button = model_download_button

        return [
                self.repo_download_releases_only,
                self.repo_download_checkbox_group,
                self.repo_download_radio,
                self.release_options_radio,
                self.release_assets_checkbox_group,
                self.repo_download_button,
                self.model_download_types,
                self.tagging_model_download_types,
                self.model_download_checkbox_group,
                self.nested_model_links_checkbox_group,
                self.model_download_button
                ]

    def get_event_listeners(self):
        self.tagging_model_download_types.select(
            fn=self.make_visible,
            inputs=[],
            outputs=[self.model_download_button]
        )
        self.release_options_radio.select(
            fn=self.get_repo_assets,
            inputs=[self.release_options_radio],
            outputs=[self.repo_download_button, self.release_assets_checkbox_group]
        )
        self.repo_download_radio.select(
            fn=self.get_repo_releases,
            inputs=[self.repo_download_radio],
            outputs=[self.release_options_radio]
        )
        self.repo_download_releases_only.change(
            fn=self.reload_release_options,
            inputs=[self.repo_download_releases_only],
            outputs=[self.repo_download_checkbox_group, self.repo_download_radio, self.release_options_radio, self.repo_download_button,
                     self.release_assets_checkbox_group]
        )
        self.repo_download_button.click(
            fn=self.download_repos,
            inputs=[self.repo_download_releases_only, self.repo_download_checkbox_group, self.release_assets_checkbox_group,
                    self.repo_download_radio],
            outputs=[]
        )
        self.model_download_types.select(
            fn=self.show_model_downloads_options,
            inputs=[self.model_download_types],
            outputs=[self.model_download_checkbox_group, self.model_download_button, self.nested_model_links_checkbox_group]
        )
        self.model_download_checkbox_group.change(
            fn=self.show_nested_fluffyrock_models,
            inputs=[self.model_download_checkbox_group],
            outputs=[self.model_download_checkbox_group, self.model_download_button, self.nested_model_links_checkbox_group]
        )
        self.model_download_button.click(
            fn=self.download_models,
            inputs=[self.model_download_types, self.model_download_checkbox_group, self.tagging_model_download_types,
                    self.nested_model_links_checkbox_group],
            outputs=[self.model_download_types, self.tagging_model_download_types, self.nested_model_links_checkbox_group,
                     self.custom_dataset_tab_manager.file_upload_button_single,
                     self.custom_dataset_tab_manager.file_upload_button_batch,
                     self.custom_dataset_tab_manager.gallery_images_batch]
        ).then( # update the model list in the custom dataset tab
            fn=self.custom_dataset_tab_manager.refresh_model_list,
            inputs=[],
            outputs=[self.custom_dataset_tab_manager.model_choice_dropdown]
        )
