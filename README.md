# Dataset-Curation-Tool

A tool for downloading from public image boards (which allow scraping) / preview your images & tags / edit your images & tags. Additional tabs for downloading other desired code repositories as well as S.O.T.A. diffusion and clips models for your purposes. Custom datasets can be added!

![visitor badge](https://visitor-badge.glitch.me/badge?page_id=x-CK-x.Dataset-Curation-Tool)

## WIKI-Page / Tutorial for this Repository HERE:

![https://github.com/x-CK-x/Dataset-Curation-Tool/wiki](https://github.com/x-CK-x/Dataset-Curation-Tool/wiki)

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

#### aria2
This downloader uses aria2 for fast downloading.

(Linux)
```
sudo apt-get install aria2
sudo apt-get install wget
```
#### other system installs
- unzip for the (optionally) downloaded zip files

(Linux)
```
sudo apt-get install unzip
```

(Windows)

For Windows, install the aria2 build https://github.com/aria2/aria2/releases/

Add aria2 in your environment variable paths.

Here's two way's to add to PATH on your Windows machine:

https://www.java.com/en/download/help/path.html

https://docs.oracle.com/en/database/oracle/machine-learning/oml4r/1.5.1/oread/creating-and-modifying-environment-variables-on-windows.html#GUID-DD6F9982-60D5-48F6-8270-A27EC53807D0

##### You can test that your machine recognizes aria2, by running the following on the command line
> aria2c

## How to use

#### Run the Web-User Interface
```
python webui.py
python webui.py --server_port 7860 --inbrowser --share
python webui.py --server_port 7860 --inbrowser --share --username NAME --password PASS
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
