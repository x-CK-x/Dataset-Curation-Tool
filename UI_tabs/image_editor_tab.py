import shutil

import gradio as gr
import copy
import os

from utils import helper_functions as help


class Image_editor_tab:
    def __init__(self, gallery_tab_manager, download_tab_manager, cwd, image_mode_choice_state, 
                 custom_dataset_tab_manager):
        self.cwd = cwd

        self.download_tab_manager = download_tab_manager
        self.gallery_tab_manager = gallery_tab_manager
        self.custom_dataset_tab_manager = custom_dataset_tab_manager

        self.image_mode_choice_state = image_mode_choice_state


    '''
    new_feature             ::  dropdown menu option
    data                    ::  image/s data being transferred to the component of interest
    no_update_index         ::  (using an integer) to specify the component on the "mapping" list 
                                i.e. ["Auto-Tag Model", "Image Default Editor", "Image Crop Editor", "Image Sketch Editor", "Image Color Sketch Editor"]
    image_id                ::  use/s image id if sending from gallery
    is_batch                ::  true if multiple images being sent
    apply_type_select       ::  use/s file type selection checkboxgroup if sending from gallery
    use_highlight           ::  use/s boolean determining if multiple images are highlighted if sending from gallery
    highlight_select_data   ::  use/s multiple images that are highlighted if sending from gallery
                                state of image mappings represented by index -> [ext, img_id]
    highlight_select        ::  use/s multiple images that are highlighted if sending from gallery
                                JSON list of image ids in the gallery
    '''
    def send_images_from_feature(self, new_feature, data, no_update_index, image_id, is_batch, apply_type_select,
                                 use_highlight, highlight_select_data, highlight_select):

        help.verbose_print(f"data:\t{data}")

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
            gallery_images_batch = self.custom_dataset_tab_manager.gallery_batch_no_update()
            return file_upload_button_single, image_editor, image_editor_crop, image_editor_sketch, \
                   image_editor_color_sketch, gallery_images_batch

        # batch run check
        if is_batch:
            if (len(apply_type_select) > 0 or use_highlight[0]):
                # find type of selected image
                temp_ext = None
                temp_all_images_dict_keys = list(self.gallery_tab_manager.all_images_dict.keys())
                if "searched" in temp_all_images_dict_keys:
                    temp_all_images_dict_keys.remove("searched")
                for each_key in temp_all_images_dict_keys:
                    if image_id in list(self.gallery_tab_manager.all_images_dict[each_key]):
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
                        image_id_list += self.gallery_tab_manager.all_images_dict["searched"][key_type]
                elif ("png" in apply_type_select) or ("jpg" in apply_type_select) or ("gif" in apply_type_select):
                    key_types = copy.copy(apply_type_select)
                    for key_type in key_types:
                        image_id_list += self.gallery_tab_manager.all_images_dict[key_type]
                # help.verbose_print(f"==============================================image_id_list:\t{image_id_list}")
                if use_highlight[0]:
                    temp_id_list = []
                    for index in highlight_select:
                        ext, img_id = highlight_select_data[index]
                        temp_id_list.append(img_id)
                    image_id_list = temp_id_list
                # help.verbose_print(f"==============================================image_id_list:\t{image_id_list}")
                # get the generic paths
                full_path_downloads = os.path.join(os.path.join(self.cwd, self.download_tab_manager.settings_json["batch_folder"]),
                                                   self.download_tab_manager.settings_json["downloaded_posts_folder"])
                # get the type of each image & collect full paths
                full_paths_all = []
                for ext in ["png", "jpg", "gif"]:
                    full_path_gallery_type = os.path.join(full_path_downloads, self.download_tab_manager.settings_json[f"{ext}_folder"])
                    for img_id in image_id_list:
                        if img_id in self.gallery_tab_manager.all_images_dict[ext]:
                            full_path = os.path.join(full_path_gallery_type, f"{img_id}.{ext}")
                            full_paths_all.append(full_path)
                # help.verbose_print(f"++++++++++++++++++++++++++++++++++++++++++++full_paths_all:\t{full_paths_all}")
                file_upload_button_single = gr.update()
                image_editor = gr.update()
                image_editor_crop = gr.update()
                image_editor_sketch = gr.update()
                image_editor_color_sketch = gr.update()
                gallery_images_batch = self.custom_dataset_tab_manager.gallery_batch_set(full_paths_all)
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
            gallery_images_batch = self.custom_dataset_tab_manager.gallery_batch_no_update()
            return file_upload_button_single, image_editor, image_editor_crop, image_editor_sketch, \
                   image_editor_color_sketch, gallery_images_batch

        # 0: auto tag
        # 1: default editor
        # 2: crop
        # 3: sketch
        # 4: color
        for i, tab_opt in enumerate(self.tab_selection):
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
        gallery_images_batch = self.custom_dataset_tab_manager.gallery_batch_no_update()
        # help.verbose_print(f"updates:\t{updates}")
        # help.verbose_print(f"custom_dataset_tab_manager.file_upload_button_single, image_editor, image_editor_crop, image_editor_sketch, image_editor_color_sketch:\t{[custom_dataset_tab_manager.file_upload_button_single, image_editor, image_editor_crop, image_editor_sketch, image_editor_color_sketch]}")
        return file_upload_button_single, image_editor, image_editor_crop, image_editor_sketch, \
               image_editor_color_sketch, gallery_images_batch

    def render_tab(self):
        self.tab_selection = ["Auto-Tag Model", "Image Default Editor", "Image Crop Editor", "Image Sketch Editor",
                              "Image Color Sketch Editor"]
        with gr.Tab("Image Editor"):
            with gr.Tab("Image Editor Tool"):
                with gr.Accordion("Add Image to Edit Here"):
                    # other tabs need to also update this component now also!!!
                    upload_button_single_edit = gr.File(label=f"Upload Image",
                                                   file_count="single",
                                                   interactive=True, file_types=["image"],
                                                   visible=True, type="filepath")

                image_editor = gr.ImageEditor(label=f"Image Default Editor", interactive=True, visible=True, value="imageeditor",
                                        sources=["upload"], type="filepath", height=1028)
                send_img_from_default_editor_dropdown = gr.Dropdown(label="Image to Tab Selector", choices=self.tab_selection)
                send_img_from_default_editor_button = gr.Button(value="Send Image to (Other) Tab", variant='primary')
            with gr.Tab("Image Crop Tool"):
                with gr.Accordion("Add Image to Edit Here"):
                    # other tabs need to also update this component now also!!!
                    upload_button_single_crop = gr.File(label=f"Upload Image",
                                                   file_count="single",
                                                   interactive=True, file_types=["image"],
                                                   visible=True, type="filepath")

                image_editor_crop = gr.ImageEditor(label=f"Image Crop Editor", interactive=True, visible=True,
                                             value="imagemask", sources=["upload"], type="filepath", height=1028)
                send_img_from_crop_editor_dropdown = gr.Dropdown(label="Image to Tab Selector", choices=self.tab_selection)
                send_img_from_crop_editor_button = gr.Button(value="Send Image to (Other) Tab", variant='primary')
            with gr.Tab("Image Sketch Tool"):
                with gr.Accordion("Add Image to Edit Here"):
                    # other tabs need to also update this component now also!!!
                    upload_button_single_sketch = gr.File(label=f"Upload Image",
                                                   file_count="single",
                                                   interactive=True, file_types=["image"],
                                                   visible=True, type="filepath")

                image_editor_sketch = gr.ImageEditor(label=f"Image Sketch Editor", interactive=True, visible=True,
                                               value="sketchpad", sources=["upload"], type="filepath", height=1028)
                send_img_from_sketch_editor_dropdown = gr.Dropdown(label="Image to Tab Selector", choices=self.tab_selection)
                send_img_from_sketch_editor_button = gr.Button(value="Send Image to (Other) Tab", variant='primary')
            with gr.Tab("Image Color Sketch Tool"):
                with gr.Accordion("Add Image to Edit Here"):
                    # other tabs need to also update this component now also!!!
                    upload_button_single_color = gr.File(label=f"Upload Image",
                                                   file_count="single",
                                                   interactive=True, file_types=["image"],
                                                   visible=True, type="filepath")

                image_editor_color_sketch = gr.ImageEditor(label=f"Image Color Sketch Editor", interactive=True, visible=True,
                                                     value="paint", sources=["upload"], type="filepath", height=1028)
                send_img_from_color_editor_dropdown = gr.Dropdown(label="Image to Tab Selector", choices=self.tab_selection)
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
        self.upload_button_single_edit = upload_button_single_edit
        self.upload_button_single_crop = upload_button_single_crop
        self.upload_button_single_sketch = upload_button_single_sketch
        self.upload_button_single_color = upload_button_single_color

        self.upload_data_mapping = {
            self.tab_selection[0]: self.custom_dataset_tab_manager.file_upload_button_single,
            self.tab_selection[1]: self.upload_button_single_edit,
            self.tab_selection[2]: self.upload_button_single_crop,
            self.tab_selection[3]: self.upload_button_single_sketch,
            self.tab_selection[4]: self.upload_button_single_color
        }
        self.editor_data_mapping = {
            self.tab_selection[0]: self.custom_dataset_tab_manager.file_upload_button_single,
            self.tab_selection[1]: self.image_editor,
            self.tab_selection[2]: self.image_editor_crop,
            self.tab_selection[3]: self.image_editor_sketch,
            self.tab_selection[4]: self.image_editor_color_sketch
        }

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
            self.send_img_from_color_editor_button,
            self.upload_button_single_edit,
            self.upload_button_single_crop,
            self.upload_button_single_sketch,
            self.upload_button_single_color
        ]

    def set_editor_type(self, img_path):
        if img_path is None:
            return gr.update(value=None)
        print(f"img_path.name:\t{img_path.name}")
        return gr.update(value=img_path.name)

    def save_image(self, upload_path, edited_data_path):
        temp = '\\' if help.is_windows() else '/'

        upload_path = upload_path.name
        ext = upload_path.split(".")[-1]
        path_w_name_no_ext = ".".join(upload_path.split(".")[:-1])

        path_no_name_no_ext = temp.join(path_w_name_no_ext.split(temp)[:-1])
        just_name = path_w_name_no_ext.split(temp)[-1]

        # path_no_name_no_ext = os.getcwd() # add this in only if absolutely needed (since) it will automatically download to the dataset repo folder as it has no knowledge of where the source images are from

        counter = 0
        while os.path.exists(os.path.join(path_no_name_no_ext, f"{just_name}_{counter}.{ext}")):
            counter += 1
        help.verbose_print(f"Image:\t{os.path.join(path_no_name_no_ext, f'{just_name}_{counter}.{ext}')}\tSAVED!")
        shutil.copy(edited_data_path, f"{os.path.join(path_no_name_no_ext, f'{just_name}_{counter}.{ext}')}")
        return gr.update(value=f"{os.path.join(path_no_name_no_ext, f'{just_name}_{counter}.{ext}')}")

    def get_event_listeners(self):

        self.upload_button_single_edit.change(
            fn=self.set_editor_type,
            inputs=[self.upload_button_single_edit],
            outputs=[self.editor_data_mapping[self.tab_selection[1]]]
        )
        self.upload_button_single_crop.change(
            fn=self.set_editor_type,
            inputs=[self.upload_button_single_crop],
            outputs=[self.editor_data_mapping[self.tab_selection[2]]]
        )
        self.upload_button_single_sketch.change(
            fn=self.set_editor_type,
            inputs=[self.upload_button_single_sketch],
            outputs=[self.editor_data_mapping[self.tab_selection[3]]]
        )
        self.upload_button_single_color.change(
            fn=self.set_editor_type,
            inputs=[self.upload_button_single_color],
            outputs=[self.editor_data_mapping[self.tab_selection[4]]]
        )


        self.send_img_from_default_editor_button.click(
            fn=self.save_image,
            inputs=[self.upload_data_mapping[self.tab_selection[1]], self.editor_data_mapping[self.tab_selection[1]]],
            outputs=[self.upload_data_mapping[self.tab_selection[1]]]
        ).then(
            fn=self.send_images_from_feature,
            inputs=[self.send_img_from_default_editor_dropdown, 
                    self.upload_data_mapping[self.tab_selection[1]],
                    gr.State(1), gr.State(None), gr.State(False), gr.State(None), gr.State(None), gr.State(None), gr.State(None)],
            outputs=[self.upload_data_mapping[self.tab_selection[0]],
                     self.upload_data_mapping[self.tab_selection[1]], 
                     self.upload_data_mapping[self.tab_selection[2]], 
                     self.upload_data_mapping[self.tab_selection[3]], 
                     self.upload_data_mapping[self.tab_selection[4]], 
                     self.custom_dataset_tab_manager.gallery_images_batch]
        ).then(
            fn=self.custom_dataset_tab_manager.load_images,
            inputs=[self.upload_data_mapping[self.tab_selection[1]], self.image_mode_choice_state],
            outputs=[self.image_mode_choice_state]
        )


        self.send_img_from_crop_editor_button.click(
            fn=self.save_image,
            inputs=[self.upload_data_mapping[self.tab_selection[2]], self.editor_data_mapping[self.tab_selection[2]]],
            outputs=[self.upload_data_mapping[self.tab_selection[2]]]
        ).then(
            fn=self.send_images_from_feature,
            inputs=[self.send_img_from_crop_editor_dropdown,
                    self.upload_data_mapping[self.tab_selection[2]],
                    gr.State(2), gr.State(None), gr.State(False), gr.State(None), gr.State(None), gr.State(None), gr.State(None)],
            outputs=[self.upload_data_mapping[self.tab_selection[0]],
                     self.upload_data_mapping[self.tab_selection[1]], 
                     self.upload_data_mapping[self.tab_selection[2]], 
                     self.upload_data_mapping[self.tab_selection[3]], 
                     self.upload_data_mapping[self.tab_selection[4]], 
                     self.custom_dataset_tab_manager.gallery_images_batch]
        ).then(
            fn=self.custom_dataset_tab_manager.load_images,
            inputs=[self.upload_data_mapping[self.tab_selection[2]], self.image_mode_choice_state],
            outputs=[self.image_mode_choice_state]
        )



        self.send_img_from_sketch_editor_button.click(
            fn=self.save_image,
            inputs=[self.upload_data_mapping[self.tab_selection[3]], self.editor_data_mapping[self.tab_selection[3]]],
            outputs=[self.upload_data_mapping[self.tab_selection[3]]]
        ).then(
            fn=self.send_images_from_feature,
            inputs=[self.send_img_from_sketch_editor_dropdown,
                    self.upload_data_mapping[self.tab_selection[3]],
                    gr.State(3), gr.State(None), gr.State(False), gr.State(None), gr.State(None), gr.State(None), gr.State(None)],
            outputs=[self.upload_data_mapping[self.tab_selection[0]],
                     self.upload_data_mapping[self.tab_selection[1]], 
                     self.upload_data_mapping[self.tab_selection[2]], 
                     self.upload_data_mapping[self.tab_selection[3]], 
                     self.upload_data_mapping[self.tab_selection[4]], 
                     self.custom_dataset_tab_manager.gallery_images_batch]
        ).then(
            fn=self.custom_dataset_tab_manager.load_images,
            inputs=[self.upload_data_mapping[self.tab_selection[3]], self.image_mode_choice_state],
            outputs=[self.image_mode_choice_state]
        )



        self.send_img_from_color_editor_button.click(
            fn=self.save_image,
            inputs=[self.upload_data_mapping[self.tab_selection[4]], self.editor_data_mapping[self.tab_selection[4]]],
            outputs=[self.upload_data_mapping[self.tab_selection[4]]]
        ).then(
            fn=self.send_images_from_feature,
            inputs=[self.send_img_from_color_editor_dropdown,
                    self.upload_data_mapping[self.tab_selection[4]],
                    gr.State(4), gr.State(None), gr.State(False), gr.State(None), gr.State(None), gr.State(None), gr.State(None)],
            outputs=[self.upload_data_mapping[self.tab_selection[0]],
                     self.upload_data_mapping[self.tab_selection[1]], 
                     self.upload_data_mapping[self.tab_selection[2]], 
                     self.upload_data_mapping[self.tab_selection[3]], 
                     self.upload_data_mapping[self.tab_selection[4]], 
                     self.custom_dataset_tab_manager.gallery_images_batch]
        ).then(
            fn=self.custom_dataset_tab_manager.load_images,
            inputs=[self.upload_data_mapping[self.tab_selection[4]], self.image_mode_choice_state],
            outputs=[self.image_mode_choice_state]
        )
