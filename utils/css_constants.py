cyan_button_css = "label.svelte-1qxcj04.svelte-1qxcj04.svelte-1qxcj04 {background: linear-gradient(#00ffff, #2563eb)}"
red_button_css = "label.svelte-1qxcj04.svelte-1qxcj04.svelte-1qxcj04.selected {background: linear-gradient(#ff0000, #404040)}"
green_button_css = "label.svelte-1qxcj04.svelte-1qxcj04.svelte-1qxcj04 {background: linear-gradient(#2fa614, #2563eb)}"

thumbnail_colored_border_css = """
.selected-custom {
    --ring-color: red !important;
    transform: scale(0.9) !important;
    border-color: red !important;
}
"""

preview_hide_rule = """
.hidden {
  display: none;
}
"""

refresh_aspect_btn_rule = """
#refresh_aspect_btn {
  margin: 0.6em 0em 0.55em 1.25em;
  max-width: 2.5em;
  min-width: 2.5em !important;
  height: 2.4em;
}
"""

trim_row_length = """
#trim_row_length {
  max-width: 0em;
  min-width: 6.5em !important;
}
"""

trim_markdown_length = """
#trim_markdown_length {
  margin: 0.6em 0em 0.55em 0;
  max-width: 7.5em;
  min-width: 2.5em !important;
  height: 2.4em;
}
"""

refresh_models_btn_rule = """
#refresh_models_btn {
  margin: -1.50em 0.75em 0.75em 0.35em;
  max-width: 0.5em;
  min-width: 0em !important;
  height: 0em;
}
"""

gallery_fix_height = """
.custom-gallery { 
    height: 1356px !important; 
    width: 100%; 
    margin: 10px auto; 
    padding: 0px; 
    overflow-y: auto !important; 
}
"""

tag_checkbox_color_css = """
.artist-checkbox label { color: yellow !important; }
.character-checkbox label { color: green !important; }
.species-checkbox label { color: red !important; }
.general-checkbox label { color: white !important; }
.rating-checkbox label { color: cyan !important; }
.meta-checkbox label { color: purple !important; }
.invalid-checkbox label { color: black !important; }
.lore-checkbox label { color: black !important; }
.copyright-checkbox label { color: violet !important; }
"""

dataset_gallery_css = """
#dataset_gallery_path_textbox label {
    color: cyan !important;
}
#load_dataset_gallery_button {
    background-color: red !important;
}
"""
