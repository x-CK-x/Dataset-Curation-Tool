import copy
import glob
import json
import os
from pathlib import Path
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

from tqdm import tqdm

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

def get_list(arb_string, delimeter):
    return arb_string.split(delimeter)

def get_string(arb_list, delimeter):
    return delimeter.join(arb_list)

def from_padded(line):
    if len(line) > 1:# check for padded-0
        if int(line[0]) == 0:# remove the 0, cast to int, return
            return int(line[-1])
    return int(line)

def to_padded(num):
    return f"{num:02}"

def is_windows():
    return os.name == 'nt'

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
    # verbose_print(f"single_file:\t\t{csv_file_path}")
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
    print(f"input_string:\t{input_string}")
    print(f"file_path:\t{file_path}")
    with open(file_path, 'w') as file:
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

    with open(file_path, 'w') as file:
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
        print(f"Request to {url} failed with status code: {response.status_code}")
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
        print(f"Request to {url} failed with status code: {response.status_code}")
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

            print(f"Release: {release['tag_name']} - {release['html_url']}")
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
                    print(f"Download URL: {url}")
            else:
                print(
                    f"Failed to fetch assets for release {release['tag_name']}. Status code: {assets_response.status_code}")
                print(f"403 error means you've DONE OVER 60 API CALLS to githubs API per 1 hour. Now you have to wait! or do it manually")
                temp_list.append([])
            print()  # Add an empty line for better readability
            release_list.append(temp_list)
            counter += 1
    else:
        print("Failed to fetch the releases. Status code:", response.status_code)
        print(f"403 error means you've DONE OVER 60 API CALLS to githubs API per 1 hour. Now you have to wait! or do it manually")
    return copy.deepcopy(release_list)


def download_file(url: str, target_file: Path | str, *, proxy_url: str | None = None) -> None:
    proxies = {'http': proxy_url, 'https': proxy_url} if proxy_url else None
    with requests.get(url, stream=True, proxies=proxies) as response:
        total_length_repr = response.headers.get("Content-Length")
        total_length = int(total_length_repr) if total_length_repr else None

        with tqdm.wrapattr(response.raw, "read", total=total_length, desc="") as raw:
            with open(target_file, 'wb') as output:
                shutil.copyfileobj(raw, output)


def download_negative_tags_file(proxy_url: str | None = None) -> None:
    url = "https://raw.githubusercontent.com/pikaflufftuft/pikaft-e621-posts-downloader/main/remove_tags.txt"
    verbose_print(f"DOWNLOADING asset:\t{url}")
    download_file(url, "remove_tags.txt", proxy_url=proxy_url)
    verbose_print("Done")

def get_today_datetime():
    now = datetime.now()
    # Format the date as "year-month-day"
    formatted_date = now.strftime("%Y-%m-%d")
    return formatted_date

def download_all_e6_tags_csv(proxy_url: str | None = None) -> None:
    before_count = len(glob.glob(os.path.join(os.getcwd(), f"tags-*.csv")))
    verbose_print(f"before_count:\t{before_count}")

    repo_name = f"tags-{get_today_datetime()}.csv.gz"
    url = f"{'https://e621.net/db_export/'}{repo_name}"
    target_file = Path.cwd() / repo_name
    verbose_print(f"DOWNLOADING asset:\t{url}")
    try:
        download_file(url, target_file, proxy_url=proxy_url)
    except sub.CalledProcessError as e:
        verbose_print(f"{e.output}")

    if len(glob.glob(os.path.join(os.getcwd(), f"*.gz"))) > 0:
        # finally unzip the file
        unzip_all()
        delete_all_archives()

    after_count = len(glob.glob(os.path.join(os.getcwd(), f"tags-*.csv")))
    verbose_print(f"after_count:\t{after_count}")

    if (after_count - before_count) == 0:
        day = int((((repo_name.split('.csv.gz')[0]).split('-'))[-1]))
        temp = '-'.join(((repo_name.split('.csv.gz')[0]).split('-'))[:-1])
        repo_name = f"{temp}-{(day-1)}.csv.gz"

        verbose_print(f"repo_name:\t{repo_name}")

        url = f"{'https://e621.net/db_export/'}{repo_name}"
        target_file = Path.cwd() / repo_name
        verbose_print(f"DOWNLOADING asset:\t{url}")
        download_file(url, target_file, proxy_url=proxy_url)

        # finally unzip the file
        unzip_all()
        delete_all_archives()

    verbose_print("Done")

def download_zack3d_model(proxy_url: str | None = None):
    url = "https://pixeldrain.com/api/file/iNMyyi2w"
    target_file = Path.cwd() / "Z3D-E621-Convnext.zip"
    verbose_print(f"DOWNLOADING asset:\t{url}")
    download_file(url, target_file, proxy_url=proxy_url)

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

def check_to_update_csv(proxy_url: str | None = None):
    VALID_TIME_RANGE = 7
    cwd = os.getcwd()
    csv_files = sort_csv_files_by_date(cwd)
    if len(csv_files) > 0:
        # get datatime string from newest
        date = ((csv_files[0].split("tags-"))[-1]).split(".csv")[0]
        if days_since(date) >= VALID_TIME_RANGE:
            download_all_e6_tags_csv(proxy_url=proxy_url)
            verbose_print(f"ALL TAGS CSV HAS BEEN UPDATED. PLEASE REMOVE OLDER VERSION/S")
    else:
        download_all_e6_tags_csv(proxy_url=proxy_url)
        verbose_print(f"ALL TAGS CSV HAS BEEN UPDATED. PLEASE REMOVE OLDER VERSION/S")

def is_installed(package):
    try:
        spec = importlib.util.find_spec(package)
    except ModuleNotFoundError:
        return False
    return spec is not None

def copy_over_imgs(src, dst, image_mode_choice_state):
    temp = '\\' if is_windows() else '/'
    if image_mode_choice_state.lower() == 'single':
        if '.png' in src or '.jpg' in src:
            shutil.copy(src, dst)

            file_name_src = list(src)
            del file_name_src[-3:]
            file_name_src = ''.join(file_name_src)
            file_name_src += 'txt'
            path_src = os.path.join(src, file_name_src)

            file_name_dst = list(src)
            del file_name_dst[-3:]
            file_name_dst = ''.join(file_name_dst)
            file_name_dst += 'txt'
            path_dst = os.path.join(src, file_name_dst)

            if not os.path.exists(path_src):
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

                file_name = list(file_name)
                del file_name[-3:]
                file_name = ''.join(file_name)
                file_name += 'txt'
                path = os.path.join(src, file_name)
                if os.path.exists(path):
                    shutil.copy(path, os.path.join(dst, file_name))
                else:
                    # create a new file & assumes NO tags
                    f = open(os.path.join(dst, file_name), 'w')
                    f.close()
    print("Images are copied successfully")

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
    print("Files are copied successfully")

def check_requirements():
    requirements_list = ['torch', 'onnxruntime', 'onnxruntime-gpu', 'protobuf==3.20']
    for requirement in requirements_list:
        if not is_installed(requirement):
            command_str = "pip install "
            command_str = f"{command_str}{requirement}"
            for line in execute(command_str.split(" ")):
                verbose_print(line)
    print('done')

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

def download_models(model_download_types,
                    model_download_checkbox_group,
                    tagging_model_download_types,
                    nested_model_links_checkbox_group,
                    proxy_url: str | None = None,
                    ):
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
        command_str = f"wget "
        progress_flag = "-q --show-progress "

        # get full url path
        url_path = full_model_download_link(model_download_types, model_name)
        file_name = url_path.rsplit("/", maxsplit=1)[1]
        target_file = Path.cwd() / file_name

        verbose_print(f"DOWNLOADING:\t{model_name}")
        download_file(url_path, target_file, proxy_url=proxy_url)
        verbose_print(f"Done")
    if tagging_model_download_types is not None and len(tagging_model_download_types) > 0:
        # download zack3d's model
        download_zack3d_model()
        # add to new tagging feature
        if len(auto_tag_models)==0 and os.path.exists(os.path.join(os.getcwd(), 'Z3D-E621-Convnext')) \
                and os.path.exists(os.path.join(os.path.join(os.getcwd(), 'Z3D-E621-Convnext'), 'Z3D-E621-Convnext.onnx')):
            auto_tag_models.append('Z3D-E621-Convnext')
        if len(auto_tag_models)==0 and os.path.exists(os.path.join(os.getcwd(), 'Fluffusion-AutoTag')) \
                and os.path.exists(os.path.join(os.path.join(os.getcwd(), 'Fluffusion-AutoTag'), 'Fluffusion-AutoTag.pb')):
            auto_tag_models.append('Fluffusion-AutoTag')
    return auto_tag_models



def download_repos(repo_download_releases_only,
                   repo_download_checkbox_group,
                   release_assets_checkbox_group,
                   proxy_url: str | None = None,
                   ) -> None:
    if repo_download_releases_only:
        for asset_url in release_assets_checkbox_group:
            file_name = asset_url.rsplit("/", maxsplit=1)[1]
            target_file = Path.cwd() / file_name
            verbose_print(f"DOWNLOADING asset:\t{asset_url}")
            download_file(asset_url, target_file, proxy_url=proxy_url)

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
                command_str = f"wget "
                progress_flag = "-q --show-progress "

                url_path = "https://github.com/KichangKim/DeepDanbooru/releases/download/v3-20211112-sgd-e28/deepdanbooru-v3-20211112-sgd-e28.zip"  # newest model

                file_name = url_path.rsplit("/", maxsplit=1)[1]
                target_file = Path.cwd() / file_name
                verbose_print(f"DOWNLOADING pre-trained model:\t{repo_name}")
                download_file(url_path, target_file, proxy_url=proxy_url)

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
            verbose_print(f"Done")


def get_repo_releases(event_data):
    repo_release_urls = {}
    # populate the release options list & make button visible
    repo_download_options_no_auto1111 = ["Kohya_ss LORA Trainer", "Auto-Tagging Model", "InvokeAI"]
    url = None
    release_options_radio_list = []

    if event_data.value == repo_download_options_no_auto1111[0]:
        owner = 'bmaltais'
        repo = 'kohya_ss'
        url = f'https://api.github.com/repos/{owner}/{repo}/releases'
    elif event_data.value == repo_download_options_no_auto1111[1]:
        owner = 'KichangKim'
        repo = 'DeepDanbooru'
        url = f'https://api.github.com/repos/{owner}/{repo}/releases'
    elif event_data.value == repo_download_options_no_auto1111[2]:
        owner = 'invoke-ai'
        repo = 'InvokeAI'
        url = f'https://api.github.com/repos/{owner}/{repo}/releases'

    all_releases = extract_time_and_href_github(url) # list of lists containing [release name, list of downloads]
    verbose_print(f"all_releases:\t{all_releases}")

    for release in all_releases:
        header_text, urls = release
        release_options_radio_list.append(f"{header_text}")
        repo_release_urls[header_text] = urls
    return copy.deepcopy(release_options_radio_list), copy.deepcopy(repo_release_urls)

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
