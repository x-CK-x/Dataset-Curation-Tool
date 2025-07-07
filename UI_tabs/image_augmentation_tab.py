import gradio as gr

class Image_augmentation_tab:
    def __init__(self, logic_manager):
        self.logic = logic_manager

    def render_tab(self):
        with gr.Tab("Image Augmentation"):
            operation_choices = ["Crop", "Zoom", "Resize", "Rotate", "Scale", "Translation",
                                "Brightness", "Contrast", "Saturation", "Noise", "Shear", "Horizontal Flip", "Vertical Flip"]
            operations_dropdown = gr.Dropdown(choices=operation_choices, multiselect=True, label="Preprocess Options", interactive=True, value=[])
            with gr.Row():
                landscape_crop_dropdown = gr.Dropdown(choices=['left', 'mid', 'right', None], label="Landscape Crop", info="Mandatory", visible=False)
                portrait_crop_dropdown = gr.Dropdown(choices=['top', 'mid', 'bottom', None], label="Portrait Crop", info="Mandatory", visible=False)
            zoom_slider = gr.Slider(minimum=0.5, maximum=3.0, value=1.0, step=0.1, label="Zoom Value", visible=False)
            rotate_slider = gr.Slider(minimum=-180, maximum=180, step=1, value=0, visible=False, label="Rotate Value")
            scale_slider = gr.Slider(minimum=0.5, maximum=2, step=0.05, value=1, visible=False, label="Scale Value")
            dx_slider = gr.Slider(minimum=-100, maximum=100, step=1, value=0, visible=False, label="Translation-X Value")
            dy_slider = gr.Slider(minimum=-100, maximum=100, step=1, value=0, visible=False, label="Translation-Y Value")
            brightness_slider = gr.Slider(minimum=0.5, maximum=2, step=0.05, value=1, visible=False, label="Brightness Value")
            contrast_slider = gr.Slider(minimum=0.5, maximum=2, step=0.05, value=1, visible=False, label="Contrast Value")
            saturation_slider = gr.Slider(minimum=0.5, maximum=2, step=0.05, value=1, visible=False, label="Saturation Value")
            noise_slider = gr.Slider(minimum=0, maximum=100, step=1, value=0, visible=False, label="Noise Value")
            shear_slider = gr.Slider(minimum=-0.5, maximum=0.5, step=0.05, value=0, visible=False, label="Shear Value")
        # expose components on logic manager
        self.logic.operations_dropdown = operations_dropdown
        self.logic.landscape_crop_dropdown = landscape_crop_dropdown
        self.logic.portrait_crop_dropdown = portrait_crop_dropdown
        self.logic.zoom_slider = zoom_slider
        self.logic.rotate_slider = rotate_slider
        self.logic.scale_slider = scale_slider
        self.logic.dx_slider = dx_slider
        self.logic.dy_slider = dy_slider
        self.logic.brightness_slider = brightness_slider
        self.logic.contrast_slider = contrast_slider
        self.logic.saturation_slider = saturation_slider
        self.logic.noise_slider = noise_slider
        self.logic.shear_slider = shear_slider

        self.operations_dropdown = operations_dropdown
        self.landscape_crop_dropdown = landscape_crop_dropdown
        self.portrait_crop_dropdown = portrait_crop_dropdown
        self.zoom_slider = zoom_slider
        self.rotate_slider = rotate_slider
        self.scale_slider = scale_slider
        self.dx_slider = dx_slider
        self.dy_slider = dy_slider
        self.brightness_slider = brightness_slider
        self.contrast_slider = contrast_slider
        self.saturation_slider = saturation_slider
        self.noise_slider = noise_slider
        self.shear_slider = shear_slider

        return [operations_dropdown]

    def get_event_listeners(self):
        self.operations_dropdown.change(
            fn=self.logic.make_menus_visible,
            inputs=[self.operations_dropdown],
            outputs=[self.landscape_crop_dropdown, self.portrait_crop_dropdown, self.zoom_slider, self.rotate_slider,
                     self.scale_slider, self.dx_slider, self.dy_slider, self.brightness_slider, self.contrast_slider,
                     self.saturation_slider, self.noise_slider, self.shear_slider],
        )
        self.zoom_slider.change(fn=self.logic.set_zoom_slider, inputs=[self.zoom_slider], outputs=[])
        self.rotate_slider.change(fn=self.logic.set_rotate_slider, inputs=[self.rotate_slider], outputs=[])
        self.scale_slider.change(fn=self.logic.set_scale_slider, inputs=[self.scale_slider], outputs=[])
        self.dx_slider.change(fn=self.logic.set_dx_slider, inputs=[self.dx_slider], outputs=[])
        self.dy_slider.change(fn=self.logic.set_dy_slider, inputs=[self.dy_slider], outputs=[])
        self.brightness_slider.change(fn=self.logic.set_brightness_slider, inputs=[self.brightness_slider], outputs=[])
        self.contrast_slider.change(fn=self.logic.set_contrast_slider, inputs=[self.contrast_slider], outputs=[])
        self.saturation_slider.change(fn=self.logic.set_saturation_slider, inputs=[self.saturation_slider], outputs=[])
        self.noise_slider.change(fn=self.logic.set_noise_slider, inputs=[self.noise_slider], outputs=[])
        self.shear_slider.change(fn=self.logic.set_shear_slider, inputs=[self.shear_slider], outputs=[])
        self.landscape_crop_dropdown.select(fn=self.logic.set_landscape_square_crop, inputs=[self.landscape_crop_dropdown], outputs=[])
        self.portrait_crop_dropdown.select(fn=self.logic.set_portrait_square_crop, inputs=[self.portrait_crop_dropdown], outputs=[])

