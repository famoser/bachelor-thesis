import datetime
import time
import os
import json

from python_libs.config import StaticConfig
from python_libs.config import Inventory
from python_libs.mouse import Mouse
from python_libs.netflix_browser import NetflixBrowser
from python_libs.browser_proxy import BrowserProxy
from python_libs.bandwidth_manipulator import BandwidthManipulator


class Configuration:
    def __init__(self):
        # how long the process sleeps after video url load
        #
        # choosing 20 because normally the video starts almost instantly
        self.wait_after_video_load = 20

        # there are certain checks executed to ensure the video is playing
        # after these checks, wait for another few seconds to again ensure the video is buffered etc
        #
        # choosing 20 for consistency
        self.wait_after_ensured_video_load = 20

        # the position at which the video is started to be captured
        #
        # choosing the same value like after video load
        self.reposition_to = 200

        # how long we wait till we stop the capture and continue
        #
        # choosing 5 minutes
        self.capture_length = 5*60


static_config = StaticConfig()
video_ids = Inventory().full_capture()

# define the ids we want to capture
config = Configuration()

done_videos = []
file_name = "capture_videos_done.json"
if os.path.exists(file_name):
    with open(file_name, "r") as file:
        done_videos = json.load(file)

# initialize the proxy
with BrowserProxy("attack") as proxy:
    # initialize the browser
    with NetflixBrowser(proxy.get_port()) as browser:
        # advising user to reset his mouse pointer
        print("please move your mouse to the center of the chromium window,"
              ", where the netflix play button will appear, and keep it there")

        # get all video ids from the inventory, and perform the "attack"
        for video in video_ids:
            video_id = video_ids[video]

            if video_id in done_videos:
                continue

            # inform user
            print("## capturing " + video + " with id " + str(video_id) + " ###")

            # navigate to video & prepare capture
            if not browser.navigate(video_id):
                print("could not navigate to video")
                continue

            # wait till player initializes
            print("navigated to video, waiting to settle for " + str(config.wait_after_video_load) + "s")
            time.sleep(config.wait_after_video_load)

            # ensure player has initialized by clicking on presumed underlying "play" button
            # if there is no button (so the video is already playing) this has no effect
            Mouse.click_at_current_position()
            print("ensured video is playing, now waiting to settle for " +
                  str(config.wait_after_ensured_video_load) + "s")
            time.sleep(config.wait_after_ensured_video_load)

            # get available bitrates
            bitrates = browser.get_available_bitrates()
            if bitrates is None:
                print("no bitrates found")
                continue

            for bitrate in bitrates:
                # set bitrate, start capture, & go to start of video
                browser.set_bitrate(bitrate)
                proxy.start_new_capture()
                browser.set_video_time(config.reposition_to)

                print("capturing with bitrate " + str(bitrate) + "k")
                browser.wait_for_video_to_stop(config.capture_length, 1)

                # create the filename
                fileName = str(video_id) + '_'
                fileName += str(bitrate) + "_ "
                fileName += datetime.datetime.now().isoformat().replace(":", "_")

                # save the capture with the active config
                configuration = config.__dict__
                configuration["bitrate"] = bitrate
                proxy.save_active_capture(static_config.captures_dir + "/" + fileName, configuration)

                # need to reinitialize browser completely
                if not browser.navigate(video_id):
                    print("could not navigate to video")
                    continue

                # wait till player initializes
                print("navigated to video, waiting to settle for " + str(config.wait_after_video_load) + "s")
                time.sleep(config.wait_after_video_load)

                # ensure player has initialized by clicking on presumed underlying "play" button
                # if there is no button (so the video is already playing) this has no effect
                Mouse.click_at_current_position()
                print("ensured video is playing, now waiting to settle for " +
                      str(config.wait_after_ensured_video_load) + "s")
                time.sleep(config.wait_after_ensured_video_load)

            done_videos.append(video_id)
            with open(file_name, "w+") as file:
                json.dump(done_videos, file)

print("finished")
