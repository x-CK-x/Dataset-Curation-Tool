# Dataset-Curation-Tool

A tool for downloading from public image boards (which allow scraping) / preview your images & tags / edit your tags. Additional tabs for downloading other desired code repositories as well as S.O.T.A. Diffusion and Clip models for your purposes. Custom datasets can be added!

![visitor badge](https://visitor-badge.glitch.me/badge?page_id=x-CK-x.Dataset-Curation-Tool)

## WIKI-Page / Tutorial for this Repository ![HERE](https://github.com/x-CK-x/Dataset-Curation-Tool/wiki)

## Future Objectives/Features

- [ ] Include support for a variation of different public image boards
- [ ] Add Aliases for tags suggestions in the textboxes
- [ ] Add De-Noise & Upscale Models, e.g. ![StableSR](https://github.com/IceClear/StableSR)
- [ ] Add Segmentation & Detection Models, e.g. ![SegmentAnything-HQ](https://github.com/continue-revolution/sd-webui-segment-anything)
- [ ] Add Cross Attention Visualization ![DAAM](https://github.com/castorini/daam)
- [ ] Add Grad-CAM
- [ ] Add UMAP

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

#### other system installs
- unzip for the (optionally) downloaded zip files

(Linux)
```
sudo apt-get install unzip
```

## How to use

#### Run the Web-User Interface
```
python webui.py
python webui.py --server_port 7860 --share
python webui.py --server_port 7860 --share --username NAME --password PASS
```

## Additional Information

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
