import copy
import os
from tqdm import tqdm
import numpy as np
import math
import multiprocessing as mp
import pandas as pd
import heapq
import shutil

import torch
import onnxruntime as ort

from utils import helper_functions as help
from utils.features.captioning import image_data_loader

class AutoTag:
    def __init__(self, labels_file="tags-selected.csv", batch_size=1, max_data_loader_n_workers=math.ceil(mp.cpu_count()/2),
                 caption_extension='.txt', debug=True, dest_folder=None, tag_folder=None):
        self.categories_map = {0: 'general', 1: 'artist', 2: 'rating', 3: 'copyright', 4: 'character', 5: 'species', 6: 'invalid',
                              7: 'meta', 8: 'lore'}
        self.valid_categories = {'artist': 0, 'character': 1, 'species': 2, 'general': 3, 'meta': 4, 'rating': 5}
        self.labels_file = labels_file
        self.caption_extension = caption_extension
        self.batch_size = batch_size
        self.max_data_loader_n_workers = max_data_loader_n_workers
        self.debug = debug
        self.crop_or_resize = 'resize'
        self.global_image_predictions_predictions = []
        self.landscape_square_crop = None
        self.portrait_square_crop = None
        self.global_images_list = []
        self.thresh = 50
        self.write_tag_opts_dropdown = None
        self.use_tag_opts_radio = None
        self.image_with_tag_path_textbox = ""
        self.copy_mode_ckbx = False
        self.dataset = None
        self.model_dir = None
        self.dest_folder = dest_folder
        self.tag_folder = tag_folder
        self.crop_image_size = 448
        self.filter_in_categories = None
        self.filter_in_checkbox = None
        self.image_paths = None

    def set_crop_image_size(self, crop_image_size):
        if '.onnx' in self.model_name:
            self.crop_image_size = 448
        else:
            self.crop_image_size = crop_image_size
        return self.crop_image_size

    def load_model(self, model_dir="", model_name="", use_cpu=True):
        self.model_name = model_name
        self.model_dir = model_dir
        self.use_cpu = use_cpu
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        if self.use_cpu:
            del providers[0]
        self.ort_sess = ort.InferenceSession(os.path.join(self.model_dir, self.model_name), providers=providers)

    def get_dataset(self):
        return self.dataset

    def get_model_name(self):
        return self.model_name

    def get_model_dir(self):
        return self.model_dir

    def get_image_paths(self):
        return self.image_paths

    def set_threshold(self, thresh):
        self.thresh = thresh

    def set_image_with_tag_path_textbox(self, image_with_tag_path_textbox):
        self.image_with_tag_path_textbox = image_with_tag_path_textbox

    def set_copy_mode_ckbx(self, copy_mode_ckbx):
        self.copy_mode_ckbx = copy_mode_ckbx

    def set_write_tag_opts(self, write_tag_opts_dropdown):
        self.write_tag_opts_dropdown = write_tag_opts_dropdown

    def set_use_tag_opts(self, use_tag_opts_radio):
        self.use_tag_opts_radio = use_tag_opts_radio

    def set_crop_or_resize(self, crop_or_resize='resize'):
        self.crop_or_resize = crop_or_resize
        print(f"is now:\t{self.crop_or_resize}")

    def set_landscape_square_crop(self, landscape_square_crop=None):
        self.landscape_square_crop = landscape_square_crop

    def set_portrait_square_crop(self, portrait_square_crop=None):
        self.portrait_square_crop = portrait_square_crop

    def set_data(self, train_data_dir=None, single_image=False):
        self.train_data_dir = train_data_dir
        self.model_dir = os.path.join(os.getcwd(), 'Z3D-E621-Convnext')

        help.verbose_print(f"self.model_dir:\t{self.model_dir}")

        self.label_names = pd.read_csv(os.path.join(self.model_dir, self.labels_file))

        if single_image and (('.png' in self.train_data_dir) or ('.jpg' in self.train_data_dir)):
            self.image_paths = [self.train_data_dir]
        else:
            temp = '\\' if help.is_windows() else '/'
            self.image_paths = [path for path in self.train_data_dir if
                                   (path.split(temp)[-1]).split('.')[-1] == 'png' or (path.split(temp)[-1]).split('.')[-1] == 'jpg']

    def glob_images_pathlib(self, dir_path, extension_list):
        image_paths = []
        for ext in extension_list:
            image_paths += list(dir_path.rglob("*" + ext))
        image_paths = list(set(image_paths))
        image_paths.sort()
        return image_paths

    def set_image_size(self, crop_size):
        self.crop_image_size = crop_size

    def collate_fn_remove_corrupted(self, batch):
        # Filter out all the Nones (corrupted examples)
        batch = list(filter(lambda x: x is not None, batch))
        return batch

    def run_batch(self, path_imgs, single_image, all_tags_ever_dict):
        self.global_image_predictions_predictions = []
        imgs = np.array([im for _, im in path_imgs])
        input_name = self.ort_sess.get_inputs()[0].name
        label_name = self.ort_sess.get_outputs()[0].name
        outputs = self.ort_sess.run([label_name], {input_name: imgs})

        temp = '\\' if help.is_windows() else '/'
        for i, output in enumerate(outputs[0]):
            self.combined_tags = {}
            self.label_names["probs"] = output
            found_tags = None
            # get image name
            image_name = ((path_imgs[i][0]).split(temp)[-1]).split('.')[0]
            image_ext = ((path_imgs[i][0]).split(temp)[-1]).split('.')[-1]
            src = self.image_with_tag_path_textbox
            dst = self.dest_folder

            temp_src_image_path = os.path.join(src, f"{image_name}.{image_ext}")
            temp_src_tags_path = os.path.join(src, f"{image_name}.txt")

            temp_dst_image_path = os.path.join(dst, f"{image_name}.{image_ext}")
            temp_dst_tags_path = os.path.join(dst, f"{image_name}.txt")

            if single_image:
                found_tags = self.label_names[self.label_names["probs"] > float(0)][["name", "probs"]]
                found_tags = found_tags.values.tolist()

                # help.verbose_print(f"found_tags:\t{found_tags}")

                # remove tags not in csv or not a valid category type
                found_tags = [tag for tag in found_tags if (tag[0] in all_tags_ever_dict) and
                              (self.categories_map[all_tags_ever_dict[tag[0]][0]] in self.valid_categories)]

                # set predictions for the UI
                for element in found_tags:
                    self.combined_tags[element[0]] = [element[1], f"{image_name}.{image_ext}"]  # tag -> [probability, name w/ extension]
            else:
                if self.use_tag_opts_radio == 'Use All above Threshold':
                    print(f"(float(self.thresh) / 100.0):\t{(float(self.thresh) / 100.0)}")
                    found_tags = self.label_names[(self.label_names["probs"] > (float(self.thresh)/100.0))][["name", "probs"]]
                elif self.use_tag_opts_radio == 'Use All' or self.use_tag_opts_radio == 'Manually Select':
                    found_tags = self.label_names[self.label_names["probs"] > float(0)][["name", "probs"]]
                else:
                    raise ValueError("batch use tag operation NOT set")
                # convert to list
                found_tags = found_tags.values.tolist()
                # remove tags not in csv or not a valid category type
                found_tags = [tag for tag in found_tags if (tag[0] in all_tags_ever_dict) and
                              (self.categories_map[all_tags_ever_dict[tag[0]][0]] in self.valid_categories)]

                # user selected categories filter (optional)
                if self.filter_in_checkbox:
                    found_tags = [tag for tag in found_tags if (self.categories_map[all_tags_ever_dict[tag[0]][0]]) in self.filter_in_categories]

                # set predictions for the UI
                for element in found_tags:
                    self.combined_tags[element[0]] = [element[1], f"{image_name}.{image_ext}"]  # tag -> [probability, name w/ extension]

                # sort by category
                sorted_list = sorted(found_tags, key=lambda x: self.valid_categories[self.categories_map[all_tags_ever_dict[x[0]][0]]])
                sorted_list = [pair[0] for pair in sorted_list] # get just the tags

                # Load image tags from file and sort them into the same kind of this sorted by category
                existing_tags = []
                if os.path.exists(temp_src_tags_path): # extract tags
                    existing_tags = help.parse_single_all_tags(temp_src_tags_path)
                else: # make file and set tags list to empty
                    # create a new file & assumes NO tags
                    f = open(temp_src_tags_path, 'w')
                    f.close()
                # sort by category
                sorted_existing_tags_list = sorted(existing_tags, key=lambda x: self.valid_categories[self.categories_map[all_tags_ever_dict[x][0]]])

                # remove duplicate tag/s in generated tag list
                sorted_list1_set = set(sorted_existing_tags_list)
                filtered_sorted_list2 = [tag for tag in sorted_list if tag not in sorted_list1_set]
                filtered_sorted_list2 = sorted(filtered_sorted_list2, key=lambda x: self.valid_categories[self.categories_map[all_tags_ever_dict[x][0]]])

                merged_list = []
                if self.write_tag_opts_dropdown == 'Merge':
                    # merge the two sorted lists by category
                    merged_list = list(heapq.merge(sorted_existing_tags_list, filtered_sorted_list2, key=lambda x: self.valid_categories[self.categories_map[all_tags_ever_dict[x][0]]]))
                elif self.write_tag_opts_dropdown == 'Pre-pend':
                    # pre-pend the generated list to the existing one
                    merged_list = filtered_sorted_list2 + sorted_existing_tags_list
                elif self.write_tag_opts_dropdown == 'Append':
                    # append the generated list to the existing one
                    merged_list = sorted_existing_tags_list + filtered_sorted_list2
                elif self.write_tag_opts_dropdown == 'Overwrite':
                    merged_list = sorted_list
                else:
                    raise ValueError("batch write tag operation NOT set")

                # create tag string
                tag_string = ', '.join(merged_list)
                # save local
                help.write_tags_to_text_file(tag_string, temp_src_tags_path)
                if self.copy_mode_ckbx: # copy to dataset directory
                    help.write_tags_to_text_file(tag_string, temp_dst_tags_path)
                    # copy image over
                    shutil.copy(temp_src_image_path, temp_dst_image_path)

                artist_csv_dict = {}
                character_csv_dict = {}
                species_csv_dict = {}
                general_csv_dict = {}
                meta_csv_dict = {}
                rating_csv_dict = {}
                tags_csv_dict = {}

                # check if csv dictionaries EXIST yet (i.e. from having downloaded images & tags)
                if os.path.exists(os.path.join(self.tag_folder, "tags.csv")):
                    # load csv dictionaries
                    artist_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(self.tag_folder, "artist.csv"))
                    character_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(self.tag_folder, "character.csv"))
                    species_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(self.tag_folder, "species.csv"))
                    general_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(self.tag_folder, "general.csv"))
                    meta_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(self.tag_folder, "meta.csv"))
                    rating_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(self.tag_folder, "rating.csv"))
                    tags_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(self.tag_folder, "tags.csv"))

                # update existing csvs
                for tag in merged_list:
                    artist_csv_dict, character_csv_dict, species_csv_dict, \
                    general_csv_dict, meta_csv_dict, rating_csv_dict, \
                    tags_csv_dict = help.update_all_csv_dictionaries(copy.deepcopy(artist_csv_dict),
                                                                     copy.deepcopy(character_csv_dict),
                                                                     copy.deepcopy(species_csv_dict),
                                                                     copy.deepcopy(general_csv_dict),
                                                                     copy.deepcopy(meta_csv_dict),
                                                                     copy.deepcopy(rating_csv_dict),
                                                                     copy.deepcopy(tags_csv_dict),
                                                                     self.categories_map[all_tags_ever_dict[tag][0]], tag, "+", 1)
                # persist changes to csv dictionary files
                help.write_tags_to_csv(artist_csv_dict, os.path.join(self.tag_folder, "artist.csv"))
                help.write_tags_to_csv(character_csv_dict, os.path.join(self.tag_folder, "character.csv"))
                help.write_tags_to_csv(species_csv_dict, os.path.join(self.tag_folder, "species.csv"))
                help.write_tags_to_csv(general_csv_dict, os.path.join(self.tag_folder, "general.csv"))
                help.write_tags_to_csv(meta_csv_dict, os.path.join(self.tag_folder, "meta.csv"))
                help.write_tags_to_csv(rating_csv_dict, os.path.join(self.tag_folder, "rating.csv"))
                help.write_tags_to_csv(tags_csv_dict, os.path.join(self.tag_folder, "tags.csv"))

            self.global_image_predictions_predictions = [copy.deepcopy(self.combined_tags)] # only keeps most recent prediction
            del self.combined_tags

    def interrogate(self, single_image, all_tags_ever_dict, filter_in_categories, filter_in_checkbox):
        data = None

        self.filter_in_categories = filter_in_categories
        self.filter_in_checkbox = filter_in_checkbox

        if self.global_image_predictions_predictions is not None:
            del self.global_image_predictions_predictions
        self.global_image_predictions_predictions = []

        if self.global_images_list is not None:
            del self.global_images_list
        self.global_images_list = []

        if self.dataset is not None:
            del self.dataset
        self.dataset = None

        if data is not None:
            del data

        if self.max_data_loader_n_workers is not None:
            self.dataset = image_data_loader.ImageLoadingPrepDataset(copy.deepcopy(self.image_paths))

            self.dataset.set_crop_image_size(self.crop_image_size)
            print(f"self.dataset.crop_image_size is now:\t{self.dataset.crop_image_size}")
            self.dataset.set_crop_or_resize(self.crop_or_resize)
            print(f"self.crop_or_resize is now:\t{self.crop_or_resize}")
            print(f"self.dataset.crop_or_resize is now:\t{self.dataset.crop_or_resize}")
            self.dataset.set_portrait_square_crop(self.portrait_square_crop)
            self.dataset.set_landscape_square_crop(self.landscape_square_crop)
            print(f"self.dataset.portrait_square_crop is now:\t{self.dataset.portrait_square_crop}")
            print(f"self.dataset.landscape_square_crop is now:\t{self.dataset.landscape_square_crop}")
            print(f"=============================")

            data = None
            if help.is_windows():
                data = torch.utils.data.DataLoader(
                    self.dataset,
                    batch_size=self.batch_size,
                    shuffle=False,
                    collate_fn=self.collate_fn_remove_corrupted,
                    drop_last=False,
                )
            else:
                data = torch.utils.data.DataLoader(
                    self.dataset,
                    batch_size=self.batch_size,
                    num_workers=self.max_data_loader_n_workers,
                    shuffle=False,
                    collate_fn=self.collate_fn_remove_corrupted,
                    drop_last=False,
                )
        else:
            data = [[(None, ip)] for ip in self.image_paths]
        self.global_images_list = []
        b_imgs = []

        for entry in tqdm(data, smoothing=0.0):
            for image_data in entry:
                if image_data is None:
                    continue
                image, image_path = image_data
                if image is not None:
                    image = image.detach().numpy()
                    self.global_images_list.append(copy.deepcopy(image))
                else:
                    try:
                        image = self.dataset.smart_imread(image_path)
                        image = self.dataset.preprocess_image(image)
                        self.global_images_list.append(copy.deepcopy(image))
                    except Exception as e:
                        print(f"Could not load image path {image_path}, error: {e}")
                        continue
                b_imgs.append((image_path, image))

                if len(b_imgs) >= self.batch_size:
                    b_imgs = [(str(image_path), image) for image_path, image in b_imgs]  # Convert image_path to string
                    self.run_batch(b_imgs, single_image, all_tags_ever_dict)
                    b_imgs.clear()

        if len(b_imgs) > 0:
            b_imgs = [(str(image_path), image) for image_path, image in b_imgs]  # Convert image_path to string
            self.run_batch(b_imgs, single_image, all_tags_ever_dict)

        print("done!")

    def get_predictions(self, single_image):####### gets a list of -> tag -> [prob, image_name.ext]
        # print(f"self.global_image_predictions_predictions:\t{self.global_image_predictions_predictions}")

        if single_image:
            image_dict = self.global_image_predictions_predictions[0]
            keys = image_dict.keys()
            answer = copy.deepcopy({key: float(image_dict[key][0]) for key in keys}), copy.deepcopy(list(keys)), copy.deepcopy(self.global_images_list[0])
            return answer
        else:
            return {}, [], None

    def save_tags(self, single_image, any_selected_tags, all_tags_ever_dict):
        if single_image:
            #self.global_image_predictions_predictions### gets a list of -> tag -> [prob, image_name.ext]
            print(f"self.dataset.get_image_paths():\t{self.dataset.get_image_paths()}")
            image_path = self.dataset.get_image_paths()[-1]
            temp = '\\' if help.is_windows() else '/'
            # get image name
            image_name = (image_path.split(temp)[-1]).split('.')[0]
            image_ext = (image_path.split(temp)[-1]).split('.')[-1]
            src = self.image_with_tag_path_textbox
            dst = self.dest_folder

            # temp_src_image_path = os.path.join(src, f"{image_name}.{image_ext}")
            temp_src_tags_path = os.path.join(src, f"{image_name}.txt")

            # temp_dst_image_path = os.path.join(dst, f"{image_name}.{image_ext}")
            temp_dst_tags_path = os.path.join(dst, f"{image_name}.txt")

            print(f"self.use_tag_opts_radio:\t{self.use_tag_opts_radio}")
            print(f"self.write_tag_opts_dropdown:\t{self.write_tag_opts_dropdown}")
            print(f"(float(self.thresh) / 100.0):\t{(float(self.thresh) / 100.0)}")
            if self.use_tag_opts_radio == 'Use All above Threshold':
                temp_list = list(
                    self.global_image_predictions_predictions[0].keys())  # tag -> [probability, name w/ extension]
                any_selected_tags = [tag for tag in temp_list if float(self.global_image_predictions_predictions[0][tag][0]) > (float(self.thresh) / 100.0)]
            elif self.use_tag_opts_radio == 'Use All':
                temp_list = list(
                    self.global_image_predictions_predictions[0].keys())  # tag -> [probability, name w/ extension]
                any_selected_tags = temp_list
            elif self.use_tag_opts_radio == 'Manually Select':
                any_selected_tags = any_selected_tags
            else:
                raise ValueError("batch use tag operation NOT set")

            # remove tags not in csv or not a valid category type
            any_selected_tags = [tag for tag in any_selected_tags if (tag in all_tags_ever_dict) and
                                 (self.categories_map[all_tags_ever_dict[tag][0]] in self.valid_categories)]

            # sort by category
            sorted_list = sorted(any_selected_tags, key=lambda x: self.valid_categories[self.categories_map[all_tags_ever_dict[x][0]]])

            # Load image tags from file and sort them into the same kind of this sorted by category
            existing_tags = []
            if os.path.exists(temp_src_tags_path):  # extract tags
                existing_tags = help.parse_single_all_tags(temp_src_tags_path)
            else:  # make file and set tags list to empty
                # create a new file & assumes NO tags
                f = open(temp_src_tags_path, 'w')
                f.close()
            # sort by category
            sorted_existing_tags_list = sorted(existing_tags, key=lambda x: self.valid_categories[self.categories_map[all_tags_ever_dict[x][0]]])

            # remove duplicate tag/s in generated tag list
            sorted_list1_set = set(sorted_existing_tags_list)
            filtered_sorted_list2 = [tag for tag in sorted_list if tag not in sorted_list1_set]

            filtered_sorted_list2 = sorted(filtered_sorted_list2,
                                           key=lambda x: self.valid_categories[self.categories_map[all_tags_ever_dict[x][0]]])

            merged_list = []
            if self.write_tag_opts_dropdown == 'Merge':
                # merge the two sorted lists by category
                merged_list = list(heapq.merge(sorted_existing_tags_list, filtered_sorted_list2,
                                                   key=lambda x: self.valid_categories[self.categories_map[all_tags_ever_dict[x][0]]]))
            elif self.write_tag_opts_dropdown == 'Pre-pend':
                # pre-pend the generated list to the existing one
                merged_list = filtered_sorted_list2 + sorted_existing_tags_list
            elif self.write_tag_opts_dropdown == 'Append':
                # append the generated list to the existing one
                merged_list = sorted_existing_tags_list + filtered_sorted_list2
            elif self.write_tag_opts_dropdown == 'Overwrite':
                merged_list = sorted_list
            else:
                raise ValueError("batch write tag operation NOT set")

            # create tag string
            tag_string = ', '.join(merged_list)
            print(f"temp_src_tags_path:\t{temp_src_tags_path}")
            print(f"temp_dst_tags_path:\t{temp_dst_tags_path}")

            # save local
            help.write_tags_to_text_file(tag_string, temp_src_tags_path)
            if self.copy_mode_ckbx: # copy to dataset directory
                help.write_tags_to_text_file(tag_string, temp_dst_tags_path)

            artist_csv_dict = {}
            character_csv_dict = {}
            species_csv_dict = {}
            general_csv_dict = {}
            meta_csv_dict = {}
            rating_csv_dict = {}
            tags_csv_dict = {}

            # check if csv dictionaries EXIST yet (i.e. from having downloaded images & tags)
            if os.path.exists(os.path.join(self.tag_folder, "tags.csv")):
                # load csv dictionaries
                artist_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(self.tag_folder, "artist.csv"))
                character_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(self.tag_folder, "character.csv"))
                species_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(self.tag_folder, "species.csv"))
                general_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(self.tag_folder, "general.csv"))
                meta_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(self.tag_folder, "meta.csv"))
                rating_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(self.tag_folder, "rating.csv"))
                tags_csv_dict = help.parse_csv_all_tags(csv_file_path=os.path.join(self.tag_folder, "tags.csv"))

            # update existing csvs
            for tag in merged_list:
                artist_csv_dict, character_csv_dict, species_csv_dict, \
                general_csv_dict, meta_csv_dict, rating_csv_dict, \
                tags_csv_dict = help.update_all_csv_dictionaries(copy.deepcopy(artist_csv_dict),
                                                                 copy.deepcopy(character_csv_dict),
                                                                 copy.deepcopy(species_csv_dict),
                                                                 copy.deepcopy(general_csv_dict),
                                                                 copy.deepcopy(meta_csv_dict),
                                                                 copy.deepcopy(rating_csv_dict),
                                                                 copy.deepcopy(tags_csv_dict),
                                                                 self.categories_map[all_tags_ever_dict[tag][0]], tag, "+", 1)
            # persist changes to csv dictionary files
            help.write_tags_to_csv(artist_csv_dict, os.path.join(self.tag_folder, "artist.csv"))
            help.write_tags_to_csv(character_csv_dict, os.path.join(self.tag_folder, "character.csv"))
            help.write_tags_to_csv(species_csv_dict, os.path.join(self.tag_folder, "species.csv"))
            help.write_tags_to_csv(general_csv_dict, os.path.join(self.tag_folder, "general.csv"))
            help.write_tags_to_csv(meta_csv_dict, os.path.join(self.tag_folder, "meta.csv"))
            help.write_tags_to_csv(rating_csv_dict, os.path.join(self.tag_folder, "rating.csv"))
            help.write_tags_to_csv(tags_csv_dict, os.path.join(self.tag_folder, "tags.csv"))

