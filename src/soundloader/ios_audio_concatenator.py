//
//  ios_audio_concatenator.py
//  SoundLoader
//
//  Created by Max Green on 10/5/25.

# ios_audio_concatenator.py
from rubicon.objc import ObjCClass, objc_method, objc_block, py_from_ns
from pathlib import Path
import asyncio

# Get references to native classes
NSURL = ObjCClass('NSURL')
NSError = ObjCClass('NSError')
NSArray = ObjCClass('NSArray')

# Get a reference to the custom Objective-C class
MediaConcatenatorNative = ObjCClass('MediaConcatenator')


class AudioConcatenator:
    def __init__(self):
        # Initialize the native Objective-C object
        self._native = MediaConcatenatorNative.alloc().init()

    def concatenate_audio_files(self, file_paths, output_path):
        """
        Concatenates audio files asynchronously.

        :param file_paths: A list of pathlib.Path objects for the source files.
        :param output_path: A pathlib.Path object for the destination file.
        :return: A Python Future that resolves to the output_path on success.
        """
        
        # 1. Convert Python objects (Path, list) to native Objective-C objects (NSURL, NSArray)
        
        # Convert list of Path objects to an NSArray of NSURL objects
        ns_urls = []
        for p in file_paths:
            # We must use fileURLWithPath for local files
            ns_url = NSURL.fileURLWithPath(str(p))
            ns_urls.append(ns_url)
        native_file_urls = NSArray.arrayWithArray(ns_urls)

        # Convert output Path to NSURL
        native_output_url = NSURL.fileURLWithPath(str(output_path))
        
        # Create an asyncio Future to track the asynchronous native operation
        future = asyncio.Future()

        # 2. Define the Objective-C completion block (runs when the native work is done)
        @objc_block
        def completion_handler(success: bool, error: NSError) -> None:
            # Transfer the result back to the Python world
            if success:
                future.set_result(output_path)
            else:
                py_error = py_from_ns(error)
                future.set_exception(Exception(f"Audio concatenation failed: {py_error.localizedDescription}"))
        
        # 3. Call the native Objective-C method
        self._native.concatenateAudioFiles_toOutputURL_completionHandler_(
            native_file_urls,
            native_output_url,
            completion_handler
        )

        return future
