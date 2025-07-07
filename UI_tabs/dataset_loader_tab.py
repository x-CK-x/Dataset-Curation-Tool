import gradio as gr
from utils import md_constants as md_

class Dataset_loader_tab:
    def __init__(self, gallery_tab_manager):
        self.gallery_tab_manager = gallery_tab_manager

    def render_tab(self):
        with gr.Tab("Add Custom Dataset"):
            gr.Markdown(md_.custom)
            with gr.Row():
                dataset_gallery_path_textbox = gr.Textbox(
                    label="Dataset Folder Path",
                    info="Folder with images and tag txt files",
                    interactive=True,
                    elem_id="dataset_gallery_path_textbox",
                )
                load_dataset_gallery_button = gr.Button(
                    value="Load Dataset to Gallery",
                    variant="secondary",
                    elem_id="load_dataset_gallery_button",
                )
        self.dataset_gallery_path_textbox = dataset_gallery_path_textbox
        self.load_dataset_gallery_button = load_dataset_gallery_button
        return [self.dataset_gallery_path_textbox, self.load_dataset_gallery_button]

    def get_event_listeners(self):
        self.load_dataset_gallery_button.click(
            fn=self.gallery_tab_manager.reset_gallery_component_only,
            inputs=None,
            outputs=[self.gallery_tab_manager.gallery_comp, self.gallery_tab_manager.total_image_counter],
        ).then(
            fn=self.gallery_tab_manager.load_external_dataset,
            inputs=[self.dataset_gallery_path_textbox],
            outputs=[self.gallery_tab_manager.gallery_comp, self.gallery_tab_manager.total_image_counter],
        )
