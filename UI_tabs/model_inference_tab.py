import gradio as gr

class Model_inference_tab:
    def __init__(self, logic_manager):
        self.logic = logic_manager

    def render_tab(self):
        with gr.Tab("Model Inference"):
            with gr.Row():
                file_upload_button_single = gr.File(label="Single Image Mode", file_count="single", interactive=True, file_types=["image"], type="filepath")
                file_upload_button_batch = gr.File(label="Batch Image Mode", file_count="directory", interactive=True, type="filepath")
            with gr.Row():
                gpu_ckbx = gr.Checkbox(label="GPU", info="Use GPU", value=False)
                refresh_models_btn = gr.Button(value="\U0001f504", variant="secondary")
                model_choice_dropdown = gr.Dropdown(choices=self.logic.auto_tag_models, label="Model Selection")
            confidence_threshold_slider = gr.Slider(minimum=0, maximum=100, step=1, label="Confidence Threshold", value=75)
            interrogate_button = gr.Button(value="Interrogate", variant='primary')
            with gr.Row():
                image_confidence_values = gr.Label(label="Tag/s Confidence/s", visible=True, value={})
                image_generated_tags = gr.CheckboxGroup(label="Generated Tag/s", choices=[], visible=True, interactive=True)
            image_preview_pil = gr.Image(label="Image Preview", interactive=False, visible=True, type="pil", height=420)
        # expose components on logic manager for other tabs
        self.logic.file_upload_button_single = file_upload_button_single
        self.logic.file_upload_button_batch = file_upload_button_batch
        self.logic.gpu_ckbx = gpu_ckbx
        self.logic.refresh_models_btn = refresh_models_btn
        self.logic.model_choice_dropdown = model_choice_dropdown
        self.logic.confidence_threshold_slider = confidence_threshold_slider
        self.logic.interrogate_button = interrogate_button
        self.logic.image_confidence_values = image_confidence_values
        self.logic.image_generated_tags = image_generated_tags
        self.logic.image_preview_pil = image_preview_pil
        self.logic.gallery_images_batch = None
        self.logic.include_invalid_tags_ckbx = True

        self.file_upload_button_single = file_upload_button_single
        self.file_upload_button_batch = file_upload_button_batch
        self.gpu_ckbx = gpu_ckbx
        self.refresh_models_btn = refresh_models_btn
        self.model_choice_dropdown = model_choice_dropdown
        self.confidence_threshold_slider = confidence_threshold_slider
        self.interrogate_button = interrogate_button
        self.image_confidence_values = image_confidence_values
        self.image_generated_tags = image_generated_tags
        self.image_preview_pil = image_preview_pil
        return [
            file_upload_button_single,
            file_upload_button_batch,
            gpu_ckbx,
            refresh_models_btn,
            model_choice_dropdown,
            confidence_threshold_slider,
            interrogate_button,
            image_confidence_values,
            image_generated_tags,
            image_preview_pil,
        ]

    def get_event_listeners(self):
        self.refresh_models_btn.click(
            fn=self.logic.refresh_model_list,
            inputs=[],
            outputs=[self.model_choice_dropdown],
        )
        self.model_choice_dropdown.select(
            fn=self.logic.load_model,
            inputs=[self.model_choice_dropdown, self.gpu_ckbx],
            outputs=[],
        )
        self.file_upload_button_single.upload(
            fn=self.logic.load_images,
            inputs=[self.file_upload_button_single, self.logic.image_mode_choice_state],
            outputs=[self.logic.image_mode_choice_state],
        )
        self.file_upload_button_batch.upload(
            fn=self.logic.load_images,
            inputs=[self.file_upload_button_batch, self.logic.image_mode_choice_state],
            outputs=[self.logic.image_mode_choice_state],
        )
        self.confidence_threshold_slider.change(
            fn=self.logic.set_threshold,
            inputs=[self.confidence_threshold_slider],
            outputs=[self.image_confidence_values, self.image_generated_tags],
        )
        self.interrogate_button.click(
            fn=self.logic.interrogate_images,
            inputs=[self.logic.image_mode_choice_state, self.confidence_threshold_slider, None, False, None, self.logic.include_invalid_tags_ckbx],
            outputs=[self.image_confidence_values, self.image_generated_tags, self.image_preview_pil, gr.State(None)],
        )

