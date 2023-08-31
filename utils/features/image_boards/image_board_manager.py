from utils import helper_functions as help

class Image_Board:
    def __init__(self, config_path):
        self.config_path = config_path
        self.img_brd = help.load_session_config(f_name=self.config_path)

        self.categories_map = self.img_brd["categories"]
        self.categories_map = self.reconstruct_keys(self.categories_map)

        self.valid_categories = self.img_brd["valid_categories"]
        self.tag_order = self.img_brd["tag_order"]
        self.database_url = self.img_brd["database_url"]
        self.database_filename = self.img_brd["database_filename"]

    def set_tag_order(self, tag_order):
        self.tag_order = tag_order

    def update_img_brd(self):
        help.update_JSON(settings=self.img_brd, temp_config_name=self.config_path)

    def get_invalid_categories(self):
        return [category for category in self.categories_map.values() if not category in self.valid_categories]

    def reconstruct_keys(self, data):
        return {int(k): v for k, v in data.items()}

    ### this class will be expanded upon in the future to be more generic w.r.t. handling the following:
    # - tags dictionary
    # - aliases dictionary
    # - component handling for the dictionaries corresponding to the different categories
    # - other additional meta data
    # - dropdown menu on main UI tab to select the image board
    ###