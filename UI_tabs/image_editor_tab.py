import gradio as gr
import copy
import os

from utils import helper_functions as help


class Image_editor_tab:
    def __init__(self, gallery_tab_manager, all_images_dict, selected_image_dict, all_tags_ever_dict, settings_json,
                 cwd, file_upload_button_single, gallery_images_batch, image_mode_choice_state,
                 custom_dataset_tab_manager):
        self.all_images_dict = all_images_dict
        self.selected_image_dict = selected_image_dict
        self.all_tags_ever_dict = all_tags_ever_dict
        self.settings_json = settings_json
        self.cwd = cwd

        self.gallery_tab_manager = gallery_tab_manager
        self.custom_dataset_tab_manager = custom_dataset_tab_manager

        self.file_upload_button_single = file_upload_button_single
        self.gallery_images_batch = gallery_images_batch
        self.image_mode_choice_state = image_mode_choice_state



    def send_images_from_feature(self, new_feature, data, no_update_index, image_id, is_batch,
                                 apply_type_select, use_highlight, highlight_select_data, highlight_select):
        if image_id is not None and len(image_id) > 0:
            image_id = str(image_id)

        # help.verbose_print(f"new_feature:\t{new_feature}")

        if data is None:
            # help.verbose_print(f"NONE!!!")
            file_upload_button_single = gr.update()
            image_editor = gr.update()
            image_editor_crop = gr.update()
            image_editor_sketch = gr.update()
            image_editor_color_sketch = gr.update()
            gallery_images_batch = gr.update()
            return file_upload_button_single, image_editor, image_editor_crop, image_editor_sketch, \
                   image_editor_color_sketch, gallery_images_batch

        # batch run check
        if is_batch:
            if (len(apply_type_select) > 0 or use_highlight[0]):
                # find type of selected image
                temp_ext = None
                temp_all_images_dict_keys = list(self.all_images_dict.keys())
                if "searched" in temp_all_images_dict_keys:
                    temp_all_images_dict_keys.remove("searched")
                for each_key in temp_all_images_dict_keys:
                    if image_id in list(self.all_images_dict[each_key]):
                        temp_ext = each_key
                        break
                # reload the categories for the selected_image_dict
                if len(highlight_select) == 0 and not use_highlight[0]:
                    self.gallery_tab_manager.reload_selected_image_dict(temp_ext, image_id)

                image_id_list = []
                if "searched" in apply_type_select and (("png" in apply_type_select) or
                                                        ("jpg" in apply_type_select) or ("gif" in apply_type_select)):
                    key_types = copy.copy(apply_type_select)
                    key_types.remove("searched")
                    for key_type in key_types:
                        image_id_list += self.all_images_dict["searched"][key_type]
                elif ("png" in apply_type_select) or ("jpg" in apply_type_select) or ("gif" in apply_type_select):
                    key_types = copy.copy(apply_type_select)
                    for key_type in key_types:
                        image_id_list += self.all_images_dict[key_type]
                # help.verbose_print(f"==============================================image_id_list:\t{image_id_list}")
                if use_highlight[0]:
                    temp_id_list = []
                    for index in highlight_select:
                        ext, img_id = highlight_select_data[index]
                        temp_id_list.append(img_id)
                    image_id_list = temp_id_list
                # help.verbose_print(f"==============================================image_id_list:\t{image_id_list}")
                # get the generic paths
                full_path_downloads = os.path.join(os.path.join(self.cwd, self.settings_json["batch_folder"]),
                                                   self.settings_json["downloaded_posts_folder"])
                # get the type of each image & collect full paths
                full_paths_all = []
                for ext in ["png", "jpg", "gif"]:
                    full_path_gallery_type = os.path.join(full_path_downloads, self.settings_json[f"{ext}_folder"])
                    for img_id in image_id_list:
                        if img_id in self.all_images_dict[ext]:
                            full_path = os.path.join(full_path_gallery_type, f"{img_id}.{ext}")
                            full_paths_all.append(full_path)
                # help.verbose_print(f"++++++++++++++++++++++++++++++++++++++++++++full_paths_all:\t{full_paths_all}")
                file_upload_button_single = gr.update()
                image_editor = gr.update()
                image_editor_crop = gr.update()
                image_editor_sketch = gr.update()
                image_editor_color_sketch = gr.update()
                gallery_images_batch = gr.update(value=full_paths_all)
                return file_upload_button_single, image_editor, image_editor_crop, image_editor_sketch, \
                       image_editor_color_sketch, gallery_images_batch

        help.verbose_print(f"data:\t{data}")
        if isinstance(data, list):
            # get image id path and set data equal to it
            temp_data = None
            for image_data in data:
                help.verbose_print(f"image_data:\t{image_data}")
                if image_id in image_data["name"]:
                    help.verbose_print(f"image_id:\t{image_id}")
                    help.verbose_print(f"image_data['name']:\t{image_data['name']}")
                    temp_data = image_data["name"]
                    break
            data = temp_data
        elif isinstance(data, str):
            data = data
        elif isinstance(data, dict):
            data = data["image"]
        else:
            print(f"type:\t{type(data)}")
            data = data.name

        tab_selection = ["Auto-Tag Model", "Image Default Editor", "Image Crop Editor", "Image Sketch Editor",
                         "Image Color Sketch Editor"]

        # help.verbose_print(f"image:\t{image}")

        updates = [[None], [None], [None], [None], [None]]
        if no_update_index > -1:
            updates[no_update_index] = data

        if new_feature is None or len(new_feature) == 0:
            help.verbose_print(f"updates:\t{updates}")
            help.verbose_print(f"new_feature:\t{new_feature}")
            file_upload_button_single = gr.update(value=updates[0]) if updates[0][0] else gr.update()
            image_editor = gr.update(value=updates[1]) if updates[1][0] else gr.update()
            image_editor_crop = gr.update(value=updates[2]) if updates[2][0] else gr.update()
            image_editor_sketch = gr.update(value=updates[3]) if updates[3][0] else gr.update()
            image_editor_color_sketch = gr.update(value=updates[4]) if updates[4][0] else gr.update()
            gallery_images_batch = gr.update()
            return file_upload_button_single, image_editor, image_editor_crop, image_editor_sketch, \
                   image_editor_color_sketch, gallery_images_batch

        # 0: auto tag
        # 1: default editor
        # 2: crop
        # 3: sketch
        # 4: color
        for i, tab_opt in enumerate(tab_selection):
            if new_feature in tab_opt:
                updates[i] = data
                break

        help.verbose_print(f"updates:\t{updates}")
        help.verbose_print(f"new_feature:\t{new_feature}")
        help.verbose_print(f"data:\t{data}")
        file_upload_button_single = gr.update(value=updates[0]) if updates[0][0] is not None else gr.update()
        image_editor = gr.update(value=updates[1]) if updates[1][0] is not None else gr.update()
        image_editor_crop = gr.update(value=updates[2]) if updates[2][0] is not None else gr.update()
        image_editor_sketch = gr.update(value=updates[3]) if updates[3][0] is not None else gr.update()
        image_editor_color_sketch = gr.update(value=updates[4]) if updates[4][0] is not None else gr.update()
        gallery_images_batch = gr.update()
        # help.verbose_print(f"updates:\t{updates}")
        # help.verbose_print(f"file_upload_button_single, image_editor, image_editor_crop, image_editor_sketch, image_editor_color_sketch:\t{[file_upload_button_single, image_editor, image_editor_crop, image_editor_sketch, image_editor_color_sketch]}")
        return file_upload_button_single, image_editor, image_editor_crop, image_editor_sketch, \
               image_editor_color_sketch, gallery_images_batch

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


        self.image_editor = image_editor
        self.send_img_from_default_editor_dropdown = send_img_from_default_editor_dropdown
        self.send_img_from_default_editor_button = send_img_from_default_editor_button
        self.image_editor_crop = image_editor_crop
        self.send_img_from_crop_editor_dropdown = send_img_from_crop_editor_dropdown
        self.send_img_from_crop_editor_button = send_img_from_crop_editor_button
        self.image_editor_sketch = image_editor_sketch
        self.send_img_from_sketch_editor_dropdown = send_img_from_sketch_editor_dropdown
        self.send_img_from_sketch_editor_button = send_img_from_sketch_editor_button
        self.image_editor_color_sketch = image_editor_color_sketch
        self.send_img_from_color_editor_dropdown = send_img_from_color_editor_dropdown
        self.send_img_from_color_editor_button = send_img_from_color_editor_button

        return [
            self.image_editor,
            self.send_img_from_default_editor_dropdown,
            self.send_img_from_default_editor_button,
            self.image_editor_crop,
            self.send_img_from_crop_editor_dropdown,
            self.send_img_from_crop_editor_button,
            self.image_editor_sketch,
            self.send_img_from_sketch_editor_dropdown,
            self.send_img_from_sketch_editor_button,
            self.image_editor_color_sketch,
            self.send_img_from_color_editor_dropdown,
            self.send_img_from_color_editor_button
        ]

    def get_event_listeners(self):
        self.send_img_from_default_editor_button.click(
            fn=self.send_images_from_feature,
            inputs=[self.send_img_from_default_editor_dropdown, self.image_editor, gr.State(1), gr.State(None),
                    gr.State(False), gr.State(None), gr.State(None), gr.State(None), gr.State(None)],
            outputs=[self.file_upload_button_single, self.image_editor, self.image_editor_crop, self.image_editor_sketch,
                     self.image_editor_color_sketch, self.gallery_images_batch]
        ).then(
            fn=self.custom_dataset_tab_manager.load_images,
            inputs=[self.file_upload_button_single,self. image_mode_choice_state],
            outputs=[self.image_mode_choice_state]
        )
        self.send_img_from_crop_editor_button.click(
            fn=self.send_images_from_feature,
            inputs=[self.send_img_from_crop_editor_dropdown, self.image_editor_crop, gr.State(2), gr.State(None),
                    gr.State(False), gr.State(None), gr.State(None), gr.State(None), gr.State(None)],
            outputs=[self.file_upload_button_single, self.image_editor, self.image_editor_crop, self.image_editor_sketch,
                     self.image_editor_color_sketch, self.gallery_images_batch]
        ).then(
            fn=self.custom_dataset_tab_manager.load_images,
            inputs=[self.file_upload_button_single, self.image_mode_choice_state],
            outputs=[self.image_mode_choice_state]
        )
        self.send_img_from_sketch_editor_button.click(
            fn=self.send_images_from_feature,
            inputs=[self.send_img_from_sketch_editor_dropdown, self.image_editor_sketch, gr.State(3), gr.State(None),
                    gr.State(False), gr.State(None), gr.State(None), gr.State(None), gr.State(None)],
            outputs=[self.file_upload_button_single, self.image_editor, self.image_editor_crop, self.image_editor_sketch,
                     self.image_editor_color_sketch, self.gallery_images_batch]
        ).then(
            fn=self.custom_dataset_tab_manager.load_images,
            inputs=[self.file_upload_button_single, self.image_mode_choice_state],
            outputs=[self.image_mode_choice_state]
        )
        self.send_img_from_color_editor_button.click(
            fn=self.send_images_from_feature,
            inputs=[self.send_img_from_color_editor_dropdown, self.image_editor_color_sketch, gr.State(4), gr.State(None),
                    gr.State(False), gr.State(None), gr.State(None), gr.State(None), gr.State(None)],
            outputs=[self.file_upload_button_single, self.image_editor, self.image_editor_crop, self.image_editor_sketch,
                     self.image_editor_color_sketch, self.gallery_images_batch]
        ).then(
            fn=self.custom_dataset_tab_manager.load_images,
            inputs=[self.file_upload_button_single, self.image_mode_choice_state],
            outputs=[self.image_mode_choice_state]
        )