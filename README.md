# Dataset-Curation-Tool

A tool for downloading from public image boards (which allow scraping) / preview your images & tags / edit your images & tags. Additional tabs for downloading other desired code repositories as well as S.O.T.A. diffusion and clips models for your purposes. Custom datasets can be added!

![visitor badge](https://visitor-badge.glitch.me/badge?page_id=x-CK-x.Dataset-Curation-Tool)

## Base Features

- User friendly UI
- Easy to load, edit, & create new json configs
- Advanced configuration tabs
- Easy to run directly from the UI
- Easy to run multiple configs in batch runs
- Gallery preview w/ search capability
- Easy to use Tag Editor
- Tag statistics tab
- Download relevant repos & pre-trained model/s tab

#### (05-09-2023)

- sort gallery by newest-to-oldest & oldest-to-newest
- new multi-image select feature
- user no longer needs to enter tags into a specific category (it's done automatically)
- download & extract auto-tagging model

#### (04-26-2023)

- Download relevant repos & pre-trained model/s tab

#### (04-23-2023)

- Progress Bars for auto-config apply button for post-processing all images
- A feature that tracks changes for images that are downloaded and saves them to a file; additionally tracking tag/s added removed to images as well as the images themselves being removed. The file generated can be used to instantly filter images & tags to match those exact changes later on. (runs automatically after the backend script finishes running)
- A button, search bar, and selection box for appending and/or prepending text/tags based on a searched tag
- A button for replacing text/tags automatically with provided text files
- A button for removing images individually and/or batched
- A button to apply the persist the changes to Disk
--- additional notes have been added to the headers of some of the Tabs as well

## Requirements
python 3.8+

clone repository
```
git clone https://github.com/x-CK-x/Dataset-Curation-Tool.git
```
```
cd Dataset-Curation-Tool
pip install -r requirements.txt
```

#### aria2, wget, & (windows) wzunzip
This downloader uses aria2 for fast downloading.
```
sudo apt-get install aria2
sudo apt-get install wget
```
#### other system installs
- unzip for the (optionally) downloaded zip files
```
sudo apt-get install unzip
```

For Windows, install the aria2 build https://github.com/aria2/aria2/releases/   Add aria2 in your environment variable paths.

For Windows, install the wzunzip https://www.winzip.com/en/product/command-line/#overview   Add wzunzip in your environment variable paths.

## How to use

#### Run the Web-User Interface
```
python webui.py
python webui.py --server_port 7860 --inbrowser --share
python webui.py --server_port 7860 --inbrowser --share --username NAME --password PASS
```

## Additional Information

##### General Config Tab

- set the path to the batch directory (stores downloaded data) ; creates new directory if it doesn't yet exist
- set the path to the resized images directory (stores resized data) ; creates new directory if it doesn't yet exist
- set tag seperator/delimeter
- set tag order
- set any tags to prepend succeeding the download step
- set any tags to append succeeding the download step
- set the target image extension
- set tag handler for resized images
- set path to json file if not already specified
- (optional) create new config option whenever clicking "Apply & Save"
- (optional) set json file from dropdown menu
- (optional) load json config from file

##### Stats Config Tab

- set all stats requirements of images on the image-board website

##### Checkbox Config Tab

- configure settings for data collection, downloading, & resizing

##### Required Tags Config Tab

- manually provide or specify a file with the tags to include
- (to remove tags) check tags and press remove ; all non-removed tags will be included in data collection

##### Blacklist Tags Config Tab

- manually provide or specify a file with the tags to exclude
- (to remove tags) check tags and press remove ; all non-removed tags will be included in data collection

##### Additional Components Config Tab

- set paths for the different types of downloaded data
- (optional) set path to file with image IDs to include and/or exclude
- set path to save all searched images IDs to
- (optional) set path to file with all negative tags

##### Run Tab

- set cpu usage
- (optional) set to complete all phases of the download per batch
- (optional) keep db data
- (optional) cache posts file if multiple batches
- (optional) path to posts/tags files
- (optional if using linux) path to aria2c program
- run button
- a dropdown menu to set multiple configs to run as a batch

##### Image Preview Tab

- set file type to view
- search downloaded gallery with multiple file type options (positive & negative tags ONLY)
- easily add tags into respective categories for single images, as well as images of any type (including images that have been searched)

##### Data Stats Tab

- set the method type to run & meta tag category

#### File and Folder Paths
Whether it's a file or a folder path, you can specify either a relative path or an absolute path. Each parameter that is a relative path uses the specified parent folder in each batch accordingly.

##### Default folder directory tree
```
base_folder/
├─ batch_folder/
│  ├─ downloaded_posts_folder/
│  │  ├─ png_folder/
│  │  ├─ jpg_folder/
│  │  ├─ gif_folder/
│  │  ├─ webm_folder/
│  │  ├─ swf_folder/
│  ├─ resized_img_folder/
│  ├─ tag_count_list_folder/
│  │  ├─ tags.csv
│  │  ├─ tag_category.csv
│  ├─ save_searched_list_path.txt
```
Any file path parameter that are empty will use the default path.

Files/folders that use the same path are merged, not overwritten. For example, using the same path for save_searched_list_path at every batch will result in a combined searched list of every batch in one .txt file.

### Notes
* When downloading, if the file already exists, it is skipped, unless, the file exists but was modified, it will download and the modified file will be renamed. Hence, I recommend not setting `delete_original` to `true` if you plan redownloading using the same destination folder.
* When resizing, when `resized_img_folder` uses a different folder from the source folder, if the file in the destination folder already exists, it is skipped. It does not check if the already existing file has the specified `min_short_side`.
* When running a new batch using the same save directories for tag files, tag count folders, and save_searched_list, tag files, tag count csvs, and save_searched_lists will be overwritten.

##### For more information/help on the downloading script, Please see the original backend development project : https://github.com/pikaflufftuft/pikaft-e621-posts-downloader

## License

MIT

## Usage conditions
By using this downloader, the user agrees that the author is not liable for any misuse of this downloader. This downloader is open-source and free to use.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
