# SoundLoader: Soundcloud Downloader App for iOS

<img width="72" height="72" alt="ic_launcher_soundloader_round" src="https://github.com/user-attachments/assets/1cd86fc9-3afa-415c-8bcf-6d0cd810ab82" />  

## About

SoundLoader is a simple music downloader app, built for Ios with the [Beeware](https://beeware.org) suite of tools and libraries.  

The app accepts a Soundcloud URL (track only) and downloads the track as an .MP4 audio file on your device's local storage.


## Features

*  URL-to-M4A Downloader App
*  Quick Paste Button
*  Album Art
*  Metadata (ID3 Tags)
*  Original Quality

## Screenshots

<img width="405" height="720" alt="Apple iPhone 16 Pro Max Screenshot 1" src="https://github.com/user-attachments/assets/355a98ef-5c96-446d-9b1b-e16e837bab9b" />
<img width="405" height="720" alt="Apple iPhone 16 Pro Max Screenshot 2" src="https://github.com/user-attachments/assets/e463bfb3-b7e0-4dba-8c1e-a00d83b6c4ca" />
<img width="405" height="720" alt="Apple iPhone 16 Pro Max Screenshot 3" src="https://github.com/user-attachments/assets/d466dd7c-af13-4c3a-aac3-5a94b344f438" />

## Requires

* ios device
* xcode
* homebrew
* git
* python
* pip packages:
  * briefcase
  * rubicon-objc
  * requests
  * asyncio
  * aiohttp
  * httpx
  * mutagen
* beeware virtual environment

## How To Build Xcode Project

1.  Install requirements listed above
2.  Set up your Beeware virtual environment, per the [tutorial]((https://docs.beeware.org/en/latest/tutorial/tutorial-0.html#))
3.  [Activate](https://docs.beeware.org/en/latest/tutorial/tutorial-0.html#) your beeware virtual environment
4.  Clone and extract [this](https://github.com/mvxGREEN/SoundLoaderIos) project
6.  'Cd' into extracted project
7.  Build the xcode project by with ['create iOS'](https://docs.beeware.org/en/latest/tutorial/tutorial-5/iOS.html) then ['build iOS'](https://docs.beeware.org/en/latest/tutorial/tutorial-5/iOS.html)
8.  Open generated 'build' folder and locate .xcodeproj file
9.  Open .xcodeproj in Xcode
10.  Build & sign app in xcode
11.  Run app on your physical or simulated iOS device!

## How To Use App


1.  Copy desired URL
2.  Paste into SoundLoader
3.  Tap download button

Done!  File will be saved to your device's Documents directory.


## [Demo](https://youtu.be/Evi0wVs-WLI?si=z8fdNlIfUhn9m3Xa)


## Contributing

We love contributions <3
