import asyncio
import gzip
import json
import logging
import multiprocessing
import os
import re
import shutil
import subprocess
import time
from ctypes import c_int
from dataclasses import dataclass
from datetime import datetime
from itertools import pairwise, repeat
from logging import FileHandler, Logger
from pathlib import Path
from typing import Generic, Sequence, TypeVar

import aiofiles
import cv2
import polars as pl
import requests
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from tqdm.auto import tqdm


_Meta = TypeVar("_Meta")


@dataclass
class DownloadTask(Generic[_Meta]):
    url: str
    target_file: Path
    meta: _Meta


@dataclass
class FinishedDownload(Generic[_Meta]):
    task: DownloadTask[_Meta]
    exc: Exception | None

    @property
    def ok(self) -> bool:
        if self.exc:
            return False
        return True


class FilesDownloader:

    def __init__(self,
                 *,
                 workers_count: int = 16,
                 chunk_size: int = 1024**2,
                 proxy_url: str | None = None,
                 logs_paths: tuple[str | Path, str | Path] | None = None,
                 log_level: int | str | None = None,
                 ) -> None:
        self._workers_count = workers_count
        self._chunk_size = chunk_size
        self._proxy_url = proxy_url
        self._log = Logger("downloader", level=log_level or 0)
        self._err_log = Logger("Download", level=logging.WARNING)
        log_path, err_log_path = None, None
        if logs_paths:
            log_path, err_log_path = map(Path, logs_paths)
            log_handler = FileHandler(log_path, mode="w", encoding="utf-8")
            err_handler = FileHandler(log_path, mode="w", encoding="utf-8")
            self._log.addHandler(log_handler)
            self._err_log.addHandler(err_handler)
        self.log_path, self.err_log_path = log_path, err_log_path

    def download_all(self, infos: Sequence[DownloadTask[_Meta]]) -> list[FinishedDownload[_Meta]]:
        self._log.info("Start downloading")
        try:
            results = asyncio.run(self._process(infos))
        except Exception as exc:
            self._err_log.exception("Error during downloading files. ", exc_info=exc)
            raise exc
        return results

    async def _process(self, tasks: Sequence[DownloadTask[_Meta]]) -> list[FinishedDownload[_Meta]]:
        queue: asyncio.Queue[tuple[ClientSession, DownloadTask[_Meta]]] = asyncio.Queue()
        connector = ProxyConnector.from_url(self._proxy_url) if self._proxy_url else None
        workers_count = min(len(tasks), self._workers_count)
        async with ClientSession(connector=connector) as client:
            for download_info in tasks:
                queue.put_nowait((client, download_info))
            with tqdm(total=queue.qsize()) as total_progress:
                events: list[asyncio.Event | None] = [asyncio.Event() for _ in range(workers_count-1)]
                events = [None, *events, None]
                event_pairs = list(pairwise(events))
                self._log.info("Start %s workers", workers_count)
                workers = [
                    self._wrapped_worker(queue, total_progress, n, events)
                    for n, events in enumerate(event_pairs, start=1)
                ]
                finished, _ = await asyncio.wait(workers)
        total_results: list[FinishedDownload[_Meta]] = []
        for task in finished:
            results = task.result()
            total_results.extend(results)
        return total_results

    async def _wrapped_worker(self,
                              queue: asyncio.Queue[tuple[ClientSession, DownloadTask[_Meta]]],
                              total_progress: tqdm | None = None,
                              worker_position: int = 0,
                              syncronisation_events: tuple[asyncio.Event | None, asyncio.Event | None] = (None, None),
                              ) -> list[FinishedDownload[_Meta]]:
        self._log.info("Start worker #%s", worker_position)
        self_event, next_event = syncronisation_events
        if self_event:
            await self_event.wait()
            self_event.clear()
        with tqdm(desc=f"Worker {worker_position:02}", unit="B", unit_scale=True, position=worker_position) as progress:
            if next_event:
                next_event.set()
            self._log.info("Worker %s ready, start downloading files", worker_position)
            results = await self._worker(queue, progress, total_progress)
            self._log.info("Worker %s done", worker_position)
            if self_event:
                await self_event.wait()
            if next_event:
                next_event.set()
        return results

    async def _worker(self,
                      queue: asyncio.Queue[tuple[ClientSession, DownloadTask[_Meta]]],
                      progress: tqdm,
                      total_progress: tqdm
                      ) -> list[FinishedDownload[_Meta]]:
        results: list[FinishedDownload[_Meta]] = []
        while not queue.empty():
            client, task = await queue.get()
            exception = None
            self._log.info("Downloading '%s' to '%s'", task.url, task.target_file)
            try:
                await self._download(client, task, progress)
            except Exception as exc:
                exception = exc
                self._log.exception(
                    "Error occurs while downloading '%s' to '%s'",
                    task.url, task.target_file,
                    exc_info=exc
                )
            self._log.info("Successfully downloaded '%s' to '%s'", task.url, task.target_file)
            results.append(FinishedDownload(task, exception))
            if total_progress:
                total_progress.update(1)
        return results

    async def _download(self, client: ClientSession, task: DownloadTask, progress: tqdm) -> int:
        async with client.get(task.url) as response:
            response.raise_for_status()
            content_length = response.content_length or 0
            progress.reset(content_length)
            async with aiofiles.open(task.target_file, "wb") as file:
                async for data in response.content.iter_any():
                    content_length += len(data)
                    await file.write(data)
                    progress.update(len(data))
        return content_length


class E6_Downloader:
    def check_param_batch_count(self, prms):
        batch_count = None
        for param_name, parameter in prms.items():
            if isinstance(parameter, list):
                if batch_count is None:
                    batch_count = len(parameter)
                else:
                    if len(parameter) != batch_count:
                        raise ValueError(
                            f'Batch count inconsistent with {param_name}. Expected {batch_count}, found {len(parameter)} instead')

        if isinstance(prms['save_searched_list_type'], list) and not isinstance(prms['save_searched_list_path'], list):
            raise ValueError('there should be no multiple save_searched_list_type for a single save_searched_list_path')

        if batch_count is None:
            batch_count = 1

        return batch_count


    def normalize_params(self, prms, batch_count):
        for param_name, parameter in prms.items():
            if not isinstance(parameter, list):
                prms[param_name] = [parameter] * batch_count


    def check_valid_param(self, lst, name, options, typ=None):
        for item in lst:
            if options is not None:
                if item not in options:
                    raise ValueError(f'{name} of {item} is invalid. Use {options} only.')
            elif not isinstance(item, typ):
                raise ValueError(f'Invalid {name} type of {item}. Use type:{typ} only.')


    def removeslash(self, s):  # removesuffix version for python 3.8
        return s[:-1] if (s[-1] == '/') else s


    def prep_params(self, prms, batch_count, base_folder):
        cat_to_num = {'general': 0, 'artist': 1, 'rating': 2, 'copyright': 3, 'character': 4, 'species': 5, 'invalid': 6,
                      'meta': 7, 'lore': 8}
        cat_set = set(cat_to_num.keys())

        self.check_valid_param(prms["batch_folder"], 'batch_folder', None, str)
        for i, folder in enumerate(prms["batch_folder"]):
            if os.path.isabs(folder):
                prms["batch_folder"][i] = self.removeslash(folder)
            else:
                prms["batch_folder"][i] = self.removeslash(f'{base_folder}/{folder.strip("/")}')
            os.makedirs(prms["batch_folder"][i], exist_ok=True)

        self.check_valid_param(prms["required_tags"], 'required_tags', None, str)
        self.check_valid_param(prms["blacklist"], 'blacklist', None, str)

        self.check_valid_param(prms["include_png"], 'include_png', (True, False))
        self.check_valid_param(prms["include_jpg"], 'include_jpg', (True, False))
        self.check_valid_param(prms["include_gif"], 'include_gif', (True, False))
        self.check_valid_param(prms["include_webm"], 'include_webm', (True, False))
        self.check_valid_param(prms["include_swf"], 'include_swf', (True, False))

        for i, g in enumerate(zip(prms["include_png"], prms["include_jpg"], prms["include_gif"], prms["include_webm"],
                                  prms["include_swf"])):
            if not any(g):
                raise ValueError(f'Please include at least one file type at batch {i}')

        self.check_valid_param(prms["include_explicit"], 'include_explicit', (True, False))
        self.check_valid_param(prms["include_questionable"], 'include_questionable', (True, False))
        self.check_valid_param(prms["include_safe"], 'include_safe', (True, False))

        for i, g in enumerate(zip(prms["include_explicit"], prms["include_questionable"], prms["include_safe"])):
            if not any(g):
                raise ValueError(f'Please include at least one rating at batch {i}')

        self.check_valid_param(prms["min_score"], 'min_score', None, int)
        self.check_valid_param(prms["min_fav_count"], 'min_fav_count', None, int)

        self.check_valid_param(prms["min_date"], 'min_date', None, str)
        for date in prms["min_date"]:
            if re.search("^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$|^\d{4}\-(0[1-9]|1[012])$|^\d{4}$",
                         date) is None:
                raise ValueError(f'Incorrect date format "{date}" Format should be YYYY-MM-DD or YYYY-MM or YYYY')

        self.check_valid_param(prms["min_area"], 'min_area', None, int)
        for idx in range(batch_count):
            if prms["min_area"][idx] < 0:
                prms["min_area"][idx] = -1

        self.check_valid_param(prms["do_sort"], 'do_sort', (True, False))
        self.check_valid_param(prms["top_n"], 'top_n', None, int)
        for i, n in enumerate(prms["top_n"]):
            if n < 1:
                prms["top_n"][i] = -1

        self.check_valid_param(prms["skip_posts_file"], 'skip_posts_file', None, str)
        for f in prms["skip_posts_file"]:
            if not os.path.isfile(f) and f != '':
                raise RuntimeError(f'skip_posts_file {f} not found')

        self.check_valid_param(prms["skip_posts_type"], 'skip_posts_type', ('id', 'md5'))

        self.check_valid_param(prms["collect_from_listed_posts_file"], 'collect_from_listed_posts_file', None, str)
        for f in prms["collect_from_listed_posts_file"]:
            if not os.path.isfile(f) and f != '':
                raise RuntimeError(f'collect_from_listed_posts_file {f} not found')
        self.check_valid_param(prms["collect_from_listed_posts_type"], 'collect_from_listed_posts_type', ('id', 'md5'))
        self.check_valid_param(prms["apply_filter_to_listed_posts"], 'apply_filter_to_listed_posts', (True, False))

        self.check_valid_param(prms["save_searched_list_type"], 'save_searched_list_type', ('id', 'md5', 'None'))

        self.check_valid_param(prms["save_searched_list_path"], 'save_searched_list_path', None, str)
        for i, p, t, base in zip(range(batch_count), prms["save_searched_list_path"], prms["save_searched_list_type"],
                                 prms["batch_folder"]):
            if t != 'None':
                if p != '':
                    dirpath = os.path.dirname(p)
                    if os.path.isabs(dirpath):
                        os.makedirs(dirpath, exist_ok=True)
                    else:
                        prms["save_searched_list_path"][i] = base + '/' + prms["save_searched_list_path"][i].strip('/')
                        os.makedirs(base + '/' + dirpath.strip('/'), exist_ok=True)
                else:
                    prms["save_searched_list_path"][i] = base + f'/list_of_searched_{t}s.txt'
            else:
                prms["save_searched_list_path"][i] = None

        get_searched_list_from_path = {}
        get_searched_list_type_from_path = {}
        for i, path in enumerate(prms["save_searched_list_path"]):
            if path is not None:
                if path not in get_searched_list_from_path:
                    get_searched_list_from_path[path] = set()
                    get_searched_list_type_from_path[path] = prms["save_searched_list_type"][i]
                else:
                    if get_searched_list_type_from_path[path] != prms["save_searched_list_type"][i]:
                        raise ValueError(f'Found reassignment of save type for save_searched_list_path {path} in batch {i}')
        prms["get_searched_list_from_path"] = get_searched_list_from_path
        prms["get_searched_list_type_from_path"] = get_searched_list_type_from_path

        self.check_valid_param(prms["downloaded_posts_folder"], 'downloaded_posts_folder', None, str)
        for i in range(batch_count):
            if prms["downloaded_posts_folder"][i] == '':
                prms["downloaded_posts_folder"][i] = prms["batch_folder"][i] + '/'
            else:
                prms["downloaded_posts_folder"][i] = prms["downloaded_posts_folder"][i].strip('/') + '/'
                if os.path.isabs(prms["downloaded_posts_folder"][i]):
                    os.makedirs(prms["downloaded_posts_folder"][i], exist_ok=True)
                else:
                    prms["downloaded_posts_folder"][i] = prms["batch_folder"][i] + '/' + prms["downloaded_posts_folder"][i]
                    os.makedirs(prms["downloaded_posts_folder"][i], exist_ok=True)

        for filetype_folder in ('png_folder', 'jpg_folder', 'gif_folder', 'webm_folder', 'swf_folder'):
            self.check_valid_param(prms[filetype_folder], filetype_folder, None, str)
            for i in range(batch_count):
                if prms[filetype_folder][i] == '':
                    prms[filetype_folder][i] = prms["downloaded_posts_folder"][i]
                else:
                    prms[filetype_folder][i] = prms[filetype_folder][i].strip('/') + '/'
                    if os.path.isabs(prms[filetype_folder][i]):
                        os.makedirs(prms[filetype_folder][i], exist_ok=True)
                    else:
                        prms[filetype_folder][i] = prms["downloaded_posts_folder"][i] + prms[filetype_folder][i]
                        os.makedirs(prms[filetype_folder][i], exist_ok=True)

        self.check_valid_param(prms["save_filename_type"], 'save_filename_type', ('id', 'md5'))
        self.check_valid_param(prms["include_tag_file"], 'include_tag_file', (True, False))
        self.check_valid_param(prms["skip_post_download"], 'skip_post_download', (True, False))

        self.check_valid_param(prms["tag_sep"], 'tag_sep', None, str)
        for i, sep in enumerate(prms["tag_sep"]):
            if sep == '':
                raise ValueError(f'tag separator in batch {i} is empty!')

        self.check_valid_param(prms["include_explicit_tag"], 'include_explicit_tag', (True, False))
        self.check_valid_param(prms["include_questionable_tag"], 'include_questionable_tag', (True, False))
        self.check_valid_param(prms["include_safe_tag"], 'include_safe_tag', (True, False))
        self.check_valid_param(prms["reorder_tags"], 'reorder_tags', (True, False))

        self.check_valid_param(prms["tag_order_format"], 'tag_order_format', None, str)
        tag_order = []
        selected_cats = []
        for form in prms["tag_order_format"]:
            sub_tag_order = [s.strip() for s in form.split(',')]
            sub_tag_order = [s for s in sub_tag_order if s != '']
            if len(sub_tag_order) == 0:
                raise ValueError('Please include at least one category')
            tag_order.append(sub_tag_order)
            sub_selected_cats = []
            for cat in sub_tag_order:
                if cat not in cat_set:
                    raise ValueError(f'{cat} is not a tag category')
                sub_selected_cats.append(cat_to_num[cat])
            selected_cats.append(sub_selected_cats)
        prms["tag_order"] = tag_order
        prms["selected_cats"] = selected_cats

        self.check_valid_param(prms["prepend_tags"], 'prepend_tags', None, str)
        self.check_valid_param(prms["append_tags"], 'append_tags', None, str)
        self.check_valid_param(prms["replace_underscores"], 'replace_underscores', (True, False))
        self.check_valid_param(prms["remove_parentheses"], 'remove_parentheses', (True, False))

        self.check_valid_param(prms["remove_tags_list"], 'remove_tags_list', None, str)
        for f in prms["remove_tags_list"]:
            if f != '':
                if not os.path.isfile(f):
                    raise ValueError(f'remove_tags_list {f} file not found')

        self.check_valid_param(prms["replace_tags_list"], 'replace_tags_list', None, str)
        replace_tags = []
        for f in prms["replace_tags_list"]:
            if f != '':
                if not os.path.isfile(f):
                    raise ValueError(f'replace_tags_list {f} file not found')
                with open(f, 'r') as file:
                    d = {}
                    for line in file:
                        l = line.strip().split(',')
                        key = l[0].strip()
                        val = l[1].strip()
                        if key == '' or val == '':
                            raise ValueError(f'Empty text found in replace_tags_list {f}')
                        d[key] = val
                replace_tags.append(d)
            else:
                replace_tags.append({})
        prms["replace_tags"] = replace_tags

        self.check_valid_param(prms["tag_count_list_folder"], 'tag_count_list_folder', None, str)
        for i in range(batch_count):
            if prms["tag_count_list_folder"][i] != '':
                prms["tag_count_list_folder"][i] = prms["tag_count_list_folder"][i].strip('/') + '/'
                if os.path.isabs(prms["tag_count_list_folder"][i]):
                    os.makedirs(prms["tag_count_list_folder"][i], exist_ok=True)
                else:
                    prms["tag_count_list_folder"][i] = prms["batch_folder"][i] + '/' + prms["tag_count_list_folder"][i]
                    os.makedirs(prms["tag_count_list_folder"][i], exist_ok=True)

        get_all_tag_counter_from_path = {}
        get_cat_tag_counter_from_path = {}
        for batch_num, path in enumerate(prms["tag_count_list_folder"]):
            if path not in get_all_tag_counter_from_path:
                get_all_tag_counter_from_path[path] = {}
                get_cat_tag_counter_from_path[path] = {i: {} for i in range(9)}
        prms["get_all_tag_counter_from_path"] = get_all_tag_counter_from_path
        prms["get_cat_tag_counter_from_path"] = get_cat_tag_counter_from_path

        self.check_valid_param(prms["min_short_side"], 'min_short_side', None, int)
        for s in prms["min_short_side"]:
            if -1 < s < 256:
                raise ValueError(f'min_short_side of {s} is too short')

        for i, ext in enumerate(prms["img_ext"]):
            if ext not in ('.png', '.jpg', 'png', 'jpg', 'same_as_original'):
                raise ValueError(f"Invalid img_ext value: {ext} Use '.png', '.jpg', 'png', 'jpg', 'same_as_original' only")
            if ext[0] != '.':
                prms["img_ext"][i] = '.' + prms["img_ext"][i]

        self.check_valid_param(prms["delete_original"], 'delete_original', (True, False))
        self.check_valid_param(prms["resized_img_folder"], 'resized_img_folder', None, str)

        for i in range(batch_count):
            prms["resized_img_folder"][i] = prms["resized_img_folder"][i].strip('/') + '/'
            if os.path.isabs(prms["resized_img_folder"][i]):
                os.makedirs(prms["resized_img_folder"][i], exist_ok=True)
            else:
                prms["resized_img_folder"][i] = prms["batch_folder"][i] + '/' + prms["resized_img_folder"][i]
                os.makedirs(prms["resized_img_folder"][i], exist_ok=True)

        self.check_valid_param(prms["method_tag_files"], 'method_tag_files', ('relocate', 'copy'))

        for i, do_include_tag_file in enumerate(prms["include_tag_file"]):
            if do_include_tag_file is False:
                prms["method_tag_files"][i] = 'skip'


    def check_tag_query(self, prms, e621_tags_set):
        tags = ','.join(prms["required_tags"]).replace(' ', '')
        tags = set(re.split(',|\|', tags))
        if '' in tags:
            tags.remove('')
        asterisks = []
        no_asterisks = []
        for tag in tags:
            if '*' in tag:
                asterisks.append(tag)
            else:
                no_asterisks.append(tag)
        if no_asterisks:
            for tag in no_asterisks:
                if tag not in e621_tags_set:
                    raise ValueError(f'required tag "{tag}" is not an e621 tag.')
        if asterisks:
            for tag in asterisks:
                pattern = r'(^|\s)(' + re.escape(tag).replace(r'\*', r'\S*') + r')($|\s)'
                for e621_tag in e621_tags_set:
                    if re.match(pattern, e621_tag) is not None:
                        break
                else:
                    raise ValueError(f'required tag "{tag}" is not found in any e621 tag.')

        tags = ','.join(prms["blacklist"]).replace(' ', '')
        tags = set(re.split(',|\|', tags))
        if '' in tags:
            tags.remove('')
        asterisks = []
        no_asterisks = []
        for tag in tags:
            if '*' in tag:
                asterisks.append(tag)
            else:
                no_asterisks.append(tag)
        if no_asterisks:
            for tag in no_asterisks:
                if tag not in e621_tags_set:
                    raise ValueError(f'blacklist tag "{tag}" is not an e621 tag.')
        if asterisks:
            for tag in asterisks:
                pattern = r'(^|\s)(' + re.escape(tag).replace(r'\*', r'\S*') + r')($|\s)'
                for e621_tag in e621_tags_set:
                    if re.match(pattern, e621_tag) is not None:
                        break
                else:
                    raise ValueError(f'blacklist tag "{tag}" is not found in any e621 tag.')


    def get_db(self, base_folder, posts_csv='', tags_csv='', e621_posts_list_filename='', e621_tags_list_filename='',
               keep_db=False, proxy_url: str | None = None):
        proxies = {'http': proxy_url, 'https': proxy_url} if proxy_url else None
        if all((posts_csv == '', e621_posts_list_filename == '')) or all((tags_csv == '', e621_tags_list_filename == '')):
            with requests.get('https://e621.net/db_export/', proxies=proxies) as response:
                response.raise_for_status()
                contents = response.text

            pattern = r"posts\S*?\.gz"
            matches = []
            for line in contents.split("\n"):
                match = re.search(pattern, line)
                if match:
                    matches.append(match.group())
            posts_filename = matches[-1]

            pattern = r"tags\S*?\.gz"
            matches = []
            for line in contents.split("\n"):
                match = re.search(pattern, line)
                if match:
                    matches.append(match.group())
            tags_filename = matches[-1]

        if posts_csv != '' and e621_posts_list_filename == '':
            e621_posts_list_filename = os.path.join(base_folder,f'{posts_csv[:-4]}.parquet')
        elif e621_posts_list_filename == '':
            e621_posts_list_filename = f'{base_folder}/{posts_filename[:-7]}.parquet'
        if not os.path.isfile(e621_posts_list_filename):

            if posts_csv == '':
                posts_csv = os.path.join(base_folder, posts_filename[:-3])
            if not os.path.isfile(posts_csv):
                posts_link = 'https://e621.net/db_export/' + posts_filename
                posts_file_path = os.path.join(base_folder, posts_filename)
                print(posts_file_path)
                if not os.path.isfile(posts_file_path):
                    with requests.get(posts_link, stream=True, proxies=proxies) as r:
                        total_length = int(r.headers.get("Content-Length"))

                        with tqdm.wrapattr(r.raw, "read", total=total_length, desc="") as raw:
                            with open(posts_file_path, 'wb') as output:
                                shutil.copyfileobj(raw, output)

                print('## Unpacking', posts_file_path, '...')
                with gzip.open(posts_file_path, 'rb') as f_in:
                    with open(posts_csv, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                if not keep_db:
                    os.remove(posts_file_path)

            print('## Optimizing posts list data, this will take a few minutes')
            pl.scan_csv(posts_csv).select(
                ['id', 'created_at', 'md5', 'source', 'rating', 'image_width', 'image_height', 'tag_string', 'fav_count',
                 'file_ext', 'is_deleted', 'score']).filter(pl.col('is_deleted') == 'f').collect().write_parquet(
                e621_posts_list_filename)
            if not keep_db:
                os.remove(posts_csv)

        if tags_csv != '' and e621_tags_list_filename == '':
            e621_tags_list_filename = os.path.join(base_folder, f'{tags_csv[:-4]}.parquet')
        elif e621_tags_list_filename == '':
            e621_tags_list_filename = f'{base_folder}/{tags_filename[:-7]}.parquet'
        if not os.path.isfile(e621_tags_list_filename):

            if tags_csv == '':
                tags_csv = f'{base_folder}/{tags_filename[:-3]}'
            if not os.path.isfile(tags_csv):
                tags_link = 'https://e621.net/db_export/' + tags_filename
                tags_file_path = os.path.join(base_folder, tags_filename)
                print(tags_file_path)
                if not os.path.isfile(tags_file_path):
                    with requests.get(tags_link, stream=True, proxies=proxies) as r:
                        total_length = int(r.headers.get("Content-Length"))

                        with tqdm.wrapattr(r.raw, "read", total=total_length, desc="") as raw:
                            with open(tags_file_path, 'wb') as output:
                                shutil.copyfileobj(raw, output)

                print('## Unpacking', tags_file_path, '...')
                with gzip.open(tags_file_path, 'rb') as f_in:
                    with open(tags_csv, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                if not keep_db:
                    os.remove(tags_file_path)

            print('## Optimizing tags list data, this will take a few seconds')
            pl.scan_csv(tags_csv).select(['name', 'category', 'post_count']).filter(pl.col('post_count') >= 1).drop(
                ['post_count']).collect().write_parquet(e621_tags_list_filename)
            if not keep_db:
                os.remove(tags_csv)

        rating_d = {
            'name': ['explicit', 'questionable', 'safe'],
            'category': [2, 2, 2]
        }

        df = pl.read_parquet(e621_tags_list_filename)

        rdf = pl.DataFrame(rating_d)
        df = pl.concat([df, rdf])

        tag_to_cat = dict(zip(df["name"].to_list(), df["category"].to_list()))
        e621_tags_set = set(df["name"].to_list())
        del df

        return e621_posts_list_filename, tag_to_cat, e621_tags_set


    def collect_posts(self, prms, batch_num, e621_posts_list_filename):
        print(f"## Collecting posts for batch {batch_num}")
        if self.cached_e621_posts is None:
            df = pl.read_parquet(e621_posts_list_filename)
        else:
            df = self.cached_e621_posts

        if prms["collect_from_listed_posts_file"][batch_num]:
            print(f'## Collecting listed posts in {prms["collect_from_listed_posts_file"][batch_num]}')
            with open(prms["collect_from_listed_posts_file"][batch_num], 'r') as f:
                collect_from_listed_posts = list(set([s.strip() for s in f]))
            df = df.filter(pl.col(prms["collect_from_listed_posts_type"][batch_num]).cast(pl.Utf8).is_in(collect_from_listed_posts))

        if prms["collect_from_listed_posts_file"][batch_num] and not prms["apply_filter_to_listed_posts"][batch_num]:
            num_rows = df.shape[0]
            if num_rows == 0:
                print(f'##\n## Collected 0 posts. Check your settings. Skipping batch {batch_num}\n##')
                return None
            else:
                print(f'##\n## Collected {num_rows} posts.\n##')

            posts_save_path = f'{prms["batch_folder"][batch_num]}/filtered_posts_{batch_num}.parquet'
            print(f'## Saving filtered e621 posts list for batch {batch_num} in {posts_save_path}')
            df.write_parquet(posts_save_path)

            if prms["save_searched_list_type"][batch_num] != 'None':
                prms["get_searched_list_from_path"][prms["save_searched_list_path"][batch_num]].update(
                    df[prms["save_searched_list_type"][batch_num]].to_list()
                )

            return posts_save_path

        if not prms["include_explicit"][batch_num]:
            df = df.filter(pl.col('rating') != 'e')
        if not prms["include_questionable"][batch_num]:
            df = df.filter(pl.col('rating') != 'q')
        if not prms["include_safe"][batch_num]:
            df = df.filter(pl.col('rating') != 's')

        print(f'## Removing posts with score < {prms["min_score"][batch_num]}')
        df = df.filter(pl.col('score') >= prms["min_score"][batch_num])

        if prms["min_fav_count"][batch_num] > 0 and 'fav_count' in df.columns:
            print(f'## Removing posts with favorite count < {prms["min_fav_count"][batch_num]}')
            df = df.filter(pl.col('fav_count') >= prms["min_fav_count"][batch_num])

        included_file_ext = set(['png' * prms["include_png"][batch_num], 'jpg' * prms["include_jpg"][batch_num],
                                 'gif' * prms["include_gif"][batch_num], 'webm' * prms["include_webm"][batch_num],
                                 'swf' * prms["include_swf"][batch_num]])
        if '' in included_file_ext:
            included_file_ext.remove('')
        included_file_ext = '|'.join(included_file_ext)
        if included_file_ext:
            df = df.filter(pl.col('file_ext').str.contains(included_file_ext))

        if prms["min_date"][batch_num] >= '2000' and 'created_at' in df.columns:
            print(f'## Removing posts before date {prms["min_date"][batch_num]}')
            df = df.filter(pl.col("created_at") > prms["min_date"][batch_num])

        if prms["skip_posts_file"][batch_num]:
            print(f'## Skipping listed posts in {prms["skip_posts_file"][batch_num]}')
            with open(prms["skip_posts_file"][batch_num], 'r') as f:
                skip_posts = list(set([s.strip() for s in f]))
            df = df.filter(~pl.col(prms["skip_posts_type"][batch_num]).cast(pl.Utf8).is_in(skip_posts))

        if prms["min_area"][batch_num] >= 65536 and 'image_width' in df.columns and 'image_height' in df.columns:
            print(f'## Removing posts with dimension area less than {prms["min_area"][batch_num]}px')
            df = df.filter(pl.col("image_width") * pl.col("image_height") >= prms["min_area"][batch_num])

        print("## Getting posts that have required tags")
        all_required_tags = []
        tag_groups = set([s.strip().lower() for s in prms["required_tags"][batch_num].split('|')])
        if '' in tag_groups:
            tag_groups.remove('')
        expr = None

        # send total to progressbar
        if self.backend_conn:
            self.backend_conn.send(len(tag_groups))

        for group in tag_groups:
            tags = set([s.strip() for s in group.split(',')])
            if '' in tags:
                tags.remove('')
            all_required_tags.append(tags)
            escaped_tags = [re.escape(word).replace(r'\*', r'\S*') for word in tags]
            sub_expr = None
            for tag in escaped_tags:
                pattern = r'(^|\s)(' + tag + r')($|\s)'
                if sub_expr is None:
                    sub_expr = pl.col('tag_string').str.contains(pattern)
                else:
                    sub_expr &= pl.col('tag_string').str.contains(pattern)
            if expr is None:
                expr = sub_expr
            else:
                expr |= sub_expr
            # send total to progressbar
            if self.backend_conn:
                self.backend_conn.send(1)
        if expr is not None:
            df = df.filter(expr)

        print('## Removing posts that have blacklisted tags')
        tag_groups = set([s.strip().lower() for s in prms["blacklist"][batch_num].split('|')])
        if '' in tag_groups:
            tag_groups.remove('')

        for group in tag_groups:
            tags = set([s.strip() for s in group.split(',')])
            if '' in tags:
                tags.remove('')
            if not any([tags <= subset for subset in all_required_tags]):
                escaped_tags = [re.escape(word).replace(r'\*', r'\S*') for word in tags]
                sub_expr = None
                for tag in escaped_tags:
                    pattern = r'(^|\s)(' + tag + r')($|\s)'
                    if sub_expr is None:
                        sub_expr = pl.col('tag_string').str.contains(pattern)
                    else:
                        sub_expr &= pl.col('tag_string').str.contains(pattern)
                if sub_expr is not None:
                    df = df.filter(~sub_expr)

        if prms["top_n"][batch_num] > 0:
            if prms["do_sort"][batch_num]:
                print(f'## Getting {prms["top_n"][batch_num]} highest scoring posts')
                top_n = prms["top_n"][batch_num]
                df = df.filter(pl.col('score') >= pl.col('score').top_k(top_n).last()).sort('score', descending=True).head(
                    top_n)
            else:
                print(f'## Getting {prms["top_n"][batch_num]} earliest posts')
                df = df.head(n=prms["top_n"][batch_num])

        num_rows = df.shape[0]
        if num_rows == 0:
            print(f'##\n## Collected 0 posts. Check your settings. Skipping batch {batch_num}\n##')
            return None
        else:
            print(f'##\n## Collected {num_rows} posts.\n##')

        posts_save_path = f'{prms["batch_folder"][batch_num]}/filtered_posts_{batch_num}.parquet'
        print(f'## Saving filtered e621 posts list for batch {batch_num} in {posts_save_path}')
        df.write_parquet(posts_save_path)

        if prms["save_searched_list_type"][batch_num] != 'None':
            prms["get_searched_list_from_path"][prms["save_searched_list_path"][batch_num]].update(
                df[prms["save_searched_list_type"][batch_num]].to_list()
            )

        return posts_save_path


    def create_searched_list(self, prms):
        for path in set(prms["save_searched_list_path"]):
            if path is not None:
                l = prms["get_searched_list_from_path"][path]
                if l:
                    save_list_type = prms["get_searched_list_type_from_path"][path]
                    print(f"## Saving a list of {save_list_type}s from the collected posts in {path}")
                    with open(path, 'w') as f:
                        f.write('\n'.join([str(s) for s in l]))


    def run_download(self,
                     to_download: Sequence[DownloadTask[str]],
                     dwn_log_path, err_log_path,
                     proxy_url: str | None = None,
                     ) -> set[str]:
        downloader = FilesDownloader(proxy_url=proxy_url, logs_paths=(dwn_log_path, err_log_path))
        finished = downloader.download_all(to_download)
        failed_md5 = {result.task.meta for result in finished if not result.ok}
        return failed_md5


    def download_posts(self, prms, batch_nums, posts_save_paths, tag_to_cat, base_folder='', batch_mode=False):
        _img_lists_df = pl.DataFrame()
        __df = pl.DataFrame()
        _md5_source = pl.DataFrame()
        failed_md5 = set()
        df_list_for_tag_files = []

        total_links = len(batch_nums)
        # send total to progressbar
        if self.backend_conn:
            self.backend_conn.send(total_links)

        for batch_num, posts_save_path in zip(batch_nums, posts_save_paths):
            df = pl.read_parquet(posts_save_path)

            length = df.shape[0]

            if prms["remove_tags_list"][batch_num] != '':
                with open(prms["remove_tags_list"][batch_num], 'r') as f:
                    remove_tags = set([s.strip() for s in f])
                    if '' in remove_tags:
                        remove_tags.remove('')
            else:
                remove_tags = set()

            replace_tags = prms["replace_tags"][batch_num]

            ext_directory = {'png': prms["png_folder"][batch_num], 'jpg': prms["jpg_folder"][batch_num],
                             'webm': prms["webm_folder"][batch_num], 'gif': prms["gif_folder"][batch_num],
                             'swf': prms["swf_folder"][batch_num]}

            base = pl.repeat('https://static1.e621.net/data/', n=length, eager=True)
            slash = pl.repeat('/', n=length, eager=True)
            dot = pl.repeat('.', n=length, eager=True)
            df = df.with_columns((base + df['md5'].str.slice(0, length=2) + slash + df['md5'].str.slice(2,
                                                                                                        length=2) + slash +
                                  df['md5'] + dot + df['file_ext']).alias("download_links"))

            df = df.join(pl.DataFrame({'directory': ext_directory.values(), 'key': ext_directory.keys()}),
                         left_on='file_ext', right_on='key', how='left')

            df = df.with_columns(df[prms["save_filename_type"][batch_num]].cast(str))
            df = df.with_columns((df[prms["save_filename_type"][batch_num]]).alias("filename_no_ext"))
            df = df.with_columns((df[prms["save_filename_type"][batch_num]] + dot + df['file_ext']).alias("filename"))
            df = df.with_columns(
                (df[prms["save_filename_type"][batch_num]] + pl.repeat('.txt', n=length, eager=True)).alias(
                    "tagfilebasename"))
            df = df.with_columns((df['directory'] + df['tagfilebasename']).alias("tagfilename"))

            if not prms["skip_post_download"][batch_num] and not prms["skip_resize"][batch_num]:
                img_df = df.select(['directory', 'filename_no_ext', 'filename', 'tagfilebasename', 'file_ext']).filter(
                    pl.col('file_ext').str.contains('png|jpg'))
                img_df = img_df.drop(['file_ext'])
                imgs_length = img_df.shape[0]
                img_df = pl.concat([pl.DataFrame(
                    [pl.repeat(prms["resized_img_folder"][batch_num], n=imgs_length, eager=True).alias(
                        'resized_img_folder'),
                     pl.repeat(prms["min_short_side"][batch_num], n=imgs_length, eager=True).alias('min_short_side'),
                     pl.repeat(prms["img_ext"][batch_num], n=imgs_length, eager=True).alias('img_ext'),
                     pl.repeat(prms["delete_original"][batch_num], n=imgs_length, eager=True).alias('delete_original'),
                     pl.repeat(prms["method_tag_files"][batch_num], n=imgs_length, eager=True).alias('method_tag_files')]),
                    img_df], how="horizontal")

                _img_lists_df = _img_lists_df.vstack(img_df)

            if not prms["skip_post_download"][batch_num]:
                _md5_source = _md5_source.vstack(
                    df.select(['id', 'md5', 'source', 'directory', 'filename_no_ext', 'filename']))

            if not prms["skip_post_download"][batch_num] and not batch_mode:
                posts_info = df.select(['download_links','directory','filename', 'md5']).to_dicts()
                to_download = [
                    DownloadTask(post['download_links'], Path(post['directory']) / post['filename'], post['md5'])
                    for post in posts_info
                ]

            elif not prms["skip_post_download"][batch_num]:
                __df = __df.vstack(df.select(['download_links', 'directory', 'filename']))
                __df = __df.unique(subset=['directory', 'filename'])
                posts_info = __df.select(['download_links','directory','filename', 'md5']).to_dicts()
                to_download = [
                    DownloadTask(post['download_links'], Path(post['directory']) / post['filename'], post['md5'])
                    for post in posts_info
                ]

            df_list_for_tag_files.append(
                df.drop(['download_links', 'directory', 'file_ext', 'filename']))

        if not batch_mode:
            print('## Downloading posts')
            failed_set = self.run_download(to_download,
                                      prms["batch_folder"][batch_num] + f'/download_log_{batch_num}.txt',
                                      prms["batch_folder"][batch_num] + f'/download_error_log_{batch_num}.txt',
                                      )
            if failed_set:
                print('## Some posts were downloaded unsuccessfully.')
                failed_md5.update(failed_set)

        elif __df.shape[0] > 0:
            length = len(to_download)
            print(f"##\n## Found {length} unique posts to save\n##")
            print('## Downloading posts')
            failed_set = self.run_download(to_download, base_folder + '/download_log.txt',
                                      base_folder + '/download_error_log.txt',
                                      )
            if failed_set:
                print('## Some posts were downloaded unsuccessfully.')
                failed_md5.update(failed_set)

        if failed_md5:
            print(f'## Retrying download for {len(failed_md5)} failed post downloads')
            redownload_posts = df.filter(pl.col('md5').str.contains('|'.join(failed_md5))).select(
                ['download_links', 'directory', 'filename', 'md5']).to_dicts()
            to_redownload = [
                DownloadTask(post['download_links'], Path(post['directory']) / post['filename'], post['md5'])
                for post in redownload_posts
            ]
            failed_set_part_2 = self.run_download(to_redownload, base_folder + '/redownload_log.txt',
                                             base_folder + '/redownload_error_log.txt',
                                             )
            failed_md5 = failed_md5 & failed_set_part_2

        validate_redownload = set()
        found_md5 = set()
        replace_from_img_list = []
        remove_from_img_list = []
        tagfiles_no_post = set()

        if failed_md5:
            print(f'## Attempting to redownload {len(failed_md5)} unavailable posts using alternative source(s)')
            assert to_download
            to_download = [task for task in to_download if task.meta in failed_md5]
            num_redownload = len(to_download)

            if num_redownload > 0:
                print(f'## Found {num_redownload} direct file links for redownloading.')
                if not batch_mode:
                    failed_set_part_3 = self.run_download(to_download,
                                                     prms["batch_folder"][batch_num] + f'/redownload_log_b_{batch_num}.txt',
                                                     prms["batch_folder"][
                                                         batch_num] + f'/redownload_error_log_b_{batch_num}.txt',
                                                     )
                else:
                    failed_set_part_3 = self.run_download(to_download,
                                                     base_folder + '/redownload_log_b.txt',
                                                     base_folder + '/redownload_error_log_b.txt',
                                                     )
                failed_md5 = (failed_md5 - found_md5) | failed_set_part_3
            else:
                print('## Found 0 direct file links for redownloading.')

            validated = {}
            if not batch_mode:
                duplicates_folder = prms["batch_folder"][batch_nums[0]] + '/duplicate_posts/'
            else:
                duplicates_folder = base_folder + '/duplicate_posts/'
            os.makedirs(duplicates_folder, exist_ok=True)
            for directory, filename_from_type, ext in validate_redownload:
                if os.path.isfile(directory + filename_from_type + ext):
                    if directory + filename_from_type not in validated:
                        validated[directory + filename_from_type] = ext
                        replace_from_img_list.append((directory, filename_from_type, filename_from_type + ext))
                    else:
                        if validated[directory + filename_from_type] != ext:
                            os.replace(directory + filename_from_type + ext, duplicates_folder + filename_from_type + ext)
            for directory, filename_from_type, ext in validate_redownload:
                if not os.path.isfile(directory + filename_from_type + ext) and (
                        directory + filename_from_type not in validated):
                    remove_from_img_list.append((directory, filename_from_type + ext))
                    tagfiles_no_post.add(filename_from_type + '.txt')

            if tagfiles_no_post:
                if not batch_mode:
                    tagfiles_no_post_folder = prms["batch_folder"][batch_nums[0]] + '/tag_files_no_post/'
                    ids_no_post_folder = prms["batch_folder"][batch_nums[0]] + '/'
                else:
                    tagfiles_no_post_folder = base_folder + '/tag_files_no_post/'
                    ids_no_post_folder = base_folder + '/'
                os.makedirs(tagfiles_no_post_folder, exist_ok=True)
                os.makedirs(ids_no_post_folder, exist_ok=True)

            if not prms["skip_resize"][batch_num] and replace_from_img_list:
                _img_lists_df = _img_lists_df.join(
                    pl.DataFrame(replace_from_img_list, schema=['directory', 'filename_no_ext', 'new_filename']),
                    on=['directory', 'filename_no_ext'],
                    how="left"
                ).with_columns(pl.col('new_filename').fill_null(pl.col('filename'))).drop(['filename']).rename(
                    {'new_filename': 'filename'})
            if not prms["skip_resize"][batch_num] and remove_from_img_list:
                _img_lists_df = _img_lists_df.join(
                    pl.DataFrame(remove_from_img_list, schema=['directory', 'filename'], orient='row'),
                    on=['directory', 'filename'],
                    how="anti"
                )

            _failed_df = df.filter(pl.col('md5').str.contains('|'.join(failed_md5))).select(['id', 'md5', 'source'])

            if tagfiles_no_post:
                with open(ids_no_post_folder + 'failed_download_posts_alt_source_list.txt', 'w', encoding="utf-8") as f:
                    for _id, md5, source in zip(_failed_df["id"].to_list(), _failed_df["md5"].to_list(),
                                                _failed_df["source"].to_list()):
                        f.write(f'id:{_id}\nmd5:{md5}\nsource:[ {source} ]\n')

        # send total to progressbar
        if self.backend_conn:
            self.backend_conn.send(1)

        for batch_num, df in zip(batch_nums, df_list_for_tag_files):

            length = df.shape[0]

            rating_tags = {}
            if prms["include_explicit_tag"][batch_num]:
                rating_tags['e'] = 'explicit'
            if prms["include_questionable_tag"][batch_num]:
                rating_tags['q'] = 'questionable'
            if prms["include_safe_tag"][batch_num]:
                rating_tags['s'] = 'safe'

            path = prms["tag_count_list_folder"][batch_num]
            all_tag_count = prms["get_all_tag_counter_from_path"][path]
            category_ctr = prms["get_cat_tag_counter_from_path"][path]
            selected_cats = prms["selected_cats"][batch_num]
            reorder_tags = prms["reorder_tags"][batch_num]
            tag_sep = prms["tag_sep"][batch_num]
            prepend_tags = [s.strip() for s in prms["prepend_tags"][batch_num].split(tag_sep)]
            prepend_tags = [s for s in prepend_tags if s != '']
            append_tags = [s.strip() for s in prms["append_tags"][batch_num].split(tag_sep)]
            append_tags = [s for s in append_tags if s != '']
            replace_underscores = prms["replace_underscores"][batch_num]
            remove_parentheses = prms["remove_parentheses"][batch_num]

            rating_lst = df['rating'].to_list()
            tag_string_lst = df['tag_string'].to_list()
            tagfilebasename_lst = df['tagfilebasename'].to_list()
            tagfilename_lst = df['tagfilename'].to_list()

            tag_date_list = df['created_at'].to_list()

            if prms["include_tag_file"][batch_num]:
                for idx in range(length):
                    print(f'\r## Saving tag files for batch {batch_num}: {idx + 1}/{length}', end='')
                    if tagfilename_lst[idx] in self.processed_tag_files:
                        continue
                    dont_count = False
                    if tagfilebasename_lst[idx] in tagfiles_no_post:
                        dont_count = True

                    rating = rating_lst[idx]
                    if rating in rating_tags:
                        tags = [rating_tags[rating]] + tag_string_lst[idx].split(' ')
                    else:
                        tags = tag_string_lst[idx].split(' ')

                    post_creation_date = tag_date_list[idx]
                    format_string = "%Y-%m-%d %H:%M:%S.%f"
                    parsed_datetime = datetime.strptime(post_creation_date, format_string)
                    if not parsed_datetime.year in tags:
                        print(f"ADDING YEAR TO FILE:\t{parsed_datetime.year}")
                        tags += [parsed_datetime.year]

                    segregate = {}
                    unsegregated = []
                    for tag in tags:
                        if tag not in remove_tags:
                            if tag in tag_to_cat:
                                category_num = tag_to_cat[tag]
                                if tag in replace_tags:
                                    tag = replace_tags[tag]
                                if category_num in selected_cats:
                                    if reorder_tags:
                                        if category_num in segregate:
                                            segregate[category_num].append(tag)
                                        else:
                                            segregate[category_num] = [tag]
                                    else:
                                        unsegregated.append(tag)
                                    if path and not dont_count:
                                        if tag in all_tag_count:
                                            all_tag_count[tag] += 1
                                        else:
                                            all_tag_count[tag] = 1
                                        if tag in category_ctr[category_num]:
                                            category_ctr[category_num][tag] += 1
                                        else:
                                            category_ctr[category_num][tag] = 1

                    if reorder_tags:
                        category_nums = [c for c in selected_cats if c in segregate]
                        updated_tags = []
                        for cat_num in category_nums:
                            updated_tags += segregate[cat_num]
                    else:
                        updated_tags = unsegregated
                    if prepend_tags:
                        updated_tags = [tag for tag in prepend_tags if tag not in updated_tags] + updated_tags
                    if append_tags:
                        updated_tags = updated_tags + [tag for tag in append_tags if tag not in updated_tags]
                    updated_tags = tag_sep.join(updated_tags)
                    if replace_underscores:
                        updated_tags = updated_tags.replace('_', ' ')
                    if remove_parentheses:
                        updated_tags = updated_tags.replace('(', '')
                        updated_tags = updated_tags.replace(')', '')

                    # ### DEBUG
                    # print(f"===================")
                    # print(f"\nDEBUG::\t\ttagfilename_lst:\t{tagfilename_lst}")
                    # print(f"\nDEBUG::\t\ttagfilename_lst[idx]:\t{tagfilename_lst[idx]}")
                    # print(f"===================")

                    if tagfilebasename_lst[idx] in tagfiles_no_post:
                        with open(tagfiles_no_post_folder + tagfilebasename_lst[idx], 'w', encoding="utf-8") as f:
                            f.write(updated_tags)
                    else:
                        with open(tagfilename_lst[idx], 'w', encoding="utf-8") as f:
                            f.write(updated_tags)

                    self.processed_tag_files.add(tagfilename_lst[idx])

                    if path and not dont_count:
                        if prepend_tags:
                            for tag in prepend_tags:
                                if tag in all_tag_count:
                                    all_tag_count[tag] += 1
                                else:
                                    all_tag_count[tag] = 1
                        if append_tags:
                            for tag in append_tags:
                                if tag in all_tag_count:
                                    all_tag_count[tag] += 1
                                else:
                                    all_tag_count[tag] = 1
                print('')

        if not prms["skip_resize"][batch_num] and 'directory' in _img_lists_df.columns:
            _img_lists_df = _img_lists_df.unique(subset=['directory', 'filename_no_ext'])
        return _img_lists_df


    def create_tag_count(self, prms):
        cat_to_num = {'general': 0, 'artist': 1, 'rating': 2, 'copyright': 3, 'character': 4, 'species': 5, 'invalid': 6, 'meta': 7, 'lore': 8}
        for path in set(prms["tag_count_list_folder"]):
            empty = True
            if path not in ('', '/'):
                all_tag_count = prms["get_all_tag_counter_from_path"][path]
                category_ctr = prms["get_cat_tag_counter_from_path"][path]
                categories = set([item for sublist in prms["tag_order"] for item in sublist])
                for category in categories:
                    cat_list = list(category_ctr[cat_to_num[category]].items())
                    if cat_list:
                        empty = False
                        cat_df = pl.DataFrame(cat_list, schema=[category, 'count'])
                        cat_df = cat_df.sort(by=['count', category], descending=[True, False])
                        cat_df.write_csv(path + category + '.csv', has_header=True)
                all_tags_list = list(all_tag_count.items())
                if all_tags_list:
                    empty = False
                    all_tags_df = pl.DataFrame(all_tags_list, schema=['tag', 'count'])
                    all_tags_df = all_tags_df.sort(by=['count', 'tag'], descending=[True, False])
                    all_tags_df.write_csv(path + 'tags.csv', has_header=True)

                if not empty:
                    print(f'## Tag count CSVs {path} done!')


    def init_counter(self):
        self.counter = multiprocessing.Manager().Value(c_int, 0)


    def increment(self, counter, counter_lock, length):
        with counter_lock:
            counter.value += 1
            print(f'\r## Resizing Images: {counter.value}/{length} ', end='')


    def parallel_resize(self, counter, counter_lock, imgs_folder, img_file, img_ext, min_short_side, num_images, failed_images,
                        delete_original, resized_img_folder):

        # send total to progressbar
        if self.backend_conn:
            self.backend_conn.send(num_images)

        resized_img_folder = imgs_folder if (delete_original or resized_img_folder == '') else resized_img_folder
        if (img_ext == 'same_as_original') or (os.path.splitext(img_file)[1] == img_ext):
            resized_filename = resized_img_folder + img_file
        else:
            resized_filename = resized_img_folder + os.path.splitext(img_file)[0] + img_ext

        if resized_img_folder != imgs_folder and os.path.isfile(resized_filename):
            self.increment(counter, counter_lock, num_images)
            return

        try:
            image = cv2.imread(imgs_folder + img_file, cv2.IMREAD_COLOR)
            height, width = image.shape[:2]
        except Exception:
            failed_images.append(imgs_folder + img_file)
            self.increment(counter, counter_lock, num_images)
            return

        img_short_side = min(width, height)
        resized = False
        if (img_short_side > min_short_side) and (min_short_side > 1):
            if width == img_short_side:
                new_width = min_short_side
                new_height = int(height * min_short_side / width)
            else:
                new_width = int(width * min_short_side / height)
                new_height = min_short_side
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            resized = True

        if delete_original:
            if os.path.isfile(resized_filename) and resized:  # same ext -> overwrite
                cv2.imwrite(resized_filename, image)
            elif resized:  # different ext -> delete
                os.remove(imgs_folder + img_file)
                cv2.imwrite(resized_filename, image)
        else:
            if resized_img_folder != imgs_folder:  # different folder
                cv2.imwrite(resized_filename, image)
            else:  # same folder -> rename original image
                os.replace(imgs_folder + img_file, imgs_folder + '_' + img_file)
                cv2.imwrite(resized_filename, image)

        self.increment(self.counter, self.counter_lock, num_images)



    def resize_imgs(self, prms, batch_num, num_cpu, img_folders, img_files, tag_files):
        min_short_side = prms["min_short_side"][batch_num]
        img_ext = prms["img_ext"][batch_num]
        delete_original = prms["delete_original"][batch_num]
        resized_img_folder = prms["resized_img_folder"][batch_num]
        method = prms["method_tag_files"][batch_num]

        self.init_counter()

        length = len(img_files)
        # send total to progressbar
        if self.backend_conn:
            self.backend_conn.send(length)

        multiprocessing.freeze_support()
        with multiprocessing.Pool(num_cpu) as pool:
            pool.starmap(self.parallel_resize,
                         zip(repeat(self.counter), repeat(self.counter_lock), img_folders, img_files, repeat(img_ext),
                             repeat(min_short_side), repeat(len(img_files)), repeat(self.failed_images), repeat(delete_original),
                             repeat(resized_img_folder)))
        print('')

        for i, img_folder, tag_file in zip(range(1, length + 1), img_folders, tag_files):
            if (not delete_original) and (resized_img_folder != img_folder):
                if method == 'relocate':
                    print(f'\r## Relocating tag files {i}/{length}', end='')
                    os.replace(img_folder + tag_file, resized_img_folder + tag_file)
                elif method == 'copy':
                    print(f'\r## Copying tag files {i}/{length}', end='')
                    shutil.copyfile(img_folder + tag_file, resized_img_folder + tag_file)
        print('')


    def resize_imgs_batch(self, num_cpu, img_folders, img_files, resized_img_folders, min_short_side, img_ext, delete_original,
                          tag_files, method_tag_files):
        self.init_counter()

        length = len(img_files)
        # send total to progressbar
        if self.backend_conn:
            self.backend_conn.send(length)

        multiprocessing.freeze_support()
        with multiprocessing.Pool(num_cpu) as pool:
            pool.starmap(self.parallel_resize,
                         zip(repeat(self.counter), repeat(self.counter_lock), img_folders, img_files, img_ext, min_short_side,
                             repeat(length), repeat(self.failed_images), delete_original, resized_img_folders))
        print('')

        for i, img_fol, res_fol, delete, tag_file, method in zip(range(1, length + 1), img_folders, resized_img_folders,
                                                                 delete_original, tag_files, method_tag_files):
            if (not delete) and (res_fol != img_fol):
                if method == 'relocate':
                    print(f'\r## Relocating tag files {i}/{length}', end='')
                    os.replace(img_fol + tag_file, res_fol + tag_file)
                elif method == 'copy':
                    print(f'\r## Copying tag files {i}/{length}', end='')
                    shutil.copyfile(img_fol + tag_file, res_fol + tag_file)
        print('')

    def close_PIPE(self):
        if self.backend_conn:
            self.backend_conn.close()

    def __init__(self, basefolder, settings, numcpu, phaseperbatch, postscsv, tagscsv, postsparquet, tagsparquet, keepdb, cachepostsdb, backend_conn):
        self.basefolder = basefolder
        self.settings = settings
        self.numcpu = numcpu
        self.phaseperbatch = phaseperbatch
        self.postscsv = postscsv
        self.tagscsv = tagscsv
        self.postsparquet = postsparquet
        self.tagsparquet = tagsparquet
        self.keepdb = keepdb
        self.cachepostsdb = cachepostsdb

        print("============================")
        print(f"postscsv\t{postscsv}")
        print(f"tagscsv\t{tagscsv}")
        print(f"postsparquet\t{postsparquet}")
        print(f"tagsparquet\t{tagsparquet}")
        print("============================")

        self.backend_conn = backend_conn

        self.failed_images = None
        self.counter = None
        self.counter_lock = None
        self.processed_tag_files = None
        self.cached_e621_posts = None

        base_folder = os.path.dirname(os.path.abspath(__file__))
        if self.basefolder != '':
            base_folder = self.basefolder
            base_folder = self.removeslash(base_folder)
            os.makedirs(base_folder, exist_ok=True)

        with open(self.settings, 'r') as json_file:
            prms = json.load(json_file)

        if self.postscsv != '':
            if not self.postscsv.endswith('.csv'):
                raise ValueError('Invalid postscsv file type.')
            if not os.path.isfile(self.postscsv):
                raise ValueError(self.postscsv, 'not found.')
        if self.tagscsv != '':
            if not self.tagscsv.endswith('.csv'):
                raise ValueError('Invalid tagscsv file type.')
            if not os.path.isfile(self.tagscsv):
                raise ValueError(self.tagscsv, 'not found.')
        if self.postsparquet != '':
            if not self.postsparquet.endswith('.parquet'):
                raise ValueError('Invalid postsparquet file type.')
            if not os.path.isfile(self.postsparquet):
                raise ValueError(self.postsparquet, 'not found.')
        if self.tagsparquet != '':
            if not self.tagsparquet.endswith('.parquet'):
                raise ValueError('Invalid tagsparquet file type.')
            if not os.path.isfile(self.tagsparquet):
                raise ValueError(self.tagsparquet, 'not found.')

        max_cpu = multiprocessing.cpu_count()
        num_cpu = max_cpu if (self.numcpu > max_cpu) or (self.numcpu < 1) else self.numcpu

        print('## Checking number of batches validity')
        batch_count = self.check_param_batch_count(prms)

        self.normalize_params(prms, batch_count)

        print('## Checking settings validity')
        self.prep_params(prms, batch_count, base_folder)

        print('## Checking required files')
        e621_posts_list_filename, tag_to_cat, e621_tags_set = self.get_db(base_folder, self.postscsv, self.tagscsv,
                                                                     self.postsparquet, self.tagsparquet, self.keepdb)

        self.cached_e621_posts = None
        if self.cachepostsdb:
            self.cached_e621_posts = pl.read_parquet(e621_posts_list_filename)

        print('## Checking tag search query')
        self.check_tag_query(prms, e621_tags_set)
        del e621_tags_set

        self.processed_tag_files = set()

        manager = multiprocessing.Manager()
        self.failed_images = manager.list()
        self.counter = manager.Value(c_int, 0)
        self.counter_lock = manager.Lock()

        session_start_time = time.time()
        if self.phaseperbatch:
            for batch_num in range(batch_count):
                print(f"#### Batch {batch_num} ####")
                posts_save_path = self.collect_posts(prms, batch_num, e621_posts_list_filename)
                if posts_save_path is not None:
                    start_time = time.time()
                    image_list_df = self.download_posts(prms, [batch_num], [posts_save_path], tag_to_cat, base_folder)
                    elapsed = time.time() - start_time
                    print(
                        f'## Batch {batch_num} download elapsed time: {elapsed // 60:02.0f}:{elapsed % 60:02.0f}.{f"{elapsed % 1:.2f}"[2:]}')
                    if not prms["skip_resize"][batch_num] and (image_list_df.shape[0] > 0):
                        start_time = time.time()
                        self.resize_imgs(prms, batch_num, num_cpu, image_list_df["directory"].to_list(),
                                    image_list_df["filename"].to_list(), image_list_df["tagfilebasename"].to_list())
                        elapsed = time.time() - start_time
                        print(
                            f'## Batch {batch_num} resize elapsed time: {elapsed // 60:02.0f}:{elapsed % 60:02.0f}.{f"{elapsed % 1:.2f}"[2:]}')
            self.create_searched_list(prms)
            self.create_tag_count(prms)
        else:
            posts_save_paths = [self.collect_posts(prms, batch_num, e621_posts_list_filename) for batch_num in
                                range(batch_count)]
            self.create_searched_list(prms)
            posts_save_paths = [p for p in posts_save_paths if p]
            if posts_save_paths:
                start_time = time.time()
                image_list_df = self.download_posts(prms, list(range(batch_count)), posts_save_paths, tag_to_cat, base_folder,
                                               batch_mode=True)
                elapsed = time.time() - start_time
                print(
                    f'## Batch download elapsed time: {elapsed // 60:02.0f}:{elapsed % 60:02.0f}.{f"{elapsed % 1:.2f}"[2:]}')
                self.create_tag_count(prms)
                if image_list_df.shape[0] > 0:
                    start_time = time.time()
                    self.resize_imgs_batch(num_cpu,
                                      image_list_df["directory"].to_list(),
                                      image_list_df["filename"].to_list(),
                                      image_list_df["resized_img_folder"].to_list(),
                                      image_list_df["min_short_side"].to_list(),
                                      image_list_df["img_ext"].to_list(),
                                      image_list_df["delete_original"].to_list(),
                                      image_list_df["tagfilebasename"].to_list(),
                                      image_list_df["method_tag_files"].to_list())
                    elapsed = time.time() - start_time
                    print(
                        f'## Batch resize elapsed time: {elapsed // 60:02.0f}:{elapsed % 60:02.0f}.{f"{elapsed % 1:.2f}"[2:]}')

        if self.failed_images:
            print(f'## Failed to resize {len(self.failed_images)} images')
            with open(f'{base_folder}/self.failed_images.txt', 'w') as f:
                f.write('\n'.join(self.failed_images))

        print('## Done!')
        elapsed = time.time() - session_start_time
        print(f'## Total session elapsed time: {elapsed // 60:02.0f}:{elapsed % 60:02.0f}.{f"{elapsed % 1:.2f}"[2:]}')
        print('#################################################################')

        self.close_PIPE()

        del self.cached_e621_posts
