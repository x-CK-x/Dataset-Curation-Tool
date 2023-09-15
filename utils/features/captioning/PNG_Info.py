from PIL import Image
import piexif

from utils import helper_functions as help

class ImageMetadataExtractor:
    def __init__(self):
        self.image_paths = []
        self.IGNORED_INFO_KEYS = {
            'jfif', 'jfif_version', 'jfif_unit', 'jfif_density', 'dpi', 'exif',
            'loop', 'background', 'timestamp', 'duration', 'progressive', 'progression',
            'icc_profile', 'chromaticity', 'photoshop',
        }

    def set_image_paths(self, *image_paths):
        self.image_paths = image_paths

    def read_info_from_image(self, image: Image.Image):  # -> tuple[str | None, dict]:
        items = (image.info or {}).copy()

        geninfo = items.pop('parameters', None)

        if "exif" in items:
            exif = piexif.load(items["exif"])
            exif_comment = (exif or {}).get("Exif", {}).get(piexif.ExifIFD.UserComment, b'')
            try:
                exif_comment = piexif.helper.UserComment.load(exif_comment)
            except ValueError:
                exif_comment = exif_comment.decode('utf8', errors="ignore")

            if exif_comment:
                items['exif comment'] = exif_comment
                geninfo = exif_comment

        for field in self.IGNORED_INFO_KEYS:
            items.pop(field, None)

        if items.get("Software", None) == "NovelAI":
            help.verbose_print("CANNOT GET META DATA FROM NOVEL AI generated IMAGE")

        return geninfo, items

    def get_metadata(self, image_path):
        with Image.open(image_path) as img:
            return self.read_info_from_image(img)

    def display_metadata(self):
        all_tags = []
        for image_path in self.image_paths:
            help.verbose_print(f"Metadata for {image_path}:")
            metadata, _ = self.get_metadata(image_path)

            help.verbose_print(f"metadata:\t{metadata}")
            tags = []
            if metadata:
                for tag in (metadata.split("Negative prompt:")[0]).split(", "):
                    if "," in tag:
                        for tag in tag.split(","):
                            tag = tag.replace(" :", ":")
                            tag = tag.replace(": ", ":")
                            tag = tag.replace(" : ", ":")
                            tag = tag.split(":")[0]

                            tag = tag.replace(" ", "_")
                            if "_\\(" or "_(" in tag:
                                tag = tag.replace("_\\(", "+++++")
                                tag = tag.replace("_(", "+++++")

                            tag = tag.replace("(", "")
                            tag = tag.replace(")", "")

                            tag = tag.replace("{", "")
                            tag = tag.replace("}", "")
                            tag = tag.replace("\\n", "")
                            tag = tag.replace("\n", "")
                            tag = (tag.lower()).replace("by_", "") if "by_" in tag.lower() else tag
                            tag = (tag.lower()).replace("art_by_", "") if "art_by_" in tag.lower() else tag
                            tag = tag.replace("<lora", "")
                            tag = tag.replace(">", "")
                            tag = tag.replace("\\", "")
                            tag = tag.replace("BREAK", "")

                            if "+++++" in tag:
                                tag = tag.replace("+++++", "_(")
                                tag = f"{tag})"

                            # help.verbose_print(f"tag:\t{tag}")
                            tags.append(tag)
                    else:
                        tag = tag.replace(" :", ":")
                        tag = tag.replace(": ", ":")
                        tag = tag.replace(" : ", ":")
                        tag = tag.split(":")[0]

                        tag = tag.replace(" ", "_")
                        if "_\\(" or "_(" in tag:
                            tag = tag.replace("_\\(", "+++++")
                            tag = tag.replace("_(", "+++++")

                        tag = tag.replace("(", "")
                        tag = tag.replace(")", "")

                        tag = tag.replace("{", "")
                        tag = tag.replace("}", "")
                        tag = tag.replace("\\n", "")
                        tag = tag.replace("\n", "")
                        tag = (tag.lower()).replace("by_", "") if "by_" in tag.lower() else tag
                        tag = (tag.lower()).replace("art_by_", "") if "art_by_" in tag.lower() else tag
                        tag = tag.replace("<lora", "")
                        tag = tag.replace(">", "")
                        tag = tag.replace("\\", "")
                        tag = tag.replace("BREAK", "")

                        if "+++++" in tag:
                            tag = tag.replace("+++++", "_(")
                            tag = f"{tag})"

                        # help.verbose_print(f"tag:\t{tag}")
                        tags.append(tag)
            all_tags.append(tags)
            help.verbose_print("-" * 50)
        return all_tags
