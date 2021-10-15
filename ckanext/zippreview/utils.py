import struct
import re
import zipfile
import os
import logging

from io import BytesIO
from collections import OrderedDict
from urllib.parse import urlparse

import requests

from ckan.lib import uploader, formatters
log = logging.getLogger(__name__)

ALLOWED_FMTS = ('zip', 'application/zip', 'application/x-zip-compressed')


def get_zip_list(rsc):
    if rsc.get('url_type') == 'upload':
        upload = uploader.ResourceUpload(rsc)
        value = None
        try:
            zf = zipfile.ZipFile(upload.get_path(rsc['id']), 'r')
            value = zf.filelist
        except Exception:
            # Sometimes values that can't be converted to ints can sneak
            # into the db. In this case, just leave them as they are.
            pass

        if value:
            return value

        upload = uploader.get_resource_uploader(rsc)
        url = urlparse(rsc['url'])
        filename = os.path.basename(url.path)
        
        URL = upload.get_url_from_filename(rsc['id'], filename, '')
        return get_ziplist_from_url(URL)
    else:
        return get_ziplist_from_url(rsc.get('url'))
    return


def get_ziplist_from_url(url):
    try:
        head = requests.head(url)
        if 'content-length' in head.headers:
            end = int(head.headers['content-length'])

        if 'content-range' in head.headers:
            end = int(head.headers['content-range'].split("/")[1])
        return _get_list(url, end-65536, end)
    except Exception:
        pass

    try:
        return _get_list_advanced(url)
    except Exception:
        return


def _get_list(url, start, end):
    resp = requests.get(
        url, headers={'Range': 'bytes={}-{}'.format(start, end)})
    fp = BytesIO(resp.content)
    return zipfile.ZipFile(fp).filelist


def _get_list_advanced(url):
    # https://superuser.com/questions/981301/is-there-a-way-to-download-parts-of-the-content-of-a-zip-file

    offset = 0
    fp = _open_remote_zip(url)
    header = fp.read(30)
    file_list = []

    while header[:4] == 'PK\x03\x04':
        compressed_len, uncompressed_len = struct.unpack('<II', header[18:26])
        filename_len, extra_len = struct.unpack('<HH', header[26:30])
        header_len = 30 + filename_len + extra_len
        total_len = header_len + compressed_len
        filename = fp.read(filename_len)

        zi = zipfile.ZipInfo(filename)
        zi.file_size = uncompressed_len
        file_list.append(zi)
        fp.close()

        offset += total_len
        fp = _open_remote_zip(url, offset)
        header = fp.read(30)

    fp.close()
    return file_list


def _open_remote_zip(url, offset=0):
    return requests.get(url, headers={'Range': 'bytes={}-'.format(offset)})


def get_zip_tree(rsc):    
    zip_list = get_zip_list(rsc)
    if not zip_list:
        return

    tree = OrderedDict()
    for compressed_file in zip_list:
        if "/" not in compressed_file.filename:
            tree[compressed_file.filename] = _prepare_file_data(
                compressed_file)
        else:
            parts = compressed_file.filename.split("/")
            if parts[-1] != "":
                child = _prepare_child_data(compressed_file)
                parent_filename = '/'.join(parts[:-1])

                if parent_filename not in tree:
                    tree[parent_filename] = _prepare_parent_data(
                        parent_filename)

                tree[parent_filename]['children'].append(child)

    return tree.values()


def _prepare_file_data(zip_info):
    return {
        "title": zip_info.filename,
        "file_size": formatters.localised_filesize(zip_info.file_size),
        "children": [],
        "icon": _get_file_icon(zip_info.filename)
    }


def _prepare_child_data(zip_info):
    file_title = zip_info.filename.split("/").pop()
    return {
        "title": re.sub(r'[^\x00-\x7f]', r'', file_title),
        "file_size": formatters.localised_filesize(zip_info.file_size),
        "children": [],
        "icon": _get_file_icon(re.sub(r'[^\x00-\x7f]', r'', zip_info.filename))
    }


def _prepare_parent_data(file_name):
    return {
        "title": file_name,
        "children": [],
        "icon": 'folder-open'
    }


def _get_file_icon(item):
    """returns icon class based on file format"""
    extension = item.split('.')[-1].lower()
    if extension in ['xml', 'txt', 'json']:
        return "file-text"
    if extension in ['csv', 'xls']:
        return "bar-chart-o"
    if extension in ['shp', 'geojson', 'kml', 'kmz']:
        return "globe"
    return "file"


def is_resource_supported(res):
    """Check if resource format is in allowed formats"""
    res_fmt = res.get('format', '').lower()

    if not res_fmt:
        splitted_url = os.path.splitext(res['url'])
        res_fmt = splitted_url[1][1:].lower()

    return True if res_fmt in ALLOWED_FMTS else False
