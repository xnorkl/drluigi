#!/usr/bin/env python

from bs4 import BeautifulSoup
from exiftool import ExifToolHelper
from pyfiglet import Figlet
from random import randint
import argparse
import json
import io
import mimetypes
import os
import re
import requests
import shutil

# Configs
BANNER = "Dr. Luigi"
INJMETHODS = ['comment', 'disclaimer', 'idat', 'raw']
EXTENSIONS = ['.jpg', '.png', '.gif', '.tif', '.pdf', '.raw']
IMAGEDIR = "./images"

# Command Line Args
parser = argparse.ArgumentParser(description='')

parser.add_argument(
    '-q', '--query',
    help='Search for an image using Google.'
)

parser.add_argument(
    '-p', '--payload',
    help='Payload to be injected'
)

parser.add_argument(
    '-m', '--method',
    const='comment',
    nargs='?',
    choices=INJMETHODS,
    help='Select an injection method.'
)

args = parser.parse_args()


class Image(object):

    def __init__(self, filepath=None, exifdata=None, **kwargs):
        self.filepath = filepath
        self.exifdata = exifdata


class WebScraper(object): 
    
    def __init__(self, query=None, header=None, language=None, location=None, search_engine=None, results=None):
        self.query = str(query)
        self.header = dict(header)
        self.language = 'en' if language is None else str(language)
        self.location = 'us' if location is None else str(location)
        self.search_engine = 'Google Search' if search_engine is None else str(search_engine)
        self.results = results

    
    def _set_directory(self, dir):
        abspath = os.path.abspath(dir)
        if os.path.isdir(abspath):
            self.directory = abspath
        else:
            os.makedirs(abspath, exist_ok=False)
            self._set_directory(dir)
        

    def _search_url(self):

        #     
        query = "+".join(self.query.split())
        base_url = f"https://www.google.com/search?"
        params = {
            "hl" : "en",
            "gl" : "us",
            "btnG" : "Google Search",
            "tbm" : "isch",
            "no_cache" : "true",
            "num" : "10"
        }
        
        return url


    def _image_search(self, url):
        """ A query string and adds src URLs from the results page. """

        # Construct URL query
        url = f"https://www.google.com/search?hl=jp&q={query}&btnG=Google+Search*tbs=0&safe=off&tbm=isch"
    
        # Return HTML object as string.
        header = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, header)
        html = str(BeautifulSoup(response.content, features="lxml"))
    
        # Filter URL results
        pattern = r"src=\"(https://[a-zA-Z0-9-.?=&;:/]+)\""    
        return re.findall(pattern, html)


    def _download_img(self, urls):
        """ Download random image from image URLs """
        
        # Get range of array and return random element in that range.
        random = lambda l: l[randint(0,(len(l) - 1))]

        # Stream image url
        res = requests.get(random(urls), stream = True)

        # Get possible extensions using mimetypes 
        content_type = res.headers.get('Content-Type')
        exts = mimetypes.guess_all_extensions(content_type, strict=False)
        
        # Get preferred ext based on EXTENSIONS config.
        ext = [e for e in exts if e in EXTENSIONS][0]
        
        # Write to filepath.
        name = self.query.split(".")[0]  # try to drop extenstion if included in query
        self.filepath = f"{self.directory}/{name}{ext}"

        if res.status_code == 200:
            with open(self.filepath, 'wb') as f:
                shutil.copyfileobj(res.raw, f)
        
        
        
    def get_random_image(self, query, header):
        """ Accepts an image query and filename. 
            Downloads a random image result to ./images directory. 
        """     
        self._set_query(query)
        self._set_header(header)
        self._set_directory(IMAGEDIR)
        urls = self._image_search()
        self._download_img(urls)

        
class Image:


    def __init__(self):
        self.filepath = None
        self.injection_method = None
        self.data = None
        self.bytes = None


    def _set_filepath(self, filepath):

        if os.path.isfile(filepath):
            self.filepath = filepath
        else:
            print(f"{filepath} doesn not exist! Aborting...")
            exit()
    
    
    def _load_exif_data(self):            
        with ExifToolHelper() as et:
            self.data = et.get_metadata(self.filepath)[0]

    
    def _inject_comment(self, payload):
        with ExifToolHelper() as et:
            et.set_tags(self.filepath, tags={"comment": payload})


    def _inject_disclaimer(self, payload):
        with ExifToolHelper() as et:
            et.set_tags(self.filepath, tags={"disclaimer": payload}) 


    def _inject_raw(self, payload, offset=14):
        """ Inject raw bytes into file starting at offset.
            Default offset is 14 to preserver magic bytes for most image formats.
        """
        pbytes = payload.encode()
        start = offset
        end = start + len(pbytes)

        with open(self.filepath, 'rb') as f:
            bstream = f.read()
        
        buff = io.BytesIO(bstream)
        view = buff.getbuffer()
        view[start:end] = pbytes

        with open(self.filepath, 'wb') as f:
            f.write(buff.getvalue())        


    def _set_injection_method(self, method, i=0):
        """ Recursively check if method is valid.
            If it is, set injection_method attribute. 
        """
        if i >= len(INJMETHODS):
            print(f"Error: Unknown injection method {method}. Aborting...")
            exit()

        if method == INJMETHODS[i]:
            self.injection_method = f"_inject_{method}"
        else:
            self._set_injection_method(method, i+1)
        

#  Control functions
def download(query, header=None):
    """ Accepts a query and a filename"""
    scraper = WebScraper()
    scraper.get_random_image(query, header)
    return scraper.filepath


def inject(filename, payload, method):
    """ Accepts a filename, payload, and method.
        Injects the payload into image file based on the selected method.
    """
    image = Image()
    image._set_filepath(filename)
    image._set_injection_method(method)        
    image._load_exif_data()

    # Call by reference. 
    getattr(image, image.injection_method)(payload)
    
    print(json.dumps(image.__dict__))


if __name__ == "__main__":

    f = Figlet(font='slant')
    print(f.renderText(BANNER))

    query = args.query
    payload = args.payload 
    if args.method:
        method = args.method
    else:
        method = 'comment'

    image = download(query)
    inject(image, payload, method)