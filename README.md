# Dataset-Curation-Tool

A tool for downloading from public image boards (which allow scraping) / preview your images & tags / edit your tags. Additional tabs for downloading other desired code repositories as well as S.O.T.A. Diffusion and Clip models for your purposes. Custom datasets can be added!

## WIKI-Page / Tutorial for this Repository [HERE](https://github.com/x-CK-x/Dataset-Curation-Tool/wiki)

![General Config](https://github.com/x-CK-x/Dataset-Curation-Tool/blob/74f6877383bddfd9c0d8e9587ab983e63936f89f/wiki_assets/v4WebUI_page_1_tab_1.png)

### Key Features

- **Add Custom Dataset** - load your own files for tagging, captioning or post-processing
- **Tag Editor & Image Gallery** - view images, quickly edit predicted tags and organize custom tag CSVs
- **Image Editor** - crop, zoom, rotate and apply simple filters before saving files
- **Data Stats** - generate quick summaries about your current dataset
- **Database** - run SQL queries against the download history database
- **Merge DB** - combine several databases into one consolidated file
- **Import Data** - add existing images, metadata or folders into the dataset database
- **Download** - scrape images from supported imageboards with many filter options
- **Download Extras** - fetch popular model checkpoints or additional code repositories
- **Advanced Settings** - tweak miscellaneous configuration values

## Installation Requirements

> Download either the windows, mac, or linux run file (repo will be installed for you):
> 
> [Windows Download](https://github.com/x-CK-x/Dataset-Curation-Tool/blob/main/run.bat)
> 
> [Linux Download](https://github.com/x-CK-x/Dataset-Curation-Tool/blob/main/linux_run.sh)
> 
> [MacOS Download](https://github.com/x-CK-x/Dataset-Curation-Tool/blob/main/mac_run.sh)

> Mac and Linux Users should make the file executable with the following terminal command:
```
chmod +x linux_run.sh
```

OR

```
chmod +x mac_run.sh
```

#### Other System Install Options
- Unzip for the (optionally) downloaded zip files

(Linux)
```
sudo apt-get install unzip
```

## How to Run Program

### "DO NOT" run the file with admin/sudo perms!
### "DO NOT" put the manually downloaded run file from the (INSTALLATION STEP ^^^) in the Data-Curation-Tool folder!
### "DO NOT" use the run file/s in the Data-Curation-Tool folder! (Use the manually downloaded run file, from the INSTALLATION STEP ^^^ to install and/or update the repo)
### "DO NOT" move the generated "dataset_curation_path.txt" file out of the Data-Curation-Tool folder!
```
The "DUPLICATE" run files (run.bat, mac_run.sh, linux_run.sh) residing in the Data-Curation-Tool folder, are intentionally deleted when the program is run.
```

> Double-Click file to run with (Default) settings

> Update dependencies i.e. in the yaml file with the following (make sure to use the most recent yaml file in the repo: [https://raw.githubusercontent.com/x-CK-x/Dataset-Curation-Tool/main/environment.yml](https://raw.githubusercontent.com/x-CK-x/Dataset-Curation-Tool/main/environment.yml)):
```
./RUN_FILE --update
```

### Below are Several Run (additional) Options to choose from

> Run with sharing turned on : Provides a *live* link that anyone can use
```
./RUN_FILE --share
```

> Run password protected : Requires user to type in a username & password to access the webUI
```
./RUN_FILE --server_port 7860 --username NAME --password PASS
```

> Run on a specified PORT : Displays the webUI relative to a specified PORT
```
./RUN_FILE --server_port 7860
```

> Skip loading tag suggestions to speed up startup
```
./RUN_FILE --disable_tag_suggestions
```

> OR CHOOSE ANY COMBINATION OF ^

## Important Information

- the most current **STABLE** build --> [v4.4.13](https://github.com/x-CK-x/Dataset-Curation-Tool/releases/tag/v4.4.13)
- for new users, it's highly recommended to use releases instead of pulling from the main branch
- in addition it is important to avoid using the **alpha** builds in the [releases](https://github.com/x-CK-x/Dataset-Curation-Tool/releases)
- if an alpha build is present it will be labeled as a **pre-release** and the **main-branch** of the repo is also likely to contain those changes; as such please use the most recent stable build as denoted above

## Bug Reporting & Troubleshooting

Create a Support Ticket or Bug Report here: [https://github.com/x-CK-x/Dataset-Curation-Tool/issues](https://github.com/x-CK-x/Dataset-Curation-Tool/issues)

## New Feature Requests

Feel free to suggest new feature/s here: [https://github.com/x-CK-x/Dataset-Curation-Tool/discussions/categories/ideas](https://github.com/x-CK-x/Dataset-Curation-Tool/discussions/categories/ideas)

## "Existing" **AND** "Future" Objectives/Features
These can be tracked in Both the [Feature List](https://github.com/x-CK-x/Dataset-Curation-Tool/issues/36) as well as in the [Issues Section](https://github.com/x-CK-x/Dataset-Curation-Tool/issues)

## Additional Information

##### Default folder directory tree
All downloaded data is placed inside a dedicated `data/` folder to
keep it separate from application files.
```
data/
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

## SQLite Database

The tool now stores download metadata in a persistent SQLite database
named `dataset_curation.db` located in the `databases/` folder.  Each
download run is stored in the `downloads` table and references an entry
in the `configs` table describing the JSON settings file that produced
that run.  Each key/value from those configs is also stored in the
`config_entries` table for easier querying.  Individual posts are tracked
in the `files` table with
their CDN URLs, local paths and tag files.  A global `images` table stores
unique hashes for every image and the `files` table references it to avoid
duplicates.  If a post is modified in the GUI a related entry is added to
`modified_files`.  Detected duplicates are stored in the `duplicates`
table.  The connection is thread‑safe so downloads can be recorded from
background tasks without errors.

The UI includes a **Database** tab for running custom SQL queries, an
**Import Data** tab for adding folders of files (with optional JSON
config files) and a **Merge DB** tab to combine multiple databases.

Each time a download is started from the Download tab, a new record is
created in the `downloads` table so you can track individual runs.

### Notes
* When downloading, if the file already exists, it is skipped, unless, the file exists but was modified, it will download and the modified file will be renamed. Hence, I recommend not setting `delete_original` to `true` if you plan redownloading using the same destination folder.
* When resizing, when `resized_img_folder` uses a different folder from the source folder, if the file in the destination folder already exists, it is skipped. It does not check if the already existing file has the specified `min_short_side`.
* When running a new batch using the same save directories for tag files, tag count folders, and save_searched_list, tag files, tag count csvs, and save_searched_lists will be overwritten.

##### For more information/help on the downloading script, Please see the original image board downloader script : https://github.com/pikaflufftuft/pikaft-e621-posts-downloader

## License

This project is licensed under the terms of the
[GNU General Public License v3.0](LICENSE).

## Usage conditions
By using this downloader, the user agrees that the author is not liable for any misuse of this downloader. This downloader is open-source and free to use.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
