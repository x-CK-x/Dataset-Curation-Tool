import copy
import glob
import json
import os
import subprocess as sub
import operator
import sys
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
import re
from datetime import datetime
import importlib.util
import shutil
from zipfile import ZipFile
import gzip
import pandas as pd

from utils.features.captioning.model_configs import model_configs as mc

ops = {'+': operator.add, '-': operator.sub}

'''
##################################################################################################################################
###################################################     HELPER FUNCTIONS     #####################################################
##################################################################################################################################
'''

def verbose_print(text):
    print(f"{text}")

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def load_session_config(f_name):
    session_config = None
    file_exists = os.path.exists(f_name)
    if not file_exists: # create the file
        dir_name = os.path.dirname(f_name)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(f_name, 'w') as f:
            f.close()
    else: # load the file
        data_flag = True # detects if the file is empty
        with open(f_name, 'r') as json_file:
            lines = json_file.readlines()
            if len(lines) == 0 or len(lines[0].replace(' ', '')) == 0:
                data_flag = False
            json_file.close()

        if data_flag: # data present
            with open(f_name) as json_file:
                data = json.load(json_file)

                temp_config = [dictionary for dictionary in data]
                if len(temp_config) > 0:
                    session_config = data
                else:
                    session_config = {}
                json_file.close()
    return session_config


def download_url(url, file_name):
    try:
        r = requests.get(url, stream=True)
        r.raise_for_status()

        # Get the total file size to set up tqdm
        total_size = int(r.headers.get('content-length', 0))

        # Initialize tqdm progress bar
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=file_name) as pbar:
            with open(file_name, 'wb') as file:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:  # Filter out keep-alive new chunks
                        file.write(chunk)
                        # Update tqdm progress bar with chunk size
                        pbar.update(len(chunk))
    except requests.exceptions.RequestException as err:
        print(f"Error occurred with {url}: {err}")

def grab_pre_selected(settings, all_checkboxes):
    pre_selected_checkboxes = []
    for key in all_checkboxes:
        if settings[key]:
            pre_selected_checkboxes.append(key)
    return pre_selected_checkboxes

def update_JSON(settings, temp_config_name):
    temp = copy.deepcopy(settings)
    for entry in temp:
        verbose_print(f"{entry}:\t{settings[entry]}")
    # Ensure the target directory exists before writing the JSON file
    dir_name = os.path.dirname(temp_config_name)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    with open(temp_config_name, "w") as f:
        json.dump(temp, indent=4, fp=f)
    f.close()
    verbose_print("="*42)

def create_dirs(arb_path):
    if not os.path.exists(arb_path):
        os.makedirs(arb_path)

def execute(cmd):
    popen = sub.Popen(cmd, stdout=sub.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise sub.CalledProcessError(return_code, cmd)

def get_list(arb_string, delimiter):
    return arb_string.split(delimiter)

def get_string(arb_list, delimiter):
    return delimiter.join(arb_list)

def from_padded(line):
    if len(line) > 1:# check for padded-0
        if int(line[0]) == 0:# remove the 0, cast to int, return
            return int(line[-1])
    return int(line)

def to_padded(num):
    return f"{num:02}"

def is_windows():
    return os.name == 'nt'

def get_OS_delimiter():
    """Return the path delimiter for the current operating system."""
    if is_windows():
        return '\\'
    else:
        return '/'

# Backwards compatibility for legacy code/tests using the misspelled
# function name ``get_OS_delimeter``.
def get_OS_delimeter():
    return get_OS_delimiter()

def unzip_file(file_path, new_name=""):
    temp = '\\' if is_windows() else '/'
    name = file_path.split(temp)[-1]
    ext = name.split('.')[-1]
    name = name.split('.')[0]

    if len(new_name) == 0:
        if '.csv' in file_path:
            new_name = f"{name}.csv"
        else:
            new_name = name

    if 'gz' in ext:
        with gzip.open(file_path, 'rb') as f_in:
            with open(new_name, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        verbose_print(f"gz file:\t{file_path} & {new_name}")
    else: # if 'zip' or no extension
        with ZipFile(file_path, 'r') as zObject:
            zObject.extractall(path=os.getcwd())
        verbose_print(f"zip file of some kind:\t{file_path}")

def make_all_dirs(list_of_paths):
    for path in list_of_paths:
        create_dirs(path)

def delete_all_archives():
    zip_list = glob.glob(os.path.join(os.getcwd(), f"*.zip"))
    rar_list = glob.glob(os.path.join(os.getcwd(), f"*.rar"))
    gz_list = glob.glob(os.path.join(os.getcwd(), f"*.gz"))
    for zip in zip_list:
        os.remove(zip)
    for rar in rar_list:
        os.remove(rar)
    for gz in gz_list:
        os.remove(gz)


def unzip_all():
    zip_list = glob.glob(os.path.join(os.getcwd(), f"*.zip"))
    rar_list = glob.glob(os.path.join(os.getcwd(), f"*.rar"))
    gz_list = glob.glob(os.path.join(os.getcwd(), f"*.gz"))
    for zip in zip_list:
        unzip_file(zip)
    for rar in rar_list:
        unzip_file(rar)
    for gz in gz_list:
        unzip_file(gz)

def parse_single_all_tags(file_path):
    all_tags = []
    # verbose_print(f"file_path:\t\t{file_path}")
    if not os.path.exists(file_path):
        return all_tags.copy()
    with open(file_path, 'r', encoding='utf-8') as read_file:
        while True:
            line = read_file.readline()
            if not line:
                break

            line = line.replace(" ", "")
            length = len(line.split(","))

            if length > 3:  # assume everything on one line
                tags = line.split(",")
                for tag in tags:
                    all_tags.append(tag)
            else:  # assume cascaded tags
                tag = line.split(",")[0]
                all_tags.append(tag)
        read_file.close()
    return all_tags.copy()

def parse_files_all_tags(file_list):
    all_tags_all_files = {}
    temp = '\\' if is_windows() else '/'
    for single_file in file_list:
        img_id = single_file.split(temp)[-1].split(".")[0]
        all_tags = parse_single_all_tags(single_file)
        all_tags_all_files[img_id] = all_tags
    return all_tags_all_files.copy()

def parse_csv_all_tags(csv_file_path):
    # verbose_print(f"csv_file_path:\t\t{csv_file_path}")
    temp_dict = {}
    counter = 0
    with open(csv_file_path, 'r', encoding='utf-8') as read_file:
        while True:
            line = read_file.readline()
            if not line:
                break
            if counter > 0:
                line = line.replace(" ", "")
                key = line.split(',')[0]
                value = line.split(',')[-1]
                temp_dict[key] = int(value.strip())
            counter += 1
        read_file.close()
    return temp_dict.copy()

def merge_dict(path1, path2, path3):
    png_list = glob.glob(os.path.join(path1, f"*.png"))
    png_list = [x.replace(f".png", f".txt") for x in png_list]

    jpg_list = glob.glob(os.path.join(path2, f"*.jpg"))
    jpg_list = [x.replace(f".jpg", f".txt") for x in jpg_list]

    gif_list = glob.glob(os.path.join(path3, f"*.gif"))
    gif_list = [x.replace(f".gif", f".txt") for x in gif_list]

    temp = {}
    temp["png"] = parse_files_all_tags(png_list)
    temp["jpg"] = parse_files_all_tags(jpg_list)
    temp["gif"] = parse_files_all_tags(gif_list)
    temp["searched"] = {}
    return temp.copy()

def write_tags_to_text_file(input_string, file_path):
    verbose_print(f"input_string:\t{input_string}")
    verbose_print(f"file_path:\t{file_path}")
    with open(file_path, 'w', encoding="utf-8") as file:
        file.write(input_string)
    file.close()

def dict_to_sorted_list(d):
    return sorted([[k, v] for k, v in d.items()], key=lambda x: x[1], reverse=True)

def write_tags_to_csv(dictionary, file_path):
    temp = '\\' if is_windows() else '/'
    csv_name = (file_path.split(temp)[-1]).split('.csv')[0]
    header_string = f"{csv_name},count"
    if "tags" in header_string:
        header_string = f"tag,count"
    # sort tags descending by frequency
    sort_dictionary_to_list = dict_to_sorted_list(dictionary)

    with open(file_path, 'w', encoding="utf-8") as file:
        file.write(f"{header_string}\n")
        for pair in sort_dictionary_to_list:
            file.write(f"{pair[0]},{pair[1]}\n")
    file.close()

def update_all_csv_dictionaries(artist_csv_dict, character_csv_dict, species_csv_dict, general_csv_dict, meta_csv_dict,
                                rating_csv_dict, tags_csv_dict, string_category, tag, op, count):
    if string_category in "artist":
        if tag in list(artist_csv_dict.keys()):
            artist_csv_dict[tag] = ops[op](artist_csv_dict[tag], count)
        else:
            artist_csv_dict[tag] = ops[op](0, count)
    if string_category in "character":
        if tag in list(character_csv_dict.keys()):
            character_csv_dict[tag] = ops[op](character_csv_dict[tag], count)
        else:
            character_csv_dict[tag] = ops[op](0, count)
    if string_category in "species":
        if tag in list(species_csv_dict.keys()):
            species_csv_dict[tag] = ops[op](species_csv_dict[tag], count)
        else:
            species_csv_dict[tag] = ops[op](0, count)
    if string_category in "general":
        if tag in list(general_csv_dict.keys()):
            general_csv_dict[tag] = ops[op](general_csv_dict[tag], count)
        else:
            general_csv_dict[tag] = ops[op](0, count)
    if string_category in "meta":
        if tag in list(meta_csv_dict.keys()):
            meta_csv_dict[tag] = ops[op](meta_csv_dict[tag], count)
        else:
            meta_csv_dict[tag] = ops[op](0, count)
    if string_category in "rating":
        if tag in list(rating_csv_dict.keys()):
            rating_csv_dict[tag] = ops[op](rating_csv_dict[tag], count)
        else:
            rating_csv_dict[tag] = ops[op](0, count)
    # change the global tag csv
    if tag in list(tags_csv_dict.keys()):
        tags_csv_dict[tag] = ops[op](tags_csv_dict[tag], count)
    else:
        tags_csv_dict[tag] = ops[op](0, count)

    return artist_csv_dict.copy(), character_csv_dict.copy(), species_csv_dict.copy(), general_csv_dict.copy(), \
           meta_csv_dict.copy(), rating_csv_dict.copy(), tags_csv_dict.copy()

# one entry per line
def get_text_file_data(file_path, tag_per_line):
    all_tags = []
    # verbose_print(f"file_path:\t\t{file_path}")
    with open(file_path, 'r', encoding='utf-8') as read_file:
        while True:
            line = read_file.readline()
            if not line:
                break
            line = line.replace(" ", "")
            if tag_per_line == 1:
                tag = line
                if "," in line:
                    tag = line.split(",")[0]
                all_tags.append(tag)
            elif tag_per_line > 1:
                keyword = line.split(",")[0]
                replacements = line.split(",")[1:]
                all_tags.append([keyword, replacements])
        read_file.close()
    return all_tags

def get_href_links(url):
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')

        href_links = []
        for link in links:
            href = link.get('href')
            if href:
                href_links.append(href)

        return href_links
    else:
        verbose_print(f"Request to {url} failed with status code: {response.status_code}")
        return []

def extract_time_and_href(url):
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Assuming that the list elements are wrapped within a <ul> or <ol> tag.
        list_elements = soup.find_all(['li', 'ol'])

        results = []

        for element in list_elements:
            link = element.find('a')
            time_element = element.find('time')

            if link and time_element:
                href = link.get('href')
                time_value = time_element.get('datetime') or time_element.text
                time_object = parse(time_value)
                results.append([href, time_object])

        # Sort the results based on datetime object, newest to oldest
        sorted_results = sorted(results, key=lambda x: x[-1], reverse=True)

        return sorted_results
    else:
        verbose_print(f"Request to {url} failed with status code: {response.status_code}")
        return []

model_download_options = ["Fluffusion", "FluffyRock"]

def get_fluffusion_models():
    # get all model names
    url = "https://static.treehaus.dev/sd-checkpoints/fluffusionR1/"#####https://static.treehaus.dev/sd-checkpoints/fluffusionR1/archive/
    href_links = get_href_links(url)
    temp_list = set()
    for href_link in href_links:
        if "/" in href_link:
            temp_list.add(href_link.split("/")[-1])
        else:
            temp_list.add(href_link)
        verbose_print(f"href_link:\t{href_link}")
    # filter out fluffyrock models
    temp_list = list(temp_list)
    for i in range(len(temp_list)-1, -1, -1):
        if (model_download_options[-1]).lower() in temp_list[i] or not "safetensors" in (temp_list[i]).split(".")[-1]:
            temp_list.remove(temp_list[i])
    sorted_results = sorted(temp_list, key=lambda x: x)
    return sorted_results

def extract_time_and_href_github(api_url):
    response = requests.get(api_url)
    release_list = []

    # releases are already ordered most recent to oldest
    # so take the first 5 to look at

    if response.status_code == 200:
        releases = response.json()

        counter = 0
        for release in releases:
            if counter >= 5:
                break
            temp_list = []
            temp_list.append(release['tag_name'])

            verbose_print(f"Release: {release['tag_name']} - {release['html_url']}")
            # Add source code archives to download URLs
            download_urls = [release['zipball_url']]
            assets_url = release['assets_url']
            assets_response = requests.get(assets_url)
            if assets_response.status_code == 200:
                assets = assets_response.json()
                asset_download_urls = [asset['browser_download_url'] for asset in assets]
                download_urls.extend(asset_download_urls)
                temp_list.append(download_urls)
                for url in download_urls:
                    verbose_print(f"Download URL: {url}")
            else:
                verbose_print(
                    f"Failed to fetch assets for release {release['tag_name']}. Status code: {assets_response.status_code}")
                verbose_print(f"403 error means you've DONE OVER 60 API CALLS to githubs API per 1 hour. Now you have to wait! or do it manually")
                temp_list.append([])
            verbose_print("")  # Add an empty line for better readability
            release_list.append(temp_list)
            counter += 1
    else:
        verbose_print(f"Failed to fetch the releases. Status code:\t{response.status_code}")
        verbose_print(f"403 error means you've DONE OVER 60 API CALLS to githubs API per 1 hour. Now you have to wait! or do it manually")
    return copy.deepcopy(release_list)

def download_negative_tags_file():
    url = "https://raw.githubusercontent.com/pikaflufftuft/pikaft-e621-posts-downloader/main/remove_tags.txt"
    verbose_print(f"DOWNLOADING asset:\t{url}")
    download_url(url, url.split('/')[-1])
    verbose_print("Done")

def get_today_datetime():
    now = datetime.now()
    # Format the date as "year-month-day"
    formatted_date = now.strftime("%Y-%m-%d")
    return formatted_date

def download_all_e6_tags_csv(proxy_url=None):
    before_count = len(glob.glob(os.path.join(os.getcwd(), f"tags-*.csv")))
    verbose_print(f"before_count:\t{before_count}")

    repo_name = f"{'tags-'}{get_today_datetime()}{'.csv.gz'}"
    url = f"{'https://e621.net/db_export/'}{repo_name}"
    verbose_print(f"DOWNLOADING asset:\t{url}")
    try:
        download_url(url, repo_name)
    except sub.CalledProcessError as e:
        verbose_print(f"Tag file not yet uploaded/created. Trying again with (DAY - 1)")

    if len(glob.glob(os.path.join(os.getcwd(), f"*.gz"))) > 0:
        # finally unzip the file
        unzip_all()
        delete_all_archives()

    after_count = len(glob.glob(os.path.join(os.getcwd(), f"tags-*.csv")))
    verbose_print(f"after_count:\t{after_count}")

    if (after_count - before_count) == 0:
        day = int((((repo_name.split('.csv.gz')[0]).split('-'))[-1]))
        temp = '-'.join(((repo_name.split('.csv.gz')[0]).split('-'))[:-1])
        day = str(day-1).zfill(2)
        repo_name = f"{temp}-{day}.csv.gz"

        verbose_print(f"repo_name:\t{repo_name}")

        url = f"{'https://e621.net/db_export/'}{repo_name}"
        verbose_print(f"DOWNLOADING asset:\t{url}")
        download_url(url, repo_name)

        # finally unzip the file
        unzip_all()
        delete_all_archives()

    verbose_print("Done")

def days_since(date_str: str) -> int:
    # Parse the input date string into a datetime object
    input_date = datetime.strptime(date_str, "%Y-%m-%d")
    # Get the current date
    current_date = datetime.now()
    # Calculate the difference in days
    days_difference = (current_date - input_date).days
    verbose_print(f"days_difference:\t{days_difference}")
    return days_difference

def sort_csv_files_by_date(path: str) -> list:
    # List all files in the specified directory
    files = os.listdir(path)
    # Filter the files by the specified format
    csv_files = [file for file in files if re.match(r'^tags-\d{4}-\d{2}-\d{2}\.csv$', file)]
    # Sort the files by date (newest to oldest)
    sorted_csv_files = sorted(csv_files, key=lambda x: datetime.strptime(x[5:15], "%Y-%m-%d"), reverse=True)
    verbose_print(f"sorted_csv_files:\t{sorted_csv_files}")
    return sorted_csv_files

def check_to_update_csv(proxy_url=None):
    VALID_TIME_RANGE = 7
    cwd = os.getcwd()
    csv_files = sort_csv_files_by_date(cwd)
    if len(csv_files) > 0:
        # get datatime string from newest
        date = ((csv_files[0].split("tags-"))[-1]).split(".csv")[0]
        if days_since(date) >= VALID_TIME_RANGE:
            download_all_e6_tags_csv(proxy_url=proxy_url)
            verbose_print(f"ALL TAGS CSV HAS BEEN UPDATED. PLEASE REMOVE OLDER VERSION/S")
            return True
        else:
            return False
    else:
        download_all_e6_tags_csv(proxy_url=proxy_url)
        verbose_print(f"ALL TAGS CSV HAS BEEN UPDATED. PLEASE REMOVE OLDER VERSION/S")
        return True

def is_installed(package):
    try:
        spec = importlib.util.find_spec(package)
    except ModuleNotFoundError:
        return False
    return spec is not None

def copy_over_imgs(src, dst, image_mode_choice_state):

    verbose_print(f"src folder:\t{src}")
    verbose_print(f"dst folder:\t{dst}")

    temp = '\\' if is_windows() else '/'
    if image_mode_choice_state.lower() == 'single':
        if '.png' in src or '.jpg' in src:
            shutil.copy(src, dst)

            file_name_src, _ = os.path.splitext(src)
            file_name_src = f"{file_name_src}.txt"
            path_src = os.path.join(src, file_name_src)

            file_name_dst, _ = os.path.splitext(dst)
            file_name_dst = f"{file_name_dst}.txt"
            path_dst = os.path.join(dst, file_name_dst)

            verbose_print(f"path_src:\t{path_src}")
            verbose_print(f"path_dst:\t{path_dst}")

            if os.path.exists(path_src):
                shutil.copy(path_src, path_dst)
            else:
                # create a new file & assumes NO tags
                f = open(path_dst, 'w')
                f.close()
    else:
        # Fetching the list of all the files
        files = os.listdir(src)
        # Fetching all the files to directory
        for file_name in files:
            if '.png' in file_name or '.jpg' in file_name:
                shutil.copy(os.path.join(src, file_name), os.path.join(dst, file_name))

                file_name, _ = os.path.splitext(file_name)
                file_name = f"{file_name}.txt"
                path = os.path.join(src, file_name)

                verbose_print(f"path_src:\t{os.path.join(src, file_name)}")
                verbose_print(f"path_dst:\t{os.path.join(dst, file_name)}")

                if os.path.exists(path):
                    shutil.copy(path, os.path.join(dst, file_name))
                else:
                    # create a new file & assumes NO tags
                    f = open(os.path.join(dst, file_name), 'w')
                    f.close()
    verbose_print("Images are copied successfully")

def copy_over_tags(src, dst, image_mode_choice_state):
    temp = '\\' if is_windows() else '/'
    if image_mode_choice_state.lower() == 'single':
        if '.txt' in src:
            shutil.copy(src, dst)
    else:
        # Fetching the list of all the files
        files = os.listdir(src)
        # Fetching all the files to directory
        for file_name in files:
            if '.txt' in file_name:
                shutil.copy(os.path.join(src, file_name), os.path.join(dst, file_name))
    verbose_print("Files are copied successfully")

def check_requirements():
    requirements_list = ['torch', 'onnxruntime', 'onnxruntime-gpu', 'protobuf==3.20']
    for requirement in requirements_list:
        if not is_installed(requirement):

            verbose_print(f"package ( {requirement} ) is NOT installed!!!")
            verbose_print(f"internet connection NEEDED to install")

            command_str = "pip install "
            command_str = f"{command_str}{requirement}"
            for line in execute(command_str.split(" ")):
                verbose_print(line)
    verbose_print('done')

def full_model_download_link(name, file_name):
    verbose_print(f"file_name:\t{file_name}")
    if name == "Fluffusion":
        url = "https://static.treehaus.dev/sd-checkpoints/fluffusionR1/"#####https://static.treehaus.dev/sd-checkpoints/fluffusionR1/archive/
        return f"{url}{file_name}"
    elif name == "FluffyRock":
        url = "https://huggingface.co/lodestones/furryrock-model-safetensors/resolve/main/"
        return f"{url}{(file_name.split('---')[0])}"

def get_nested_fluffyrock_models(folder_name_list):
    verbose_print(f"folder_name_list:\t{folder_name_list}")
    temp_list = set()
    for folder_name in folder_name_list:
        folder_name = ((folder_name.split('---'))[0]).split('/')[-1]
        verbose_print(f"url:\t{folder_name}")
        url = f"https://huggingface.co/lodestones/furryrock-model-safetensors/tree/main/{folder_name}/"
        verbose_print(f"url:\t{url}")

        # get all model names
        href_links = extract_time_and_href(url)
        for href_link in href_links:
            href_link, time_element = href_link
            if "/" in href_link:
                temp_list.add(f'{"/".join(((href_link.split(" / ")[-1]).split("/"))[-2:])}---{time_element}')
            else:
                temp_list.add(f'{"/".join(((href_link).split("/"))[-2:])}---{time_element}')
            verbose_print(f'href_link:\t{"/".join(((href_link).split("/"))[-2:])}\tand\ttime_element:\t{time_element}')
        # filter out non-safetensor files
    temp_list = list(temp_list)
    for i in range(len(temp_list) - 1, -1, -1):
        if not "safetensors" in (temp_list[i]).split(".")[-1]:
            temp_list.remove(temp_list[i])
    sorted_results = sorted(temp_list, key=lambda x: (x.split('---'))[-1], reverse=True)
    return sorted_results

def get_fluffyrock_models():
    # get all model names
    url = "https://huggingface.co/lodestones/furryrock-model-safetensors/tree/main/"
    href_links = extract_time_and_href(url)
    temp_list = set()
    for href_link in href_links:
        href_link, time_element = href_link
        if "/" in href_link:
            temp_list.add(f'{href_link.split(" / ")[-1]}---{time_element}')
        else:
            temp_list.add(f'{href_link}---{time_element}')
        verbose_print(f"href_link:\t{href_link}\tand\ttime_element:\t{time_element}")
    # filter out non-safetensor files
    temp_list = list(temp_list)
    for i in range(len(temp_list) - 1, -1, -1):
        if not "safetensors" in (temp_list[i]).split(".")[-1]:
            temp_list.remove(temp_list[i])
    sorted_results = sorted(temp_list, key=lambda x: (x.split('---'))[-1], reverse=True)
    return sorted_results

def get_model_names(name):
    if name == "Fluffusion":
        return get_fluffusion_models()
    elif name == "FluffyRock":
        return get_fluffyrock_models()

def download_models(model_download_types, model_download_checkbox_group, tagging_model_download_types, nested_model_links_checkbox_group):
    disable_flag = "--disable-ipv6"
    model_flag = False
    for model_name in model_download_checkbox_group:
        if "rock" in model_name.lower():
            model_flag = True
            break

    model_name_list = model_download_checkbox_group
    if model_flag:
        model_name_list = nested_model_links_checkbox_group

    auto_tag_models = []
    for model_name in model_name_list:
        verbose_print(f"model name:\t{model_name}")

        if "/" in model_name:
            if "rock" in model_name.lower():
                model_name = "/".join(model_name.split("/")[-2:])
            else:
                model_name = "/".join(model_name.split("/")[-1])

        # get full url path
        url_path = full_model_download_link(model_download_types, model_name)

        verbose_print(f"DOWNLOADING:\t{model_name}")
        download_url(url_path, url_path.split('/')[-1])
        verbose_print(f"Done")

    if tagging_model_download_types is not None and len(tagging_model_download_types) > 0:
        for each_model in tagging_model_download_types:
            # download caption model
            mc.download_caption_model(model_selection=each_model)

            # add to new tagging feature
            if os.path.exists(os.path.join(os.getcwd(), "Z3D-E621-Convnext")) \
                    and os.path.exists(os.path.join(os.getcwd(), "Z3D-E621-Convnext", "Z3D-E621-Convnext.onnx")):
                auto_tag_models.append("Z3D-E621-Convnext")
            else:# linux didn't register the file extension
                os.rename(src="iNMyyi2w", dst="iNMyyi2w.zip")
                # finally unzip the file
                unzip_all()
                delete_all_archives()
                auto_tag_models.append("Z3D-E621-Convnext")
                verbose_print("Done")

            if os.path.exists(os.path.join(os.getcwd(), "eva02-clip-vit-large-7704")) \
                    and os.path.exists(os.path.join(os.getcwd(), "eva02-clip-vit-large-7704", "model.onnx")):
                auto_tag_models.append("eva02-clip-vit-large-7704")

            if os.path.exists(os.path.join(os.getcwd(), "eva02-vit-large-448-8046")) \
                    and os.path.exists(os.path.join(os.getcwd(), "eva02-vit-large-448-8046", "model.pth")):
                auto_tag_models.append("eva02-vit-large-448-8046")

            if os.path.exists(os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035")) \
                    and os.path.exists(os.path.join(os.getcwd(), "experimental_efficientnetv2_m_8035", "model.pth")):
                auto_tag_models.append("experimental_efficientnetv2_m_8035")
    return auto_tag_models



def download_repos(repo_download_releases_only, repo_download_checkbox_group, release_assets_checkbox_group, repo_download_radio):
    if repo_download_releases_only:
        for asset_url in release_assets_checkbox_group:
            verbose_print(f"DOWNLOADING asset:\t{asset_url}")
            download_url(asset_url, asset_url.split('/')[-1])

            # no zip extension check (ONLY) check repos with the known issue on Linux
            if "kohya" in repo_download_radio.lower() or "auto1111" in repo_download_radio.lower():
                temp_file_name = asset_url.split("/")[-1]
                verbose_print(f"temp_file_name:\t{temp_file_name}")
                os.rename(src=temp_file_name, dst=temp_file_name+".zip")
                # finally unzip the file
                unzip_all()
                delete_all_archives()
                if os.path.exists(temp_file_name+".1"):
                    verbose_print(temp_file_name+".1")
                    os.remove(temp_file_name+".1") # if a copy remains
            else:
                # finally unzip the file
                unzip_all()
                delete_all_archives()
            verbose_print("Done")
    else:
        for repo_name in repo_download_checkbox_group:
            command_str = "git clone --progress "
            if "kohya" in repo_name.lower():
                # get full url path
                url_path = "https://github.com/bmaltais/kohya_ss.git"
                command_str = f"{command_str}{url_path}"
                verbose_print(f"DOWNLOADING repo:\t{repo_name}")
                for line in execute(command_str.split(" ")):
                    verbose_print(line)
            elif "tag" in repo_name.lower():
                # get full url path
                url_path = "https://github.com/KichangKim/DeepDanbooru.git"
                command_str = f"{command_str}{url_path}"
                verbose_print(f"DOWNLOADING repo:\t{repo_name}")
                for line in execute(command_str.split(" ")):
                    verbose_print(line)
                # also install the latest pre-trained model
                url_path = "https://github.com/KichangKim/DeepDanbooru/releases/download/v3-20211112-sgd-e28/deepdanbooru-v3-20211112-sgd-e28.zip"  # newest model
                verbose_print(f"DOWNLOADING pre-trained model:\t{repo_name}")
                download_url(url_path, repo_name)

                # finally unzip the file
                unzip_all()
                delete_all_archives()
                verbose_print("Done")
            elif "webui" in repo_name.lower():
                # get full url path
                url_path = "https://github.com/AUTOMATIC1111/stable-diffusion-webui.git"
                command_str = f"{command_str}{url_path}"
                verbose_print(f"DOWNLOADING repo:\t{repo_name}")
                for line in execute(command_str.split(" ")):
                    verbose_print(line)
            elif "invoke" in repo_name.lower():
                # get full url path
                url_path = "https://github.com/invoke-ai/InvokeAI.git"
                command_str = f"{command_str}{url_path}"
                verbose_print(f"DOWNLOADING repo:\t{repo_name}")
                for line in execute(command_str.split(" ")):
                    verbose_print(line)
            elif "comfyui" in repo_name.lower():
                # get full url path
                url_path = "https://github.com/comfyanonymous/ComfyUI.git"
                command_str = f"{command_str}{url_path}"
                verbose_print(f"DOWNLOADING repo:\t{repo_name}")
                for line in execute(command_str.split(" ")):
                    verbose_print(line)
            elif "plasma" in repo_name.lower():
                # get full url path
                url_path = "https://github.com/Jordach/comfy-plasma.git"
                command_str = f"{command_str}{url_path}"
                verbose_print(f"DOWNLOADING repo:\t{repo_name}")
                for line in execute(command_str.split(" ")):
                    verbose_print(line)
            verbose_print(f"Done")


def get_repo_releases(event_data):
    repo_release_urls = {}
    # populate the release options list & make button visible
    repo_download_options_no_auto1111 = ["Kohya_ss LORA Trainer", "Auto-Tagging Model", "InvokeAI", "AUTO1111 WEBUI"]
    owner = None
    repo = None
    release_options_radio_list = []

    if event_data.value == repo_download_options_no_auto1111[0]:
        owner = 'bmaltais'
        repo = 'kohya_ss'
    elif event_data.value == repo_download_options_no_auto1111[1]:
        owner = 'KichangKim'
        repo = 'DeepDanbooru'
    elif event_data.value == repo_download_options_no_auto1111[2]:
        owner = 'invoke-ai'
        repo = 'InvokeAI'
    elif event_data.value == repo_download_options_no_auto1111[3]:
        owner = 'AUTOMATIC1111'
        repo = 'stable-diffusion-webui'
    url = f'https://api.github.com/repos/{owner}/{repo}/releases'

    all_releases = extract_time_and_href_github(url) # list of lists containing [release name, list of downloads]
    verbose_print(f"all_releases:\t{all_releases}")

    for release in all_releases:
        header_text, urls = release
        release_options_radio_list.append(f"{header_text}")
        repo_release_urls[header_text] = urls
    return copy.deepcopy(release_options_radio_list), copy.deepcopy(repo_release_urls)

def convert_to_list_file(filepath):
    df = pd.read_csv(filepath)
    # Keep only the first column
    first_column = df.iloc[:, 0]
    # Delete the first row
    first_column = first_column.iloc[1:]
    # Save first column to a text file with one element per line
    first_column.to_csv('keep_tags.txt', index=False, header=False, lineterminator='\n')
    # Delete the dataframe
    del df

def get_full_text_path(download_folder_type, img_name, cwd):
    global settings_json
    full_path_downloads = os.path.join(os.path.join(cwd, settings_json["batch_folder"]), settings_json["downloaded_posts_folder"])
    full_path_gallery_type = os.path.join(full_path_downloads, settings_json[f"{download_folder_type}_folder"])
    full_path = os.path.join(full_path_gallery_type, f"{img_name}.txt")
    # help.verbose_print(f"img_name:\t\t{img_name}")
    # help.verbose_print(f"full_path:\t\t{full_path}")
    return full_path

# def load_tags_csv(proxy_url=None, settings_json=None, all_tags_ever_dict=None):
#     data = None
#     if ("use_csv_custom" in settings_json and settings_json["use_csv_custom"]) and \
#             ("csv_custom_path" in settings_json and len(settings_json["csv_custom_path"]) > 0):
#         try:
#             data = pd.read_csv(settings_json["csv_custom_path"])
#             # Check if there is a header
#             if data.columns.str.contains('Unnamed').any():
#                 data = pd.read_csv(settings_json["csv_custom_path"], header=None, skiprows=1)
#         except pd.errors.ParserError:
#             verbose_print("File not found or is not a CSV")
#
#         # take first three columns and name them
#         data = data.iloc[:, :3]
#         data.columns = ['name', 'category', 'post_count']
#     else:
#         # check to update the tags csv
#         check_to_update_csv(proxy_url=proxy_url)
#         # get newest
#         current_list_of_csvs = sort_csv_files_by_date(os.getcwd())
#         try:
#             # load
#             data = pd.read_csv(current_list_of_csvs[0], usecols=['name', 'category', 'post_count'])
#         except pd.errors.ParserError:
#             verbose_print("File not found or is not a CSV")
#
#     # Convert 'name' column to string type
#     data['name'] = data['name'].astype(str)
#     # Remove rows where post_count equals 0
#     data = data[data['post_count'] != 0]
#
#     # Convert the DataFrame into a dictionary
#     # where the key is 'name' and the values are lists of [category, post_count]
#     all_tags_ever_dict = data.set_index('name')[['category', 'post_count']].T.to_dict('list')
#
#     # all_tags_ever_dict = copy.deepcopy(data_dict) # this is the part that takes the most time
#     del data
#     # del data_dict
#     return all_tags_ever_dict


def dataframe_to_dict(df):
    array = df.to_numpy()
    return {row[0]: list(row[1:]) for row in array}


import concurrent.futures
import multiprocessing as mp
from tqdm import tqdm


def chunk_to_dict(chunk):
    """Convert a chunk of the DataFrame to the desired dictionary format."""
    array = chunk.to_numpy()
    return {row[0]: list(row[1:]) for row in array}


def parallel_dataframe_to_dict(df, num_threads):
    """Convert the DataFrame to a dictionary using parallel threads."""
    # Split DataFrame into chunks based on the number of threads
    chunk_size = len(df) // num_threads
    chunks = [df.iloc[i:i + chunk_size] for i in range(0, len(df), chunk_size)]

    result_dict = {}
    # Create a tqdm object
    with tqdm(total=len(chunks), desc="Processing Tag chunks", unit="chunk") as pbar:
        # Use ThreadPoolExecutor to process chunks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            for d in executor.map(chunk_to_dict, chunks):
                result_dict.update(d)
                pbar.update(1)  # Update the progress bar

    return result_dict


def preprocess_csv(proxy_url=None, settings_json=None, all_tags_ever_dict=None, invalid_categories=None):
    data = None
    if ("use_csv_custom" in settings_json and settings_json["use_csv_custom"]) and \
            ("csv_custom_path" in settings_json and len(settings_json["csv_custom_path"]) > 0):
        try:
            data = pd.read_csv(settings_json["csv_custom_path"])
            # Check if there is a header
            if data.columns.str.contains('Unnamed').any():
                data = pd.read_csv(settings_json["csv_custom_path"], header=None, skiprows=1)
        except pd.errors.ParserError:
            verbose_print("File not found or is not a CSV")

        # take first three columns and name them
        data = data.iloc[:, :3]
        data.columns = ['name', 'category', 'post_count']
    else:
        # check to update the tags csv
        downloaded_again = check_to_update_csv(proxy_url=proxy_url)
        # if no csv downloaded again and preprocessed_tags.parquet exist
        if not downloaded_again and os.path.exists('preprocessed_tags.parquet'):
            return

        # get newest
        current_list_of_csvs = sort_csv_files_by_date(os.getcwd())
        try:
            # load
            data = pd.read_csv(current_list_of_csvs[0], usecols=['name', 'category', 'post_count'])
        except pd.errors.ParserError:
            verbose_print("File not found or is not a CSV")

    # Data type conversions
    data['name'] = data['name'].astype(str)
    data['category'] = data['category'].astype('category')
    data['post_count'] = data['post_count'].astype(int)

    # Remove rows with invalid categories if provided
    if invalid_categories:
        data = data[~data['category'].isin(invalid_categories)]

    # Filter out rows
    data = data[data['post_count'] != 0]

    # Save the preprocessed data in Parquet format (or Feather)
    data.to_parquet('preprocessed_tags.parquet', index=False)

def load_tags_csv_fast():
    data = pd.read_parquet('preprocessed_tags.parquet')
    # all_tags_ever_dict = data.set_index('name')[['category', 'post_count']].T.to_dict('list')
    all_tags_ever_dict = parallel_dataframe_to_dict(data, mp.cpu_count()) # use all available threads
    verbose_print("Done Loading Tags!")
    del data
    return all_tags_ever_dict

def load_trie(trie, all_tags_ever_dict):
    verbose_print("Starting Trie Tree Construction!")
    # Add data to the trie with a progress bar
    for tag in tqdm(all_tags_ever_dict.keys(), desc="Loading Trie"):
        trie[tag] = all_tags_ever_dict[tag][1]
    verbose_print("Done constructing Trie tree!")

def get_batch_name(f_name):
    settings_file = load_session_config(f_name)
    return settings_file["batch_folder"]

def get_batch_names(paths):
    names = []
    for path in paths:
        names.append(get_batch_name(path))
    return names

def map_batches_to_files(f_names, b_names):
    return {b_name: f_name for f_name, b_name in zip(f_names, b_names)}

