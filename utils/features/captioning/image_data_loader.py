import shutil

import cv2
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import numpy as np
import math
import copy
import os

from utils import helper_functions as help

try:
    import torch
    from torch.utils.data import Dataset as _TorchDataset
except ImportError:  # pragma: no cover - optional dependency
    torch = None

    class _TorchDataset:
        pass

class ImageLoadingPrepDataset(_TorchDataset):
    def __init__(self, image_paths):
        self.images = image_paths
        self.images = [path for path in self.images if not (".txt" in path)]

        self.operation_choices = ["Crop", "Zoom", "Resize", "Rotate", "Scale", "Translation",
                                  "Brightness", "Contrast", "Saturation", "Noise", "Shear",
                                  "Horizontal Flip", "Vertical Flip"]
        self.preprocess_options = ['resize']
        self.zoom_value = 1.0
        self.rotate_slider = 0
        self.scale_slider = 1
        self.dx_slider = 0
        self.dy_slider = 0
        self.brightness_slider = 1
        self.contrast_slider = 1
        self.saturation_slider = 1
        self.noise_slider = 0
        self.shear_slider = 0
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
            tensor = self._to_tensor(image)
        except Exception as e:
            print(f"Could not load image path: {img_path}, error: {e}")
            return None
        return (tensor, img_path)

    def _to_tensor(self, image):
        if torch is not None:
            return torch.tensor(image)
        return np.asarray(image)

    def get_image_paths(self):
        return self.images

    def set_image_paths(self, images):
        self.images = images

    def save_image_data(self, src_name, src, is_augmented):
        temp = '\\' if help.is_windows() else '/'
        img_path = None
        temp_names = [name.split(temp)[-1] for name in self.images]
        name_w_type = None
        for idx, name in enumerate(temp_names):
            if src_name in name:
                img_path = self.images[idx]
                name_w_type = temp_names[idx]
                break

        print(f"img_path:\t{img_path}")
        print(f"src:\t{src}")
        print(f"is_augmented:\t{is_augmented}")

        ext = name_w_type.split(".")[-1]
        path_no_ext = '.'.join(os.path.join(src, name_w_type).split(".")[:-1])

        try:
            image = self.smart_imread(img_path)
            tensor = self._to_tensor(image)
        except Exception as e:
            print(f"Could not load image path: {img_path}, error: {e}")

        img = self.augment_image(tensor)

        if not is_augmented:
            if not os.path.exists(f"{path_no_ext}.{ext}"):
                cv2.imwrite(f"{path_no_ext}.{ext}", img)
                help.verbose_print(f"Image:\t{path_no_ext}.{ext}\tSAVED!")
                return f"{path_no_ext}.{ext}"
            else:
                return None
        else:
            counter = 0
            while os.path.exists(f"{path_no_ext}_{counter}.{ext}"):
                counter += 1
            cv2.imwrite(f"{path_no_ext}_{counter}.{ext}", img)
            help.verbose_print(f"Image:\t{path_no_ext}_{counter}.{ext}\tSAVED!")
            return f"{path_no_ext}_{counter}.{ext}"

    def set_crop_image_size(self, crop_image_size):
        self.crop_image_size = crop_image_size

    def set_preprocess_options(self, preprocess_options):
        self.preprocess_options = preprocess_options

    def set_zoom_value(self, zoom_value):
        self.zoom_value = zoom_value

    def set_rotate_slider(self, rotate_slider):
        self.rotate_slider = rotate_slider
    def set_scale_slider(self, scale_slider):
        self.scale_slider = scale_slider
    def set_dx_slider(self, dx_slider):
        self.dx_slider = dx_slider
    def set_dy_slider(self, dy_slider):
        self.dy_slider = dy_slider
    def set_brightness_slider(self, brightness_slider):
        self.brightness_slider = brightness_slider
    def set_contrast_slider(self, contrast_slider):
        self.contrast_slider = contrast_slider
    def set_saturation_slider(self, saturation_slider):
        self.saturation_slider = saturation_slider
    def set_noise_slider(self, noise_slider):
        self.noise_slider = noise_slider
    def set_shear_slider(self, shear_slider):
        self.shear_slider = shear_slider

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
        # image = (image.astype(np.float32))# / 255.0
        return image

    def crop_portrait(self, image, vertical_crop):
        height, width, _ = image.shape
        one_third_height = height // 3

        if vertical_crop == "top":
            start_y = 0
        elif vertical_crop == "mid":
            start_y = one_third_height
        else:  # bottom
            start_y = 2 * one_third_height
        end_y = start_y + one_third_height

        return image[start_y:end_y, :, :]

    def crop_landscape(self, image, horizontal_crop):
        height, width, _ = image.shape
        one_third_width = width // 3

        if horizontal_crop == "left":
            start_x = 0
        elif horizontal_crop == "mid":
            start_x = one_third_width
        else:  # right
            start_x = 2 * one_third_width
        end_x = start_x + one_third_width

        return image[:, start_x:end_x, :]

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
        return image

    def zoom_image(self, img, zoom_value):
        # Convert input to PIL Image if it's not already
        if not isinstance(img, Image.Image):
            img = Image.fromarray(np.uint8(img)).convert('RGB')  # Ensure it's RGB

        # Calculate new dimensions based on zoom value
        new_width = int(img.width * zoom_value)
        new_height = int(img.height * zoom_value)

        # Resize the image based on the new dimensions
        zoomed_img = img.resize((new_width, new_height), Image.LANCZOS)

        # Now, let's center the zoomed image in the original frame
        result = Image.new("RGB", (img.width, img.height))
        x_offset = (img.width - zoomed_img.width) // 2
        y_offset = (img.height - zoomed_img.height) // 2
        result.paste(zoomed_img, (x_offset, y_offset))
        return np.array(result)

    def flip_horizontal(self, img):
        # Convert input to PIL Image if it's not already
        if not isinstance(img, Image.Image):
            img = Image.fromarray(np.uint8(img)).convert('RGB')  # Ensure it's RGB
        result = img.transpose(Image.FLIP_LEFT_RIGHT)
        return np.array(result)

    def flip_vertical(self, img):
        # Convert input to PIL Image if it's not already
        if not isinstance(img, Image.Image):
            img = Image.fromarray(np.uint8(img)).convert('RGB')  # Ensure it's RGB
        result = img.transpose(Image.FLIP_TOP_BOTTOM)
        return np.array(result)

    def rotate(self, img, angle):
        # Convert input to PIL Image if it's not already
        if not isinstance(img, Image.Image):
            img = Image.fromarray(np.uint8(img)).convert('RGB')  # Ensure it's RGB
        result = img.rotate(angle)
        return np.array(result)

    def scale(self, img, factor): # consider using GANs & Diffusion models to increase resolution & denoise images as better approaches
        # Convert input to PIL Image if it's not already
        if not isinstance(img, Image.Image):
            img = Image.fromarray(np.uint8(img)).convert('RGB')  # Ensure it's RGB
        width, height = img.size
        result = img.resize((int(width * factor), int(height * factor)))
        return np.array(result)

    def translate(self, img, dx, dy):
        # Convert input to PIL Image if it's not already
        if not isinstance(img, Image.Image):
            img = Image.fromarray(np.uint8(img)).convert('RGB')  # Ensure it's RGB
        result = img.transform(img.size, Image.AFFINE, (1, 0, dx, 0, 1, dy))
        return np.array(result)

    def adjust_brightness(self, img, factor):
        # Convert input to PIL Image if it's not already
        if not isinstance(img, Image.Image):
            img = Image.fromarray(np.uint8(img)).convert('RGB')  # Ensure it's RGB
        enhancer = ImageEnhance.Brightness(img)
        result = enhancer.enhance(factor)
        return np.array(result)

    def adjust_contrast(self, img, factor):
        # Convert input to PIL Image if it's not already
        if not isinstance(img, Image.Image):
            img = Image.fromarray(np.uint8(img)).convert('RGB')  # Ensure it's RGB
        enhancer = ImageEnhance.Contrast(img)
        result = enhancer.enhance(factor)
        return np.array(result)

    def adjust_saturation(self, img, factor):
        # Convert input to PIL Image if it's not already
        if not isinstance(img, Image.Image):
            img = Image.fromarray(np.uint8(img)).convert('RGB')  # Ensure it's RGB
        enhancer = ImageEnhance.Color(img)
        result = enhancer.enhance(factor)
        return np.array(result)

    def inject_noise(self, img, noise_level):
        arr = np.asarray(img)
        noise = np.random.normal(0, noise_level, arr.shape)
        noisy_arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        result = Image.fromarray(noisy_arr)
        return np.array(result)

    def shear(self, img, factor):
        # Convert input to PIL Image if it's not already
        if not isinstance(img, Image.Image):
            img = Image.fromarray(np.uint8(img)).convert('RGB')  # Ensure it's RGB
        width, height = img.size
        m = factor
        result = img.transform((width, height), Image.AFFINE, (1, m, -m * width / 2, 0, 1, 0))
        return np.array(result)

    def partial_image_crop_button(self, image):
        print(f'options to run:\t{self.preprocess_options}')
        image = np.array(image)
        print(f"shape:\t{image.shape}")

        for i, preprocess_op in enumerate(self.preprocess_options):
            if preprocess_op.lower() == self.operation_choices[2].lower(): # resize
                image = self.resize(image)
            elif preprocess_op.lower() == self.operation_choices[0].lower(): # crop
                print(f'crop portrait_square_crop:\t{self.portrait_square_crop}')
                print(f'crop landscape_square_crop:\t{self.landscape_square_crop}')
                # Check if both cropping parameters are set. If set, perform the respective cropping
                if self.portrait_square_crop not in [None, "", "None"]:
                    image = self.crop_portrait(image, self.portrait_square_crop)
                if self.landscape_square_crop not in [None, "", "None"]:
                    image = self.crop_landscape(image, self.landscape_square_crop)
            elif preprocess_op.lower() == self.operation_choices[1].lower(): # zoom
                image = self.zoom_image(image, self.zoom_value)
            elif preprocess_op.lower() == self.operation_choices[3].lower(): # rotate
                image = self.rotate(image, self.rotate_slider)
            elif preprocess_op.lower() == self.operation_choices[4].lower(): # scale
                image = self.scale(image, self.scale_slider)
            elif preprocess_op.lower() == self.operation_choices[5].lower(): # translate
                image = self.translate(image, self.dx_slider, self.dy_slider)
            elif preprocess_op.lower() == self.operation_choices[6].lower(): # brightness
                image = self.adjust_brightness(image, self.brightness_slider)
            elif preprocess_op.lower() == self.operation_choices[7].lower(): # contrast
                image = self.adjust_contrast(image, self.contrast_slider)
            elif preprocess_op.lower() == self.operation_choices[8].lower(): # saturation
                image = self.adjust_saturation(image, self.saturation_slider)
            elif preprocess_op.lower() == self.operation_choices[9].lower(): # noise
                image = self.inject_noise(image, self.noise_slider)
            elif preprocess_op.lower() == self.operation_choices[10].lower(): # shear
                image = self.shear(image, self.shear_slider)
            elif preprocess_op.lower() == self.operation_choices[11].lower(): # Horizontal Flip
                image = self.flip_horizontal(image)
            elif preprocess_op.lower() == self.operation_choices[12].lower(): # Vertical Flip
                image = self.flip_vertical(image)

        if not 'resize' in self.preprocess_options[-1].lower():
            image = self.resize(image)  # formats image to required size

        # Convert to float32, if necessary
        image = image.astype(np.float32)

        # Add to the global image list and print the hash
        self.global_images_list.append(copy.deepcopy(image))
        print(f'numpy image HASH:\t{hash(image.tostring())}')

        return image



    def augment_image(self, image):
        print(f'options to run:\t{self.preprocess_options}')
        image = np.array(image)
        print(f"shape:\t{image.shape}")

        for i, preprocess_op in enumerate(self.preprocess_options):
            if preprocess_op.lower() == self.operation_choices[2].lower(): # resize
                image = self.resize(image)
            elif preprocess_op.lower() == self.operation_choices[0].lower(): # crop
                print(f'crop portrait_square_crop:\t{self.portrait_square_crop}')
                print(f'crop landscape_square_crop:\t{self.landscape_square_crop}')
                # Check if both cropping parameters are set. If set, perform the respective cropping
                if self.portrait_square_crop not in [None, "", "None"]:
                    image = self.crop_portrait(image, self.portrait_square_crop)
                if self.landscape_square_crop not in [None, "", "None"]:
                    image = self.crop_landscape(image, self.landscape_square_crop)
            elif preprocess_op.lower() == self.operation_choices[1].lower(): # zoom
                image = self.zoom_image(image, self.zoom_value)
            elif preprocess_op.lower() == self.operation_choices[3].lower(): # rotate
                image = self.rotate(image, self.rotate_slider)
            elif preprocess_op.lower() == self.operation_choices[4].lower(): # scale
                image = self.scale(image, self.scale_slider)
            elif preprocess_op.lower() == self.operation_choices[5].lower(): # translate
                image = self.translate(image, self.dx_slider, self.dy_slider)
            elif preprocess_op.lower() == self.operation_choices[6].lower(): # brightness
                image = self.adjust_brightness(image, self.brightness_slider)
            elif preprocess_op.lower() == self.operation_choices[7].lower(): # contrast
                image = self.adjust_contrast(image, self.contrast_slider)
            elif preprocess_op.lower() == self.operation_choices[8].lower(): # saturation
                image = self.adjust_saturation(image, self.saturation_slider)
            elif preprocess_op.lower() == self.operation_choices[9].lower(): # noise
                image = self.inject_noise(image, self.noise_slider)
            elif preprocess_op.lower() == self.operation_choices[10].lower(): # shear
                image = self.shear(image, self.shear_slider)
            elif preprocess_op.lower() == self.operation_choices[11].lower(): # Horizontal Flip
                image = self.flip_horizontal(image)
            elif preprocess_op.lower() == self.operation_choices[12].lower(): # Vertical Flip
                image = self.flip_vertical(image)

        # if not 'resize' in self.preprocess_options[-1].lower():
        #     image = self.resize(image)  # formats image to required size

        return image