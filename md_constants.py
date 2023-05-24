general_config = """
    ### Make sure all necessary dependencies have been installed.
    ### This UI currently works in the case of ( SINGLE ) batch configurations.
    ### Note: Tag/s appended/prepended and/or replaced are not included in the "GALLERY Preview" if they are not in the "category" relative tag files.
    """
stats_config = """
    ### All except last two sliders represents the \"minimum\" requirements for any given image to be downloaded.
    """
collect = """
    ### Data Collection Options
    """
download = """
    ###  Data Download Options
    """
resize = """
    ###  Data Resize Options
    """
add_comps_config = """
    ### By DEFAULT the: Path to negative tags file is filled in. Edit or remove file and/or tags as necessary.
    ### Tags specified in the negative tag file, removes all tag instances from images (when downloaded).
    ### Prepend text radio button options are ONLY used when the keyword for the search is not specified.
    ### Note: Tag/s appended/prepended and/or replaced are not included in the "GALLERY Preview" if they are not in the "category" relative tag files.
    ### To replace Tags with the file, they must follow the format of the first tag as the keyword, then after the first comma will be all replacement tag/s.
    ### Only ONE search keyword per line. (Remove and Replace button effects are Permanent!)
    ### The user can manually remove tags from batched images in the "Preview Gallery" w/ the search bar and selected the searched checkbox option for tag deletion.
    """
run = """
    ### By DEFAULT the: Path to Image Full Change Log JSON (Optional) text field is BLANK. 
    ### This file is generated from tag and/or image changes in the Image Gallery tab "after" downloading.
    ### The process runs for post-processing and ONLY starts tracking add/remove tag and/or image changes done after the backend script gets run.
    ### This includes any interaction with the webui.
    ### Settings used prior to the post-processing step with this file must be identical to the original from when it was created.
    ### This is due to the file tracking the respective changes only with the webui, so anything before that step with the backend script is assumed to be correct.
    ### Or in other words, ONLY interactions with the webui that "instantly" adds and/or removes tag/s and/or image/s get saved.
    ### (NOTE) A new file tracking config "WILL" be created if the batch name is changed, e.g. places that could happen:
    ### ----> at start
    ### ----> when saving a new batch name
    ### ----> when loading new config
    ### ----> when saving new config
    ### After downloading images, OPTIONALLY use the Post-Processing Run Button to apply all additional changes to the images.
    """
preview = """
    ### The square checkboxes are used to do batch calculations, e.g. searching tag/s, adding and removing.
    ### (USER MUST SELECT AT LEAST ONE CHECKBOX) if searching.
    ### TAGS WITHOUT A CATEGORY ARE NOT DISPLAYED e.g. tag/s added with the append, prepend, replace Option (if they are also not in a "category" csv).
    ### (NOTE) ALL images "SEARCHED" can ONLY be deleted if checkbox option is selected; otherwise it is single image deletions.
    ### Remove tags from batches of images the same way you remove tags from individual images and then select the "searched" checkbox.
    """
extra = """
    ### Here you can download pre-trained stable diffusion models for your training and/or generation purposes.
    ### In addition, you can download several different repos to help set up for these ^^^ purposes. 
    """
custom = """
    ### This tab populates with the auto-tagging option ONLY after downloading one of those models from the previous tab.
    ### The (above) line \'assumes\' the user has the (image and tag) file pairs named the same thing.
    ### To Run the model: (1) Select your model (2) Set your Threshold (3) Select your Image/s (4) Interrogate with the model.
    ### ( NOTE ) Using Batch mode, will disable the single image predictions on the right side. (batch mode is also defined as using a folder with MORE than ONE image in it)
    ### To transfer Tag/s AND/OR Image/s, simply check the \'copy\' checkbox and click the save option preferred. Tag files will be create for images without them (if transferred).
    ### ( NOTE ) When running Batch mode, the (copy checkbox) and (Use & Write Tag Options) are automatically applied and image/s and tag/s are automatically saved.
    """






