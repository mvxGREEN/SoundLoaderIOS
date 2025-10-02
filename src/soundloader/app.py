"""
A Cloud-to-MP3 Downloader for IOS
"""

import toga
import asyncio
import queue
import re
import random
import sys
import os
import requests
import json
from io import BytesIO
from pathlib import Path
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, LEFT, CENTER, RIGHT
from toga.validators import MinLength, StartsWith, Contains
import ctypes
from ctypes import c_void_p
from ctypes.util import find_library
from ctypes import cdll, CDLL, util, c_int64, c_int32, c_uint32, Structure, byref, POINTER
import rubicon.objc as objc
from rubicon.objc import ObjCClass, ObjCBlock, Block, objc_method, ObjCInstance, objc_const, SEL
from rubicon.objc.api import NSObject, Protocol, py_from_ns
from rubicon.objc.runtime import send_message
from rubicon.objc.api import *
from rubicon.objc import *
from rubicon.objc.runtime import *


# init objc libraries
cdll.LoadLibrary(util.find_library('AVFoundation'))
cdll.LoadLibrary(util.find_library('Foundation'))
cdll.LoadLibrary(util.find_library('Photos'))

# create objc class objects
NSURL = ObjCClass('NSURL')
NSURLRequest = ObjCClass('NSURLRequest')
NSURLSession = ObjCClass('NSURLSession')
NSString = ObjCClass('NSString')
NSError = ObjCClass('NSError')
NSArray = ObjCClass('NSArray')
NSData = ObjCClass('NSData')
UIPasteboard = ObjCClass('UIPasteboard')
AVAsset = ObjCClass('AVAsset')
AVURLAsset = ObjCClass('AVURLAsset')
AVMutableComposition = ObjCClass('AVMutableComposition')
AVAssetExportSession = ObjCClass('AVAssetExportSession')
AVAssetTrack = ObjCClass('AVAssetTrack')

WKWebView = ObjCClass('WKWebView')
WKNavigationDelegate = Protocol('WKNavigationDelegate')
WKWebViewConfiguration = ObjCClass('WKWebViewConfiguration')


# get filepath to destination directory
def get_dest_dir_path():
    # check OS
    if sys.platform == 'ios':
        print("Running on IOS")
        return os.path.join(os.path.expanduser('~'), 'Documents') + "/"
    elif sys.platform == 'win32':
        print("Running on Windows.")
        return "¯\\_(ツ)_/¯"
    elif sys.platform == 'android':
        print("Running on Android.")
        return "/storage/emulated/0/Documents/"
    elif sys.platform == 'darwin':
        print("Running on macOS.")
        return str(Path.home() / "Downloads") + "/"
    else:
        print(f"Running on a different platform: {sys.platform}\nReturning default path_out (windows)")
        return "¯\\_(ツ)_/¯"


# get filepath to ffmpeg
def get_bundled_ffmpeg_path():
    if platform.system() == 'Darwin':
        return os.path.join(os.path.dirname(__file__), 'ffmpeg')
    return get_ffmpeg_path()  # Use default path for other systems


# remove sensitive characters from filename
def sanitize_filename(filename):
    """Removes or replaces sensitive characters from a filename.

    Args:
        filename (str): The filename to sanitize.

    Returns:
        str: The sanitized filename.
    """

    # 1. Remove or replace characters that are invalid across platforms
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)

    # 2. Remove or replace characters that might cause issues with specific OS
    filename = filename.replace(' ', '_')  # replace spaces
    filename = filename.strip('. ')  # Remove leading/trailing spaces and dots

    # 3. Remove potentially problematic characters
    filename = re.sub(r'[,;!@#\$%^&()+]', '', filename)

    # 4. Normalize Unicode characters
    filename = filename.encode('ascii', 'ignore').decode('ascii')

    return filename


# start loading audio file(s) asynchronously
async def load_audio(audio_url):
    # TODO implement loading processes
    print("starting load_audio")


# start downloading audio file(s) asynchronously
async def download_audio(audio_url, out, filename):
    # TODO implement downloading processes
    print("starting download_audio")


# concat chunk files into completed MP3 file
def concat_chunk_files(file_paths, output_path):
    if not file_paths:
        print("error: no files provided to concat")
        return

    # init combined audio with first file
    try:
        combined_audio = AudioSegment.from_mp3(file_paths[0])
    except Exception as e:
        print(f"error loading first mp3 file: file_paths[0]={file_paths[0]}, exception={e}")
        return

    # loop through remaining chunk files and append them
    for chunk_file in file_paths[1:]:
        try:
            next_audio = AudioSegment.from_mp3(chunk_file)
            combined_audio += next_audio
            print(f"successfully appended: {os.path.basename(chunk_file)}")
        except Exception as e:
            print(f"error appending file: mp3_file={chunk_file}. Details: {e}")
            # TODO decide whether to exit or continue after error
            continue

    # try exporting combined audio to MP3 file
    try:
        # export() handles the encoding via ffmpeg
        combined_audio.export(output_path, format="mp3")
        print(f"\nconcatenation complete: output_path={output_path}")
    except Exception as e:
        print(f"error exporting combined mp3: exception={e}")


class WebViewDelegate(NSObject, metaclass=ObjCDelegate):
    # Store intercepted URLs and the HTML result
    intercepted_urls = []
    html_content = None

    # --- URL Interception ---
    @objc_method
    def webView_decidePolicyForNavigationAction_decisionHandler_(
            self,
            webView,
            navigationAction,
            decisionHandler
    ):
        # Get the URL of the request
        request = navigationAction.request
        url = request.URL.absoluteString

        # Store the URL
        print(f"Intercepted URL: {url}")
        self.intercepted_urls.append(str(url))

        # Allow the request to proceed (WKNavigationActionPolicyAllow = 1)
        # decisionHandler(1)
        # decisionHandler is a Block. We need to call it with the appropriate value.
        # Note: In pure Objective-C, WKNavigationActionPolicyAllow is an enum value.
        # You may need to verify the correct integer value for 'Allow' (which is 1)
        decisionHandler(1)

        # --- HTML Extraction ---

    @objc_method
    def webView_didFinishNavigation_(self, webView, navigation):
        print("Page finished loading. Extracting HTML...")

        # JavaScript code to get the entire page's HTML
        js_get_html = "document.documentElement.outerHTML"

        # Evaluate JavaScript in the web view
        # The result comes back via a completion handler block
        def completion_handler(html_string, error):
            if error:
                print(f"Error extracting HTML: {error}")
            elif html_string:
                # Store the extracted HTML as a Python string
                self.html_content = str(html_string)
                print(f"HTML extracted (Length: {len(self.html_content)})")

            # This is where you would typically signal that the process is complete
            # to prevent the Python script from exiting prematurely.
            # E.g., setting a condition variable or stopping a run loop.
            # For simplicity here, we rely on the final output.

        # The evaluateJavaScript_completionHandler_ method expects a Block for the handler
        Block(completion_handler)(js_get_html)


# request json from url
def request_json(url_string, callback):
    # create nsstring object of url
    url = NSURL.URLWithString(url_string)

    # 2. Get the shared NSURLSession
    session = NSURLSession.sharedSession

    # 3. Define the completion handler block
    # The block takes (NSData, NSURLResponse, NSError)
    @Block
    def completion_handler(data, response, error):
        json_string = None
        error_string = None

        if error:
            # An error occurred (e.g., network failure)
            error_string = str(error.description)
        elif data:
            # Data was received, convert it to a Python string
            # Use NSUTF8StringEncoding (4)
            data_string = NSString.alloc().initWithData(data, encoding=4)
            if data_string:
                json_string = str(data_string)
            else:
                error_string = "Could not decode data as UTF-8 string."
        else:
            # This case might happen with a valid response but no data (e.g., 204 No Content)
            error_string = "No data received."

        # Call the Python callback function with the result
        callback(json_string, error_string)

    # 4. Create and start the data task
    task = session.dataTaskWithURL(url, completionHandler=completion_handler)

    # All tasks start in a suspended state, you must call resume()
    task.resume()


def handle_json_response(json_string, error_string):
    """
    The function to be called when the network request completes.
    This will typically run on a background thread from the NSURLSession.
    """
    if error_string:
        print(f"Error fetching data: {error_string}")
        return

    print("--- JSON Response (as String) ---")
    print(json_string)

    # You can now parse the string into a Python object if needed
    try:
        data_dict = json.loads(json_string)
        print("\n--- Parsed JSON Key Example ---")
        # Assuming the response is a dictionary and has a 'title' key for example
        # print(f"Title: {data_dict.get('title', 'N/A')}")
        print(f"Type of parsed data: {type(data_dict)}")
    except json.JSONDecodeError as e:
        print(f"\nError parsing JSON string: {e}")


def load_url_in_webview(target_url):
    # 1. Create the configuration
    config = WKWebViewConfiguration.alloc().init()

    # 2. Create the web view
    frame = (0, 0, 500, 500)  # Simple arbitrary frame (x, y, width, height)
    webview = WKWebView.alloc().initWithFrame_configuration_(frame, config)

    # 3. Create and set the delegate
    delegate = WebViewDelegate.alloc().init()
    # WKWebView is an ObjCInstance, so its property setters are available
    webview.navigationDelegate = delegate

    # 4. Load the URL
    url_obj = NSURL.URLWithString(target_url)
    request_obj = NSURLRequest.requestWithURL(url_obj)
    webview.loadRequest(request_obj)

    # 5. Keep the webview and delegate alive while waiting for content
    # In a full iOS app context (like BeeWare), the main app loop handles this.
    # In a standalone script, you'd need a mechanism to keep the thread alive
    # until the HTML is extracted (e.g., a run loop or a sleep loop).

    # Example for demonstration (you'd need a robust loop in a real app):
    import time
    print("Loading web page...")
    start_time = time.time()
    while delegate.html_content is None and (time.time() - start_time) < 15:
        time.sleep(0.5)
        # Note: In a real rubicon-objc application, you would need to ensure
        # that the main thread's run loop is active for delegate calls to work.

    # 6. Return the results
    return {
        'urls': delegate.intercepted_urls,
        'html': delegate.html_content
    }


class SoundLoader(toga.App):
    # startup
    def startup(self):
        # register fonts
        toga.Font.register("FiraSans", "resources/FiraSans-Regular.ttf")
        toga.Font.register("FiraSansExtraLight", "resources/FiraSans-ExtraLight.ttf")
        toga.Font.register("FiraSansBold", "resources/FiraSans-Bold.ttf")

        # set path to ffmpeg
        os.environ["FFMPEG_PATH"] = get_bundled_ffmpeg_path()

        # update ui
        self.show_init_layout()

        # request permissions

    def show_init_layout(self):
        # main_box
        self.main_box = toga.Box(direction=COLUMN)

        # hint_box
        hint_label = toga.Label(
            "Paste URL:",
            font_family="FiraSans",
            margin=(8, 8, 4, 8),
        )
        self.hint_box = toga.Box(children=[hint_label])
        self.main_box.add(self.hint_box)

        # url_box
        self.url_input = toga.TextInput(direction=ROW,
                                        on_confirm=self.load_input,
                                        on_change=self.input_change,
                                        flex=1,
                                        validators=[StartsWith("https://", error_message="Please paste a valid URL",
                                                               allow_empty=True),
                                                    MinLength(15, error_message="Please paste a valid URL",
                                                              allow_empty=True),
                                                    ])
        self.load_button = toga.Button(
            "Paste",
            direction=ROW,
            on_press=self.load_input,
            margin=(0, 0, 0, 4),
        )
        self.load_button.style.visibility = 'visible'
        self.url_box = toga.Box(margin=(0, 8))
        self.url_box.add(self.url_input)
        self.url_box.add(self.load_button)
        self.main_box.add(self.url_box)

        # preview_box
        self.preview_box = toga.Box(direction=COLUMN)
        self.main_box.add(self.preview_box)

        # image_box
        self.image_view = toga.ImageView(image=None, height=320, direction=COLUMN, flex=1)
        self.image_box = toga.Box(children=[self.image_view], direction=COLUMN, margin=8)
        self.preview_box.add(self.image_box)

        # filename_box
        self.filename_input_label = toga.Label(
            "Filename:",
            font_family="FiraSans",
            margin=(12, 4, 8, 12)
        )
        self.filename_input = toga.TextInput(margin=(8, 12, 8, 4), direction=ROW, flex=1)
        filename_box = toga.Box(direction=ROW)
        filename_box.add(self.filename_input_label)
        filename_box.add(self.filename_input)
        self.preview_box.add(filename_box)

        # download_box
        self.download_button = toga.Button(
            "Download",
            on_press=self.download_input,
            margin=8,
        )
        download_box = toga.Box(children=[self.download_button], direction=COLUMN)
        self.preview_box.add(download_box)

        # progress_box
        self.progress = toga.ProgressBar(max=None, direction=ROW, flex=1)
        self.progress.style.visibility = 'hidden'
        progress_box = toga.Box(children=[self.progress], direction=COLUMN)
        self.preview_box.add(progress_box)
        self.image_view.style.visibility = 'hidden'
        self.filename_input_label.style.visibility = 'hidden'
        self.filename_input.style.visibility = 'hidden'
        self.download_button.style.visibility = 'hidden'

        # main_window
        self.main_window = toga.MainWindow(title="SoundLoader")
        self.main_window.content = self.main_box
        self.main_window.show()

    def show_loading_layout(self):
        # set load_button to loading
        self.load_button.text = "Loading…"

        # set download_button to download
        self.download_button.text = "Download"

        # disable clickable widgets
        self.url_input.enabled = False
        self.filename_input.enabled = False
        self.load_button.enabled = False
        self.download_button.enabled = False

        # hide preview widgets
        self.image_view.style.visibility = 'hidden'
        self.filename_input_label.style.visibility = 'hidden'
        self.filename_input.style.visibility = 'hidden'
        self.download_button.style.visibility = 'hidden'

        # show indeterminate progress
        self.progress.max = None
        self.progress.style.visibility = 'visible'
        self.progress.start()

    def show_preview_layout(self, filename, thumbnail_url):
        try:
            # try load thumbnail into image_view
            response = requests.get(thumbnail_url)
            response.raise_for_status()  # Raise an exception for bad status codes
            image_bytes = BytesIO(response.content)
            toga_image = toga.Image(src=image_bytes.read())
            self.image_view.image = toga_image
        except requests.exceptions.RequestException as e:
            print(f"Error loading thumbnail_url into image_view:\nthumbnail_url={thumbnail_url}\nRequestException={e}")
            # TODO gracefully handle errors loading thumbnail
        finally:
            # set load_button to clear
            self.load_button.text = "Clear"

            # enable clickable widgets
            self.url_input.enabled = True
            self.filename_input.enabled = True
            self.load_button.enabled = True
            self.download_button.enabled = True

            # set filename_input to current filename
            self.filename_input.value = filename

            # show preview widgets
            self.image_view.style.visibility = 'visible'
            self.filename_input_label.style.visibility = 'visible'
            self.filename_input.style.visibility = 'visible'
            self.download_button.style.visibility = 'visible'

            # stop progress animation
            self.progress.stop()

    async def show_downloading_layout(self):
        # set download_button to downloading
        self.download_button.text = "Downloading…"

        # disable clickable widgets
        self.load_button.enabled = False
        self.download_button.enabled = False
        self.url_input.enabled = False
        self.filename_input.enabled = False

        # start progress animation
        self.progress.style.visibility = 'visible'
        self.progress.start()

    async def show_finished_layout(self):
        # set download_button to finished
        self.download_button.text = "Finished!"

        # stop progress bar
        self.progress.stop()
        self.progress.max = 100
        self.progress.value = 100

        # enable (some) clickable widgets
        self.url_input.enabled = True
        self.load_button.enabled = True

    # listen for textual changes to url_input
    def input_change(self, widget):
        if self.url_input.value == "":
            print("url_input cleared")

            # set load_button to paste
            self.load_button.text = "Paste"

            # reset progress
            self.progress.value = 0
            self.progress.max = None

            # hide preview widgets
            self.image_view.style.visibility = 'hidden'
            self.filename_input_label.style.visibility = 'hidden'
            self.filename_input.style.visibility = 'hidden'
            self.download_button.style.visibility = 'hidden'
        elif "https://" in self.url_input.value and self.url_input.value.count("/") >= 3:
            # set load_button to load
            self.load_button.text = "Load"
        else:
            # set load_button to clear
            self.load_button.text = "Clear"

    # paste copied text from pasteboard into url_input
    def paste_action(self):
        print("paste_action")
        # Get the general pasteboard instance
        pasteboard = UIPasteboard.generalPasteboard

        # Get the string content from the pasteboard
        pasted_text = pasteboard.string

        # Check if there is any text to paste
        if pasted_text:
            # Set the value of the TextInput to the pasted text
            self.url_input.value = pasted_text

    # clear text from url_input
    def clear_action(self):
        print("clear_action")
        self.url_input.value = ""

    # start running load processes
    async def load_input(self, widget):
        # hide keyboard
        self.app.main_window.content = self.app.main_window.content

        # clear textinput and return on 'clear' btn click
        if self.load_button.text == "Clear":
            self.clear_action()
            return

        # paste if text input is empty
        if not self.url_input.value:
            self.paste_action()

        # validate input
        if "https://" in self.url_input.value and self.url_input.value.count("/") >= 3:
            # show loading ui
            self.show_loading_layout()

            # await load audio task
            load_task = asyncio.create_task(
                load_audio(f"{self.url_input.value}"))
            info = await load_task

            # format file info
            filename_id = f"{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}_"
            index_div1 = info.index("|||")
            index_div2 = info.rindex("|||")
            title = info[:index_div1]
            filename = filename_id + sanitize_filename(title[0:23])
            ext = info[index_div1 + 3:index_div2]
            thumbnail_url = info[index_div2 + 3:]
            print(f"loaded audio info:\ntitle={title}\nfilename={filename}\next={ext}\nthumbnail_url={thumbnail_url}")

            # convert webp thumbnail to jpg
            if thumbnail_url.endswith(".webp"):
                thumbnail_url = thumbnail_url.replace("vi_webp", "vi")
                thumbnail_url = thumbnail_url.replace(".webp", ".jpg")

            self.show_preview_layout(filename, thumbnail_url)
        # else:
        # TODO show error message on invalid input

    # start running download processes
    async def download_input(self, widget):
        # hide keyboard
        self.app.main_window.content = self.app.main_window.content

        # update ui
        await self.show_downloading_layout()

        # start downloading audio
        dl_a_task = asyncio.create_task(
            download_audio(f"{self.url_input.value}",
                           get_dest_dir_path(),
                           f"{self.filename_input.value}"))
        await dl_a_task
        print(f"finished video download!")

        # TODO start download audio task
        # dl_a_task = asyncio.create_task(
        #    dl_audio_async(f"{self.url_input.value}",
        #                   get_dest_path(),
        #                   f"{self.filename_input.value}",
        #                   "1080",
        #                   phook))
        # await dl_a_task
        # print(f"finished audio download!")

        # TODO get chunk filepaths
        # file_path_chunks = get_dest_path() + f"{self.filename_input.value}"
        file_path_dest = get_dest_dir_path() + f"{self.filename_input.value}" + ".mp3"
        print(
            f"file_path_dest={file_path_dest}")

        # TODO concat chunk files
        # av_concat(file_path_video, file_path_audio, file_path_output)

        await self.show_finished_layout()
        print("finished showing finished layout!")

    # get html as string from webpage at URL
    def get_html_from_url(url_string):
        # 1. Create an NSURL object from the Python string
        url = NSURL.URLWithString(url_string)

        if url is None:
            return f"Error: Could not create NSURL from '{url_string}'"

        # 2. Create an NSError object placeholder (required by the method signature)
        error = NSError.alloc().initWithDomain("", code=0, userInfo=None)

        # 3. Use NSString's class method to get the content
        # We use NSUTF8StringEncoding for the encoding, which is a common value.
        html_content_objc = NSString.stringWithContentsOfURL(
            url,
            encoding=NSStringEncoding.NSUTF8StringEncoding,
            error=error.ptr  # Pass a pointer to the error object
        )

        if html_content_objc is not None:
            # The Objective-C NSString is automatically bridged to a Python str
            return str(html_content_objc)
        else:
            # If loading fails, the error object might contain details
            error_details = str(error.description) if error.description else "Unknown error"
            return f"Error loading content: {error_details}"

    def load_url_in_webview(target_url):
        # create configuration
        config = WKWebViewConfiguration.alloc().init()

        # create webview
        frame = (0, 0, 500, 500)  # Simple arbitrary frame (x, y, width, height)
        webview = WKWebView.alloc().initWithFrame_configuration_(frame, config)

        # create delegate, set as navigationdelegate for webview
        delegate = WebViewDelegate.alloc().init()
        # WKWebView is an ObjCInstance, so its property setters are available
        webview.navigationDelegate = delegate

        # load url
        url_obj = NSURL.URLWithString(target_url)
        request_obj = NSURLRequest.requestWithURL(url_obj)
        webview.loadRequest(request_obj)

        import time
        print("Loading web page...")
        start_time = time.time()
        while delegate.html_content is None and (time.time() - start_time) < 15:
            time.sleep(0.5)
            # TODO ensure that the main thread's run loop is active for delegate calls to work

        # return intercepted urls
        return {
            'urls': delegate.intercepted_urls,
            'html': delegate.html_content
        }

def main():
    return SoundLoader()
