from PIL import Image
import cv2
import numpy as np
import torch
import math
import copy

class ImageLoadingPrepDataset(torch.utils.data.Dataset):
    def __init__(self, image_paths):
        self.images = image_paths
        self.images = [path for path in self.images if not (".txt" in path)]

        self.crop_or_resize = 'resize'
        self.portrait_square_crop = None
        self.landscape_square_crop = None
        self.global_images_list = []

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path = str(self.images[idx])
        try:
            image = self.smart_imread(img_path)
            image = self.preprocess_image(image)
            tensor = torch.tensor(image)
        except Exception as e:
            print(f"Could not load image path: {img_path}, error: {e}")
            return None
        return (tensor, img_path)

    def get_image_paths(self):
        return self.images

    def set_crop_image_size(self, crop_image_size):
        self.crop_image_size = crop_image_size

    def set_crop_or_resize(self, crop_or_resize):
        self.crop_or_resize = crop_or_resize

    def set_portrait_square_crop(self, portrait_square_crop):
        self.portrait_square_crop = portrait_square_crop

    def set_landscape_square_crop(self, landscape_square_crop):
        self.landscape_square_crop = landscape_square_crop

    def get_global_images_list(self):
        # print(f"self.global_images_list:\t{self.global_images_list}")
        return copy.deepcopy(self.global_images_list)

    def preprocess_image(self, image):
        return self.partial_image_crop_button(image)

    def smart_imread(self, image, flag=cv2.IMREAD_UNCHANGED):
        if image.endswith(".gif"):
            image = Image.open(image)
            if image.mode != "RGB":
                image = image.convert("RGB")
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        else:
            image = cv2.imread(image, flag)
        image_without_alpha = image[:, :, :3]
        return image_without_alpha

    def pad_image(self, image):
        print('pad image')
        # pad to square
        original_max_length = max(image.shape[0:2])
        pad_x = original_max_length - image.shape[1]
        pad_y = original_max_length - image.shape[0]
        pad_l = pad_x // 2
        pad_t = pad_y // 2
        image = np.pad(image, ((pad_t, pad_y - pad_t), (pad_l, pad_x - pad_l), (0, 0)), mode="constant",
                       constant_values=255)
        return image, original_max_length

    def resize(self, image):
        print('image resize')
        # pad to square
        image, original_max_length = self.pad_image(image)
        interp = cv2.INTER_AREA if original_max_length > self.crop_image_size else cv2.INTER_LANCZOS4
        image = cv2.resize(image, (self.crop_image_size, self.crop_image_size),
                           interpolation=interp)  # width, height
        image = (image.astype(np.float32))# / 255.0
        return image

    def crop_portrait(self, image, width, height, landscape_square_crop):
        img_fragment_text = ["top", "mid", "bottom"]
        mid_upper = math.ceil(height / 3)
        crop_dims = None
        if mid_upper < self.crop_image_size:
            print('crop portrait BACKUP')
            crop_dims = [(0, 0, width, self.crop_image_size), (
                0, ((int(height / 2)) - int(self.crop_image_size / 2)), width,
                (int(height / 2) + int(self.crop_image_size / 2))),
                         (0, height - self.crop_image_size, width, height)]
        else:
            print('crop portrait NORMAL')
            mid_lower = mid_upper + math.ceil(height / 2)
            crop_dims = [(0, 0, width, int(height / 2)), (0, mid_upper, width, mid_lower),
                         (0, int(height / 2), width, height)]

        chosen_crop = crop_dims[img_fragment_text.index(landscape_square_crop)]
        print(f"chosen crop:\t{chosen_crop}")
        # crop image
        image = image[chosen_crop[1]:chosen_crop[3], :, :]
        print(f"new image dims:\t{image.shape}")
        return image

    def crop_landscape(self, image, width, height, landscape_square_crop):
        img_fragment_text = ["left", "mid", "right"]
        mid_left = math.ceil(width / 3)
        crop_dims = None
        if mid_left < self.crop_image_size:
            print('crop landscape BACKUP')
            crop_dims = [(0, 0, self.crop_image_size, height), (
                ((int(width / 2)) - int(self.crop_image_size / 2)), 0,
                ((int(width / 2)) + int(self.crop_image_size / 2)), height),
                         (width - self.crop_image_size, 0, width, height)]
        else:
            print('crop landscape NORMAL')
            mid_right = mid_left + math.ceil(width / 2)
            crop_dims = [(0, 0, int(width / 2), height), (mid_left, 0, mid_right, height),
                         (int(width / 2), 0, width, height)]

        chosen_crop = crop_dims[img_fragment_text.index(landscape_square_crop)]
        print(f"chosen crop:\t{chosen_crop}")
        # crop image
        image = image[:, chosen_crop[0]:chosen_crop[2], :]
        print(f"new image dims:\t{image.shape}")
        return image

    def crop_center(self, image, width, height):
        print('crop center')
        crop_size = self.crop_image_size

        if height < self.crop_image_size and width < self.crop_image_size:
            return self.resize(image)
        elif height < self.crop_image_size or width < self.crop_image_size:
            if height < self.crop_image_size:
                crop_size = height
            else:
                crop_size = width

        # crop image
        up = (int(height / 2) - int(crop_size / 2))
        lp = (int(height / 2) + int(crop_size / 2))
        ll = (int(width / 2) - int(crop_size / 2))
        rl = (int(width / 2) + int(crop_size / 2))
        image = image[up:lp, ll:rl, :]
        print(f"chosen crop:\t{up}, {lp}, {ll}, {rl}")
        print(f"new image dims:\t{image.shape}")
        if (image.shape)[0] == self.crop_image_size and (image.shape)[1] == self.crop_image_size:
            return image
        else:
            return self.resize(image)

    def partial_image_crop_button(self, image):
        print(f'crop or resize:\t{self.crop_or_resize}')
        image = np.array(image)

        # image = image[:, :, ::-1]  # RGB->BGR
        width = image.shape[1]
        height = image.shape[0]

        print(f"shape:\t{image.shape}")

        if self.crop_or_resize.lower() == 'resize':
            image = self.resize(image)
            self.global_images_list.append(copy.deepcopy(image))
            print(f"IMAGE WAS ADDED TO LIST")
            # print(f"self.global_images_list:\t{self.global_images_list}")
            print(f'numpy image HASH:\t{hash(image.tostring())}')
            return image
        if self.crop_or_resize.lower() == 'crop':
            print(f'crop portrait_square_crop:\t{self.portrait_square_crop}')
            print(f'crop landscape_square_crop:\t{self.landscape_square_crop}')
            if (height > width):  # portrait
                image = self.crop_portrait(image, width, height, self.portrait_square_crop)
                if width > self.crop_image_size:
                    # try another crop
                    image = self.crop_landscape(image, width, height, self.landscape_square_crop)
                width = image.shape[1]
                height = image.shape[0]
                if width > self.crop_image_size or height > self.crop_image_size:
                    # try center crop
                    image = self.crop_center(image, width, height)
                image = (image.astype(np.float32))# / 255.0
                self.global_images_list.append(copy.deepcopy(image))
                print(f'numpy image HASH:\t{hash(image.tostring())}')
                return image
            elif (height < width):  # landscape
                image = self.crop_landscape(image, width, height, self.landscape_square_crop)
                if height > self.crop_image_size:
                    # try another crop
                    image = self.crop_portrait(image, width, height, self.portrait_square_crop)
                width = image.shape[1]
                height = image.shape[0]
                if width > self.crop_image_size or height > self.crop_image_size:
                    # try center crop
                    image = self.crop_center(image, width, height)
                image = (image.astype(np.float32))# / 255.0
                self.global_images_list.append(copy.deepcopy(image))
                print(f'numpy image HASH:\t{hash(image.tostring())}')
                return image
            else:  # square
                width = image.shape[1]
                height = image.shape[0]
                if width > self.crop_image_size or height > self.crop_image_size:
                    # try center crop
                    image = self.crop_center(image, width, height)
                image = (image.astype(np.float32))# / 255.0
                self.global_images_list.append(copy.deepcopy(image))
                print(f'numpy image HASH:\t{hash(image.tostring())}')
                return image

