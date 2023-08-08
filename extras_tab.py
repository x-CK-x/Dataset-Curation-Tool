import gradio as gr

import md_constants as md_

class Extras_tab:
    def get_tab(self):
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
        return [repo_download_releases_only, repo_download_checkbox_group, repo_download_radio, release_options_radio,
                release_assets_checkbox_group, repo_download_button, model_download_types,
                tagging_model_download_types, model_download_checkbox_group, nested_model_links_checkbox_group,
                model_download_button]