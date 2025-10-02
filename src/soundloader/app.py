"""
A Cloud-to-MP3 Downloader for IOS
"""

import toga
import asyncio
import aiohttp
from aiohttp import ClientConnectorError
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

# TODO uncommnt
#from rubicon.objc import ObjCClass

# expose objc TODO uncomment
#UIPasteboard = ObjCClass('UIPasteboard')


# get absolute path to destination directory
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


# TODO (1) asynchronously load audio
async def load_audio(input_url):
    print(f"start load_audio: input_url={input_url}")

    # get html as string
    html = await get_html_from(input_url)
    print("finished get_html_from")

    # exit if html too small TODO show error message
    if len(html) < 300:
        print("exiting load_audio; len(html) < 300")
        return

    # parse html for player url


# (1A) get html from url as string
async def get_html_from(url: str) -> str:
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


# TODO (1B) parse html for player_url
def extract_player_url(html):
    print(f"extract_player_url: len(html)={len(html)}")


# TODO (1C) asynchronously load and extract html from player_url in webview
async def load_in_webview(player_url):
    print(f"start load_in_webview: player_url={player_url}")


# TODO (1D) parse request urls client_id param
def extract_client_id():
    print(f"extract_client_id")


# TODO (1E) parse html for stream_url, thumbnail_url, and metadata
def extract_metadata(html):
    print(f"extract_audio_data: len(html)={len(html)}")


# TODO (1F) asynchronously request json w/ response handler
async def request_json(full_stream_url, callback):
    print(f"start request_json: full_stream_url={full_stream_url}")


# TODO (1G) parse json for playlist_url
def handle_json_response(json):
    print(f"start handle_json_response: json={json}")


# TODO (2) asynchronously download audio
async def download_audio(audio_url, dest_path, filename):
    print(f"start download_audio: audio_url={audio_url}, filename={dest_path}, filename={filename}")


# TODO (2A) asynchronously download m3u
async def download_m3u(playlist_url, dest_path):
    print(f"start download_m3u: playlist_url={playlist_url}")


# TODO (2B) parse m3u for chunk_urls
def extract_chunk_urls(m3u_filepath):
    print(f"extract_chunk_urls: m3u_filepath={m3u_filepath}")


# TODO (2C) asynchronously download chunks
async def download_chunks(chunk_urls, dest_path):
    print(f"start download_chunks: len(chunk_urls)={len(chunk_urls)}")


# TODO (2D) concat chunks into mp3 w/ thumbnail and metadata
def concat_chunk_files(chunk_dir_path, dest_filepath):
    print("start concat_chunk_files")


class SoundLoader(toga.App):
    # startup
    def startup(self):
        # register fonts
        toga.Font.register("FiraSans", "resources/FiraSans-Regular.ttf")
        toga.Font.register("FiraSansExtraLight", "resources/FiraSans-ExtraLight.ttf")
        toga.Font.register("FiraSansBold", "resources/FiraSans-Bold.ttf")

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

    # TODO uncomment
    # paste copied text into url_input
    def paste_action(self):
        print("paste_action")
        # Get the general pasteboard instance
        #pasteboard = UIPasteboard.generalPasteboard

        # Get the string content from the pasteboard
        #pasted_text = pasteboard.string

        # Check if there is any text to paste
        #if pasted_text:
            # Set the value of the TextInput to the pasted text
            #self.url_input.value = pasted_text

    # clear text from url_input
    def clear_action(self):
        print("clear_action")
        self.url_input.value = ""

    # on load click
    async def start_load_audio(self, widget):
        print("load button clicked (start_load_audio)")

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

            # update ui
            self.show_preview_layout(filename, thumbnail_url)
        # TODO show error message on invalid input

    # on download click
    async def start_download_audio(self, widget):
        print("download button clicked (start_download_audio)")

        # hide keyboard
        self.app.main_window.content = self.app.main_window.content

        # update ui
        await self.show_downloading_layout()

        # start downloading audio
        dl_a_task = asyncio.create_task(
            download_audio(f"{self.url_input.value}",
                           get_dest_path(),
                           f"{self.filename_input.value}"))
        await dl_a_task
        print(f"finished download_audio task")

        # TODO get chunk filepaths
        # file_path_chunks = get_dest_path() + f"{self.filename_input.value}"
        file_path_dest = get_dest_path() + f"{self.filename_input.value}" + ".mp3"
        print(
            f"file_path_dest={file_path_dest}")

        # TODO concat chunk files

        await self.show_finished_layout()
        print("finished showing finished layout!")


async def main():
    return SoundLoader()
