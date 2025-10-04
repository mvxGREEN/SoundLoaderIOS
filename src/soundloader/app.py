"""
A Cloud-to-MP3 Downloader for IOS
"""

import toga
from pathlib import Path
import asyncio
import aiohttp
from aiohttp import ClientConnectorError
import httpx
import shutil
import re
import random
import sys
import os
import requests
import json
from io import BytesIO
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, LEFT, CENTER, RIGHT
from toga.validators import MinLength, StartsWith, Contains

# global constants
TWITTER_PLAYER = "twitter:player"
TWITTER_TITLE = "twitter:title"
STREAM_URL_BEGIN = "https://api-v2.soundcloud.com/media/soundcloud:tracks:"
STREAM_URL_END = "/stream/hls"
BASE_URL_THUMBNAIL = "i1.sndcdn.com/a"
STREAM_ID_BEGIN = "media/soundcloud:tracks:"
STREAM_ID_END = "/stream"
FLAG_CLIENT_ID = "client_id:u?"

# global variables
player_url = ""
client_id = ""
stream_url = ""
full_stream_url = ""
playlist_url = ""
chunk_urls = [""]
track_filename = ""
thumbnail_filename = ""
thumbnail_url = ""
track_title = ""
track_artist = ""


# TODO uncomment
# from rubicon.objc import ObjCClass

# expose objc TODO uncomment
# UIPasteboard = ObjCClass('UIPasteboard')


# get path to destination directory
def get_dest_path():
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


# remove prohibited characters from filename
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


# delete directory and all its files and subfolders
def delete_directory_recursively(directory_path):
    print(f"delete_recursively: directory_path={directory_path}")

    # check if dir exists
    if not os.path.exists(directory_path):
        print(f"Error: Directory '{directory_path}' does not exist.")
        return

    try:
        # The core function for recursive deletion
        shutil.rmtree(directory_path)
        print(f"Directory '{directory_path}' and all contents deleted successfully.")
    except PermissionError:
        print(f"Error: Permission denied. Cannot delete directory '{directory_path}'.")
    except Exception as e:
        # Catch any other unexpected I/O errors
        print(f"An unexpected error occurred while deleting '{directory_path}': {e}")



# (2A) download playlist
async def download_m3u_file(url, save_path, filename) -> str:
    """
    Asynchronously downloads a file from a URL and saves it to the app's data folder.
    """
    try:
        response = await asyncio.to_thread(requests.get, url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # 2. Save the file content in chunks
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✅ Download complete. File saved to: {save_path}")

        return save_path

    except requests.exceptions.RequestException as e:
        error_message = f"Download failed: {e}"
        print(f"❌ {error_message}")
        return ""
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(f"❌ {error_message}")
        return ""


# (2B) parse m3u for chunk_urls
def parse_m3u_file(file_path) -> []:
    """
    Parses an M3U file at the given path and returns a list of all URLs.

    :param file_path: The full path to the M3U file in the iOS sandbox.
    :return: A list of strings, where each string is a media URL.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at path: {file_path}")
        return []

    urls = []
    try:
        # 'r' mode opens the file for reading in text mode.
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Remove leading/trailing whitespace and newline characters
                clean_line = line.strip()

                # Ignore comments/metadata lines (which start with '#')
                if clean_line and not clean_line.startswith('#'):
                    urls.append(clean_line)

    except Exception as e:
        # Handle potential file access or encoding errors
        print(f"Error reading or parsing M3U file: {e}")
        return []

    return urls


# (2C) download chunk
async def download_chunk(url: str, dir_path: Path, chunk_index: int) -> str:
    print(f"start download_chunk:\nurl={url}\ndir_path={dir_path}\nchunk_index={chunk_index}")
    try:
        # Use httpx.AsyncClient for asynchronous requests
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Use stream=True for large files
            async with client.stream("GET", url) as response:
                response.raise_for_status()  # Raise exception for bad status codes

                # Extract filename from the URL or Content-Disposition header
                # For simplicity, we use the last part of the URL path
                filename = "chunk" + str(chunk_index) + ".mp3"
                final_path = dir_path / filename

                # Write content to a local file in chunks
                with open(final_path, "wb") as file:
                    async for chunk in response.aiter_bytes():
                        file.write(chunk)

                return str(final_path)

    except httpx.RequestError as e:
        print(f"failed to download {url.split('/')[-1]}.\nrequest error: {e}")
        return ""
    except Exception as e:
        f"failed to download {url.split('/')[-1]}. unexpected error: {e}"
        return ""


# (2C) download thumbnail
async def download_art(url: str, save_path: Path) -> str:
    try:
        # Use httpx.AsyncClient for asynchronous requests
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Use stream=True for large files
            async with client.stream("GET", url) as response:
                response.raise_for_status()  # Raise exception for bad status codes

                # set thumbnail filename
                global thumbnail_filename
                final_path = save_path / thumbnail_filename

                # write content to a local file in chunks
                with open(final_path, "wb") as file:
                    async for chunk in response.aiter_bytes():
                        file.write(chunk)

                return str(final_path)
    except httpx.RequestError as e:
        return f"ERROR: Failed to download {url.split('/')[-1]}. Request error: {e}"
    except Exception as e:
        return f"ERROR: Failed to download {url.split('/')[-1]}. Unexpected error: {e}"


class SoundLoader(toga.App):
    # startup
    def startup(self):
        # register fonts
        toga.Font.register("FiraSans", "resources/FiraSans-Regular.ttf")
        toga.Font.register("FiraSansExtraLight", "resources/FiraSans-ExtraLight.ttf")
        toga.Font.register("FiraSansBold", "resources/FiraSans-Bold.ttf")

        # update ui
        self.show_init_layout()

    # get path to temp directory
    def get_temp_path(self):
        return Path(self.paths.cache) / 'temp'

    # create temp directory for temp files
    def create_temp_dir(self):
        docs_path = str(self.get_temp_path())
        try:
            os.mkdir(docs_path)
            print(f"Directory '{docs_path}' created successfully.")
        except FileExistsError:
            print(f"Directory '{docs_path}' already exists.")
        except FileNotFoundError:
            print(f"Parent directory for '{docs_path}' does not exist.")

    def show_init_layout(self):
        # main_box
        self.main_box = toga.Box(direction=COLUMN)

        # webview
        self.webview = toga.WebView(
            on_webview_load=self.on_page_loaded,
            style=Pack(flex=0)
        )
        self.webview.style.visibility = 'hidden'

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
                                        on_confirm=self.start_load_audio,
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
            on_press=self.start_load_audio,
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
            on_press=self.start_download_audio,
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

    # paste copied text into url_input TODO uncomment
    def paste_action(self):
        print("paste_action")
        # Get the general pasteboard instance
        # pasteboard = UIPasteboard.generalPasteboard

        # Get the string content from the pasteboard
        # pasted_text = pasteboard.string

        # Check if there is any text to paste
        # if pasted_text:
        # Set the value of the TextInput to the pasted text
        # self.url_input.value = pasted_text

    # clear text from url_input
    def clear_action(self):
        print("clear_action")
        self.url_input.value = ""

    # (1A) get html from url as string
    async def get_html_from(self, url: str) -> str:
        """
        Asynchronously fetches the HTML content of a given URL.

        Args:
            url: The URL of the webpage to fetch.

        Returns:
            The HTML content as a string, or None if an error occurs.
        """
        try:
            # Create an aiohttp ClientSession. It's recommended to use a context manager
            # (the 'async with' block) for the session to ensure resources are properly released.
            async with aiohttp.ClientSession() as session:
                # Send an asynchronous GET request to the URL.
                # The 'async with' block for the response ensures the connection is closed.
                # Raise an exception for bad status codes (4xx or 5xx)
                async with session.get(url) as response:
                    response.raise_for_status()

                    # Read the response content as text (HTML in this case).
                    html = await response.text()
                    print(f"received html response from: url={url}")
                    return html

        except ClientConnectorError as e:
            # Handle connection-related errors (e.g., DNS failure, connection refused)
            print(f"Connection Error for {url}: {e}")
            return ""
        except aiohttp.ClientResponseError as e:
            # Handle HTTP errors (e.g., 404 Not Found, 500 Server Error)
            print(f"HTTP Error for {url}: {e.status} {e.message}")
            return ""
        except Exception as e:
            # Handle any other unexpected exceptions
            print(f"An unexpected error occurred for {url}: {e}")
            return ""

    # (1B) parse html for player_url
    def extract_player_url(self, html) -> str:
        print(f"extract_player_url: len(html)={len(html)}")

        if TWITTER_PLAYER in html:
            print("found TWITTER_PLAYER in html")

            # extract player_url
            searchIndex = html.find(TWITTER_PLAYER) + len(TWITTER_PLAYER)
            startIndex = html.find("content", searchIndex) + 9
            endIndex = html.find('"', startIndex)
            return html[startIndex:endIndex]
        print(f"missing TWITTER_PLAYER in html:\nhtml={html}")
        return ""

    # (1C) load player_url in webview
    def load_in_webview(self, player_url):
        print(f"start load_in_webview: player_url={player_url}")
        self.webview.url = player_url

    # (1D) extract player_url from loaded webpage html
    async def on_page_loaded(self, widget):
        """
        A handler that is invoked when the WebView finishes loading the page.
        This is useful for updating other parts of the UI, like a status bar.
        """
        print(f"webview finished loading!")

        # get global var
        global player_url
        global stream_url
        global thumbnail_url
        global track_filename

        # get html via js
        html = ""
        js = "document.documentElement.outerHTML"
        try:
            html = await widget.evaluate_javascript(js)
        except Exception as e:
            print(f"An error occurred while running JavaScript: {e}")
        finally:
            if len(html) < 300:
                print(f"received html from JS: len(html)={len(html)}")

            else:
                # TODO show error message
                return

    # (1E) extract filename, thumbnail_url, metadata
    def extract_info(self, html) -> tuple[str, str, str, str]:
        print(f"extract_info: len(html)={len(html)}")

        # extract filename
        filename = "soundloader_download"
        if TWITTER_TITLE in html:
            searchIndex = html.find(TWITTER_TITLE)
            startIndex = html.find("content", searchIndex) + 9
            endIndex = html.find('"', startIndex)
            filename = html[startIndex:endIndex]
            print(f"found TWITTER_TITLE in html: filename={filename}")
        else:
            print(f"missing TWITTER_TITLE in html: filename={filename}")

        # extract thumbnail url
        t_url = ""
        if BASE_URL_THUMBNAIL in html:
            startIndex = html.find(BASE_URL_THUMBNAIL)
            endIndex = html.find('"', startIndex)
            t_url = "https://" + html[startIndex:endIndex]
            print(f"found BASE_URL_THUMBNAIL in html: t_url={t_url}")
        else:
            print(f"missing BASE_URL_THUMBNAIL in html: t_url={t_url}")

        # get meta
        meta = ""
        if "<h1" in html and "<meta" in html:
            start = html.find("<h1")
            end = html.find("<meta", start)
            meta = html[start:end]
        else:
            print("html missing meta!")

        # get track title and artist
        tt = filename  # default title
        ta = ""
        if "<a" in meta:
            search = meta.find("<a")
            start = meta.find(">", search)
            end = meta.find("</a", start)
            tt = meta[start:end]
            print(f"found track title: tt={tt}")
            search = meta.rfind("<a")
            start = meta.find(">", search)
            end = meta.find("</a", start)
            ta = meta[start:end]
            print(f"found track artist: ta={ta}")
        return filename, t_url, tt, ta

    # (1F) get client_id
    async def get_client_id_from(self, js_url) -> str:
        try:
            # execute js request
            response = await self.loop.run_in_executor(
                None,
                lambda: requests.get(js_url, timeout=10)
            )

            # check for success
            response.raise_for_status()

            # get js as string
            js_content = response.text

            # extract client_id
            if 'client_id=' in js_content:
                start = js_content.find('client_id=') + 10
                end = js_content.find('"', start)
                c_id = js_content[start:end]
                print(f"found client_id! c_id={c_id}")
                return c_id
            return ""

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            # TODO show error message
            return ""

        except Exception as e:
            # TODO show error message
            print(f"Unexpected Error: {e}")
            return ""

    # (1G) request json w/ response handler
    async def get_json_as_string(self, url: str) -> str:
        """
        Asynchronously fetches JSON data from a URL and returns it as a string.
        """
        print(f"start get_json_as_string: url={url}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)

                # raise an exception for bad status codes (4xx or 5xx)
                response.raise_for_status()

                # get the response content as a string
                json_string = response.text

                return json_string

        except httpx.HTTPStatusError as e:
            # Handle HTTP errors (e.g., 404 Not Found, 500 Server Error)
            return f"HTTP Error: {e.response.status_code} - {e.response.reason_phrase}"
        except httpx.RequestError as e:
            # Handle general request errors (e.g., connection timeout, DNS error)
            return f"Request Error: An error occurred while requesting {e.request.url} - {e.__class__.__name__}"
        except Exception as e:
            # Handle other unexpected errors
            return f"An unexpected error occurred: {e}"

    async def fetch_playlist_url(self, url) -> str:
        """
        Background task to await the fetch and update the UI.
        """
        global playlist_url
        json_str = await self.get_json_as_string(url)
        print("finished request json")

        # get playlist_url from json
        if "https://" in json_str:
            start = json_str.find("https://")
            end = json_str.find('"', start)
            playlist_url = json_str[start:end]
            print(f"found playlist_url={playlist_url}")
        else:
            print(f"missing playlist_url in json_str={json_str}")
        return playlist_url

    # on load click
    async def start_load_audio(self, widget):
        print("load button clicked (start_load_audio)")
        global player_url
        global stream_url
        global track_filename
        global thumbnail_filename
        global thumbnail_url
        global track_title
        global track_artist

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

            # await player_url
            input_url = self.url_input.value
            html = await self.get_html_from(input_url)
            print(f"finished get_html_from: len(html)={len(html)}")

            # extract player url
            player_url = self.extract_player_url(html)
            print(f"found player_url={player_url}")

            # extract last stream url
            if STREAM_ID_BEGIN in html and STREAM_ID_END in html:
                start = html.rfind(STREAM_ID_BEGIN) + len(STREAM_ID_BEGIN)
                end = html.rfind(STREAM_ID_END)
                stream_url = STREAM_URL_BEGIN + html[start:end] + STREAM_URL_END
                print(f"stream_url={stream_url}")
            else:
                # TODO show error message
                print(f"missing stream id in: player_url={player_url}")

            # load player in webiew
            # self.load_in_webview(player_url)

            # extract thumbnail, filename and metadata
            res = self.extract_info(html)
            track_filename = res[0]
            thumbnail_url = res[1]
            track_title = res[2]
            track_artist = res[3]
            print(f"audio info:\ntrack_filename={track_filename}"
                  f"\nthumbnail_url={thumbnail_url}\ntrack_title={track_title}\ntrack_artist={track_artist}")

            # sanitize filename
            track_filename = sanitize_filename(track_filename)

            # set thumbnail resolution
            if "-large" in thumbnail_url:
                print("changed resolution of thumbnail_url to t500x500")
                thumbnail_url.replace("-large", "-t500x500")
            else:
                print(f"kept resolution of thumbnail_url")

            # set thumbnail filename
            if thumbnail_url.endswith(".jpg"):
                # handle jpg
                thumbnail_filename = track_filename + ".jpg"
            elif thumbnail_url.endswith(".webp"):
                # convert webp to jpg
                thumbnail_filename = track_filename + ".jpg"
                thumbnail_url = thumbnail_url.replace("vi_webp", "vi")
                thumbnail_url = thumbnail_url.replace(".webp", ".jpg")
            elif thumbnail_url.endswith(".png"):
                # handle png
                thumbnail_filename = track_filename + ".png"
            else:
                # handle unexpected file extension
                thumbnail_filename = track_filename + thumbnail_url[thumbnail_url.rfind('.')]
                print(f"unexpected file extension: thumbnail_url={thumbnail_url}")
            print(f"thumbnail_filename={thumbnail_filename}")

            # get client id
            global client_id
            client_id = await self.get_client_id_from("https://a-v2.sndcdn.com/assets/0-2e3ca6a5.js")
            print(f"client_id={client_id}")

            # build full stream url
            global full_stream_url
            full_stream_url = stream_url + "?client_id=" + client_id  # + "&app_version=1759307428&app_locale=en"
            print(f"full_stream_url={full_stream_url}")

            # get playlist url
            global playlist_url
            playlist_url = await self.fetch_playlist_url(full_stream_url)
            print(f"playlist_url={playlist_url}")

            # update ui
            self.show_preview_layout(track_filename, thumbnail_filename)

    # ------------------- DOWNLOAD -------------------
    async def start_download_audio(self, widget):
        print("download button clicked (start_download_audio)")

        # hide keyboard
        self.app.main_window.content = self.app.main_window.content

        # update ui
        await self.show_downloading_layout()

        # start downloading audio
        dl_a_task = asyncio.create_task(
            self.download_audio(f"{self.url_input.value}",
                                get_dest_path(),
                                f"{self.filename_input.value}"))
        await dl_a_task
        print(f"finished download_audio task")

        # get path to saved file
        file_path_dest = get_dest_path() + f"{self.filename_input.value}" + ".mp3"
        print(f"file_path_dest={file_path_dest}")

        # update ui
        await self.show_finished_layout()
        print("finished showing finished layout!")

    # TODO (2) asynchronously download audio
    async def download_audio(self, p_url, dest_path, filename):
        print(f"start download_audio:\np_url={p_url}, dest_path={dest_path}, filename={filename}")

        global chunk_urls
        global thumbnail_filename
        global thumbnail_url

        # download playlist
        playlist_path = await download_m3u_file(p_url, self.get_temp_path(), filename)
        print(f"finished playlist download: playlist_path={playlist_path}")

        # parse playlist for chunk_urls
        chunk_urls = parse_m3u_file(playlist_path)
        print(f"finished parsing m3u: len(chunk_urls)={chunk_urls}")

        # make an array of download chunk tasks
        download_tasks = [
            download_chunk(url, self.get_temp_path(), chunk_index=i)
            for i, url in enumerate(chunk_urls)
        ]

        # use asyncio.gather to run all tasks concurrently
        results = await asyncio.gather(*download_tasks)
        print(f"finished downloading chunks to: len(chunk_urls)={len(chunk_urls)}")

        # download thumbnail
        await download_art(thumbnail_url, self.get_temp_path())
        print(f"finished downloading thumbnail to: str(paths.data)={str(self.get_temp_path())}")

        # concat chunks w/ thumbnail and tags
        complete_filepath = await self.concat_chunk_files(str(self.get_temp_path()), get_dest_path())
        print(f"finished concat mp3 files: complete_filepath={complete_filepath}")

    # (2D) concat chunks into mp3
    async def concat_chunk_files(self, chunk_dir_path, dest_filepath) -> str:
        print(f"start concat_chunk_files: chunk_dir_path={chunk_dir_path}, dest_filepath={dest_filepath}")

        # check if chunk0 exists
        chunk0_path = chunk_dir_path + "chunk0.mp3"
        if os.path.isfile(chunk0_path):
            print(f"file exists at chunk0_path={chunk0_path}")
        else:
            # TODO show error message
            print(f"file missing at chunk0_path={chunk0_path}")

        # TODO concatenate files

        # delete temp directory & files
        delete_directory_recursively(self.get_temp_path())

        return ""


async def main():
    return SoundLoader()
