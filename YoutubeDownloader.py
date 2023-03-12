import os
import shutil
import sys
from datetime import datetime

import ffmpeg
from time import sleep
from pytube import YouTube

# consts and global variables #
VIDEO_DOWNLOAD_PATH = os.path.dirname(os.path.realpath(__file__)) + '\\env\\Video\\'
AUDIO_DOWNLOAD_PATH = os.path.dirname(os.path.realpath(__file__)) + '\\env\\Audio\\'
TEMP_PATH = os.path.dirname(os.path.realpath(__file__)) + '\\env\\Temp\\'

constBtoMb = pow(10, 6)


#################################################################################################################
# UTILITY FUNCTIONS #
def progress_function(chunk, file_handle, bytes_remaining):
    filesize = chunk.filesize
    filesizeInMegabyte = round(filesize / constBtoMb, 2)
    megabytesDownloaded = round((filesize - bytes_remaining) / constBtoMb, 2)
    current = ((filesize - bytes_remaining) / filesize)
    percent = ('{0:.1f}').format(current * 100)
    progress = int(50 * current)

    status = '█' * progress + '-' * (50 - progress)
    sys.stdout.write(
        chunk.type + ': |{bar}| {percent}% {bytes}/{size} Megabytes\r'.format(bar=status,
                                                                              percent=percent,
                                                                              bytes=megabytesDownloaded,
                                                                              size=filesizeInMegabyte))
    if percent == "100.0":
        sys.stdout.write('\n\n')


def cleanTemp():
    # CLEAN TEMP FOLDER
    for filename in os.listdir(TEMP_PATH):
        file_path = os.path.join(TEMP_PATH, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


#################################################################################################################
# DOWNLOAD FUNCTIONS #


def download(videoObjects, cRes):
    video = videoObjects.streams.filter(res=cRes + 'p').filter().filter(progressive=True).first()
    if video is None:
        print('\n**** VIDEO AND AUDIO ARE 2 DIFFERENT STREAMS FOR THIS RESOLUTION ****')
        print('**** DOWNLOADING BOTH STREAMS AND MERGING USING FFMPEG ****')
        video = videoObjects.streams.filter(res=cRes + 'p').first()
        audio = videoObjects.streams.get_audio_only()
        audio.download(filename=audio.title + "_audio.mp4", output_path=TEMP_PATH)
        video.download(filename=video.title + ".mp4", output_path=TEMP_PATH)

        # https://www.youtube.com/watch?v=BZP1rYjoBgI
        videoFile = ffmpeg.input(TEMP_PATH + video.title + '.mp4')
        audioFile = ffmpeg.input(TEMP_PATH + audio.title + '_audio.mp4')

        ffmpeg.output(audioFile, videoFile, VIDEO_DOWNLOAD_PATH + video.title + ' (' + video.resolution + ')' + '.mp4') \
            .run()
    else:
        video.download(output_path=VIDEO_DOWNLOAD_PATH, filename=video.title + ' (' + video.resolution + ')' + '.mp4')


def input_management(videoObjects):
    quitLoop = False

    while not quitLoop:
        resList = set()
        # get possible Resolutions
        for stream in videoObjects.streams:
            if stream.resolution is not None:
                print(stream)
                resList.add(stream.resolution)

        resList = sorted(list(resList))
        print("Possible resolutions are:")

        for res in resList:
            print(res)

        cRes = input("Input resolution number (no p): ")

        if not cRes + 'p' in resList:
            print("Error in resolution, you put " + cRes)
        else:
            quitLoop = True

    # After input management loop return chosen resolution
    return cRes


#################################################################################################################
# MAIN #


if __name__ == '__main__':
    #TODO Remove not admitted characters in filename
    cleanTemp()
    while 1:
        audioVideoChoice = input("Only audio(0) or video(1)? Waiting input: ")
        sys.stdin.flush()
        if audioVideoChoice == '1' or audioVideoChoice == '0':
            URL = input("Link: ")
            youtubeObject = YouTube(URL, on_progress_callback=progress_function)
            print("You passed the video: " + youtubeObject.title)

        match str(audioVideoChoice):
            case '0':
                try:
                    if youtubeObject is None:
                        raise Exception
                    else:
                        audio = youtubeObject.streams.get_audio_only()
                        audio.download(filename=audio.title + '.mp3', output_path=AUDIO_DOWNLOAD_PATH)
                        print("******************** DONE ********************")

                except Exception as e:
                    print("ERROR - " + str(e))
                    sleep(1)

            case "1":
                try:
                    res = input_management(youtubeObject)
                    download(youtubeObject, res)
                    print("******************** DONE ********************")
                except Exception as e:
                    print("ERROR - " + str(e))
                    sleep(1)

            case _:
                print("Wrong input, try again")

        cleanTemp()

    ## END OF WHILE ##
