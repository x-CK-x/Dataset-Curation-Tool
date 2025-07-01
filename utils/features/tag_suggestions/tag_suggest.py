import gradio as gr
import string
import datrie

from utils import helper_functions as help

class Tag_Suggest:

    def __init__(self, all_tags_ever_dict, gallery_tab_manager, download_tab_manager, advanced_settings_tab_manager):
        self.trie = datrie.Trie(string.printable)
        help.load_trie(self.trie, all_tags_ever_dict)
        self.gallery_tab_manager = gallery_tab_manager
        self.download_tab_manager = download_tab_manager
        self.advanced_settings_tab_manager = advanced_settings_tab_manager

    # Function to color code categories
    def category_color(self, category):
        colors = {
            "artist": "yellow",
            "character": "green",
            "species": "red",
            "general": "white",
            "rating": "blue",
            "meta": "purple",
            "invalid": "black",
            "lore": "black",
            "copyright": "black",
        }
        return colors.get(self.download_tab_manager.image_board.categories_map[category])

    # Function to format the count
    def format_count(self, count):
        if count >= 1000:
            return f"{round(count / 1000, 1)}k"
        else:
            return str(count)

    def get_tag_options(self, input_string, num_suggestions):
        # Get a list of all tags that start with the edited part
        suggested_tags = self.trie.keys(input_string)

        # Sort the tags by count and take the top num_suggestions
        suggested_tags = sorted(suggested_tags, key=lambda tag: -self.trie[tag])[:num_suggestions]

        # Color code the tags by their categories and add the count
        color_coded_tags = []
        tag_categories = []
        for tag in suggested_tags:
            category = self.download_tab_manager.image_board.categories_map[self.gallery_tab_manager.all_tags_ever_dict[tag][0]]  # gets category of already existing tag
            tag_categories.append(category)
            count = self.gallery_tab_manager.all_tags_ever_dict[tag][1]  # gets count of already existing tag
            count_str = self.format_count(count)
            color_coded_tag = f"{tag} → {count_str}"
            color_coded_tags.append(color_coded_tag)

        tag_textbox = gr.update(value=input_string)
        tag_suggestion_dropdown = gr.update(choices=color_coded_tags, value=None)
        state = input_string  # retain the tag name until it is time
        state_tag = ""

        # print(f"color_coded_tags:\t{color_coded_tags}")
        return tag_textbox, tag_suggestion_dropdown, state, state_tag, tag_categories

    # get the suggestions and populate the dropdown menu
    def suggest_tags(self, input_string, state, num_suggestions, state_tag, enable_suggestions=True):
        if not enable_suggestions:
            generic_dropdown = gr.update(choices=[], value=None)
            return generic_dropdown, state, state_tag, []
        # print(f"input_string:\t{(input_string)}")
        # print(f"state:\t{(state)}")
        # print(f"num_suggestions:\t{(num_suggestions)}")
        # print(f"state_tag:\t{(state_tag)}")

        # tags_csv_dict          ####### tag -> count
        # all_tags_ever_dict     ####### tag -> category

        ###### prior string check, b4 updating new state

        if input_string is None or len(input_string) == 0:  ### string is null or empty
            # generic_textbox = gr.update(value="")
            generic_dropdown = gr.update(choices=[], value=None)
            tag_categories = []
            state = ""  # set the new state of the input_string
            state_tag = ""
            return generic_dropdown, state, state_tag, tag_categories
        elif " " in input_string:  ## string contains space
            string_arr = input_string.split(" ")
            tag_count = 0
            text_arr = []  # tracks length of tag string fragments
            for text in string_arr:
                text_arr.append(len(text))
                if text_arr[-1] > 0:
                    tag_count += 1

            if tag_count == 2:  # there are two valid tag strings
                state_tag = string_arr[0]  # choose the first tag
                state = string_arr[-1]  # the remainder string
                # generic_textbox = gr.update(value=state)

                # get suggestions for remainder tag
                _, generic_dropdown, _, _, tag_categories = self.get_tag_options(string_arr[-1],
                                                                            num_suggestions)  # state is 3rd output
                # help.verbose_print(f"===============\ttag_categories\t{tag_categories}")
                # help.verbose_print(f"===============\tstate\t{state}")
                return generic_dropdown, state, state_tag, tag_categories
            else:  # one valid tag string
                state_tag = string_arr[0] if text_arr[0] > 0 else string_arr[-1]
                state = ""  # the remainder string
                # generic_textbox = gr.update(value=state)

                generic_dropdown = gr.update(choices=[], value=None)
                tag_categories = []

                # help.verbose_print(f"------------------\tstring_arr\t{string_arr}")
                # help.verbose_print(f"------------------\tstate_tag\t{state_tag}")
                # help.verbose_print(f"------------------\tstate\t{state}")

                return generic_dropdown, state, state_tag, tag_categories
        else:  ### string contains ONLY text
            tag_textbox, tag_suggestion_dropdown, state, state_tag, tag_categories = self.get_tag_options(input_string,
                                                                                                     num_suggestions)
            # help.verbose_print(f"===============\ttag_categories\t{tag_categories}")
            # help.verbose_print(f"===============\ttag_textbox\t{tag_textbox}")
            # help.verbose_print(f"===============\tstate\t{state}")
            # help.verbose_print(f"===============\tstate_tag\t{state_tag}")

            return tag_suggestion_dropdown, state, state_tag, tag_categories

    def dropdown_handler_required(self, tag: gr.SelectData):
        tag = tag.value
        sep = " → "
        if sep in tag:
            tag = tag.split(sep)[0]

        if not tag in self.download_tab_manager.required_tags_list:
            self.download_tab_manager.required_tags_list.append(tag)

        tag_textbox = gr.update(value="")
        tag_suggestion_dropdown = gr.update(choices=[], value=[])
        initial_state = ""
        initial_state_tag = ""
        required_tags_group_var = gr.update(choices=self.download_tab_manager.required_tags_list, value=[])
        return tag_textbox, tag_suggestion_dropdown, initial_state, initial_state_tag, required_tags_group_var

    def dropdown_handler_blacklist(self, tag: gr.SelectData):
        tag = tag.value
        sep = " → "
        if sep in tag:
            tag = tag.split(sep)[0]

        if not tag in self.download_tab_manager.blacklist_tags:
            self.download_tab_manager.blacklist_tags.append(tag)

        tag_textbox = gr.update(value="")
        tag_suggestion_dropdown = gr.update(choices=[], value=[])
        initial_state = ""
        initial_state_tag = ""
        blacklist_group_var = gr.update(choices=self.download_tab_manager.blacklist_tags, value=[])
        return tag_textbox, tag_suggestion_dropdown, initial_state, initial_state_tag, blacklist_group_var










    def get_search_tag_options(self, partial_tag, num_suggestions):
        tag_categories = []
        if (partial_tag[0] == "-" and len(partial_tag) == 1):
            return gr.update(choices=[], value=None), tag_categories
        # check for leading "-" with additional text afterwards i.e. length exceeding 1 :: remove "-" if condition is true
        partial_tag = partial_tag[1:] if (partial_tag[0] == "-" and len(partial_tag) > 1) else partial_tag

        # Get a list of all tags that start with the edited part
        suggested_tags = self.trie.keys(partial_tag)

        # Sort the tags by count and take the top num_suggestions
        suggested_tags = sorted(suggested_tags, key=lambda tag: -self.trie[tag])[:num_suggestions]

        # Color code the tags by their categories and add the count
        color_coded_tags = []
        for tag in suggested_tags:
            category = self.download_tab_manager.image_board.categories_map[self.gallery_tab_manager.all_tags_ever_dict[tag][0]]  # gets category of already existing tag
            tag_categories.append(category)
            count = self.gallery_tab_manager.all_tags_ever_dict[tag][1]  # gets count of already existing tag
            count_str = self.format_count(count)
            color_coded_tag = f"{tag} → {count_str}"
            color_coded_tags.append(color_coded_tag)

        tag_suggestion_dropdown = gr.update(choices=color_coded_tags, value=None)

        # print(f"color_coded_tags:\t{color_coded_tags}")
        return tag_suggestion_dropdown, tag_categories

    def identify_changing_tag(self, past_string, current_string):
        # Split the strings into tags
        past_tags = past_string.split()
        current_tags = current_string.split()
        # Compare the tags and find the one that is being changed
        for i in range(min(len(past_tags), len(current_tags))):
            if past_tags[i] != current_tags[i]:
                return (current_string.index(current_tags[i]), current_tags[i])
        # If we're here, it means one of the strings has more tags than the other
        if len(past_tags) < len(current_tags):
            # A tag was added
            return (current_string.index(current_tags[-1]), current_tags[-1])
        elif len(past_tags) > len(current_tags):
            # A tag was removed
            return (0, "")
        # If we're here, it means there was no change
        return (0, "")

    def suggest_search_tags(self, input_string, num_suggestions, previous_text, enable_suggestions=True):
        if not enable_suggestions:
            generic_dropdown = gr.update(choices=[], value=None)
            current_placement_tuple = (0, "")
            return generic_dropdown, input_string, current_placement_tuple, []
        # obtain the current information
        current_placement_tuple = self.identify_changing_tag(previous_text, input_string)

        # print(f"previous_text:\t{(previous_text)}")
        # print(f"CURRENT TEXT:\t{(input_string)}")
        # print(f"num_suggestions:\t{(num_suggestions)}")
        # print(f"current_placement_tuple:\t{(current_placement_tuple)}")

        if current_placement_tuple[-1] is None or len(
                current_placement_tuple[-1]) == 0:  # ignore if the changes nothing of importance
            generic_dropdown = gr.update(choices=[], value=None)
            previous_text = input_string  # update previous state
            tag_categories = []
            return generic_dropdown, previous_text, current_placement_tuple, tag_categories

        generic_dropdown, tag_categories = self.get_search_tag_options(current_placement_tuple[-1], num_suggestions)
        # print(f"generic_dropdown:\t{(generic_dropdown)}")
        # print(f"tag_categories:\t{(tag_categories)}")

        return generic_dropdown, previous_text, current_placement_tuple, tag_categories

    def dropdown_search_handler(self, tag: gr.SelectData, input_string, previous_text, current_placement_tuple):
        tag = tag.value
        sep = " → "
        if sep in tag:
            tag = tag.split(sep)[0]

        if current_placement_tuple[-1][0] == "-":
            tag = f"-{tag}"
        # help.verbose_print(f"tag:\t{tag}")
        # help.verbose_print(f"input_string:\t{input_string}")
        # help.verbose_print(f"previous_text:\t{previous_text}")
        # help.verbose_print(f"current_placement_tuple:\t{current_placement_tuple}")
        # change the textbox
        start_index = current_placement_tuple[0]
        end_index = current_placement_tuple[0] + len(current_placement_tuple[-1])
        new_string = input_string[:start_index] + tag + input_string[end_index:]
        # update the previous state
        previous_text = new_string
        # reset the placement tuple
        current_search_state_placement_tuple = (0, "")
        return gr.update(value=new_string), previous_text, current_search_state_placement_tuple, gr.update(choices=[],
                                                                                                           value=None)

    def dropdown_handler_add_tags(self, tag: gr.SelectData, apply_to_all_type_select_checkboxgroup, img_id,
                                  multi_select_ckbx_state,
                                  only_selected_state_object, images_selected_state, state_of_suggestion):
        tag = tag.value
        sep = " → "
        if sep in tag:
            tag = tag.split(sep)[0]

        img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group, \
        img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group, \
        state_tag, tag_textbox = self.gallery_tab_manager.add_tag_changes(tag, apply_to_all_type_select_checkboxgroup, img_id,
                                                 multi_select_ckbx_state, only_selected_state_object,
                                                 images_selected_state, state_of_suggestion, False)

        tag_textbox = gr.update(value="")
        state_of_suggestion = ""
        tag_suggestion_dropdown = gr.update(choices=[], value=[])
        return img_artist_tag_checkbox_group, img_character_tag_checkbox_group, img_species_tag_checkbox_group, \
               img_general_tag_checkbox_group, img_meta_tag_checkbox_group, img_rating_tag_checkbox_group, \
               tag_textbox, tag_suggestion_dropdown, state_of_suggestion, state_tag
