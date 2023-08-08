import gradio as gr

class Image_editor_tab:
    def get_tab(self):
        with gr.Tab("Image Editor"):
            tab_selection = ["Auto-Tag Model", "Image Default Editor", "Image Crop Editor", "Image Sketch Editor", "Image Color Sketch Editor"]
            with gr.Tab("Image Editor Tool"):
                image_editor = gr.Image(label=f"Image Default Editor", interactive=True, visible=True, tool="editor",
                                        source="upload", type="filepath", height=1028)
                send_img_from_default_editor_dropdown = gr.Dropdown(label="Image to Tab Selector", choices=tab_selection)
                send_img_from_default_editor_button = gr.Button(value="Send Image to (Other) Tab", variant='primary')
            with gr.Tab("Image Crop Tool"):
                image_editor_crop = gr.Image(label=f"Image Crop Editor", interactive=True, visible=True,
                                             tool="select", source="upload", type="filepath", height=1028)
                send_img_from_crop_editor_dropdown = gr.Dropdown(label="Image to Tab Selector", choices=tab_selection)
                send_img_from_crop_editor_button = gr.Button(value="Send Image to (Other) Tab", variant='primary')
            with gr.Tab("Image Sketch Tool"):
                image_editor_sketch = gr.Image(label=f"Image Sketch Editor", interactive=True, visible=True,
                                               tool="sketch", source="upload", type="filepath", height=1028)
                send_img_from_sketch_editor_dropdown = gr.Dropdown(label="Image to Tab Selector", choices=tab_selection)
                send_img_from_sketch_editor_button = gr.Button(value="Send Image to (Other) Tab", variant='primary')
            with gr.Tab("Image Color Sketch Tool"):
                image_editor_color_sketch = gr.Image(label=f"Image Color Sketch Editor", interactive=True, visible=True,
                                                     tool="color-sketch", source="upload", type="filepath", height=1028)
                send_img_from_color_editor_dropdown = gr.Dropdown(label="Image to Tab Selector", choices=tab_selection)
                send_img_from_color_editor_button = gr.Button(value="Send Image to (Other) Tab", variant='primary')
        return [image_editor, send_img_from_default_editor_dropdown, send_img_from_default_editor_button,
                image_editor_crop, send_img_from_crop_editor_dropdown, send_img_from_crop_editor_button,
                image_editor_sketch, send_img_from_sketch_editor_dropdown, send_img_from_sketch_editor_button,
                image_editor_color_sketch, send_img_from_color_editor_dropdown, send_img_from_color_editor_button]