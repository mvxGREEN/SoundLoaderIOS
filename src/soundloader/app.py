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
from io import BytesIO
from pathlib import Path
from toga.validators import MinLength, StartsWith, Contains
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, LEFT, CENTER, RIGHT
import ctypes
from ctypes.util import find_library
from ctypes import cdll, CDLL, util, c_int64, c_int32, c_uint32, Structure, byref, POINTER
import rubicon.objc as objc
from rubicon.objc import ObjCClass, ObjCBlock, Block, objc_method, CGRect, CGSize, CGPoint, ObjCInstance, objc_const
from rubicon.objc.api import py_from_ns
from rubicon.objc.runtime import load_library, send_message
from rubicon.objc.api import *
from rubicon.objc import *
from rubicon.objc.runtime import *


# init objc libraries
cdll.LoadLibrary(util.find_library('Photos'))
AVFoundation = cdll.LoadLibrary(util.find_library('AVFoundation'))

# create objc class objects
NSURL = ObjCClass('NSURL')
NSError = ObjCClass('NSError')
NSArray = ObjCClass('NSArray')
UIPasteboard = ObjCClass('UIPasteboard')
AVAsset = ObjCClass('AVAsset')
AVURLAsset = ObjCClass('AVURLAsset')
AVMutableComposition = ObjCClass('AVMutableComposition')
AVAssetExportSession = ObjCClass('AVAssetExportSession')
AVAssetTrack = ObjCClass('AVAssetTrack')


# get destination directory filepath based on os at runtime
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

        # start downloading video
        dl_v_task = asyncio.create_task(
            download_audio(f"{self.url_input.value}",
                           get_dest_dir_path(),
                           f"{self.filename_input.value}"))
        await dl_v_task
        print(f"finished video download!")

        # TODO download audio
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

        # save new video to photo library
        save_audio(file_path_video)


def main():
    return SoundLoader()
