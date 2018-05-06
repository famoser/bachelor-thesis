import datetime
import time
import humanfriendly

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

        # how long the process sleeps after video repositioning (done at the start of capture, twice)
        #
        # choosing the same value like after video load
        self.wait_after_repositioning = 20

        # how many seconds are skipped to speed up the capture
        #
        # choosing 20 as this is almost instantly in the cache
        self.skip_seconds = 20

        # how many seconds the video is left alone before again some seconds are skipped
        #
        # choosing 15 as this should be enough to fill up the skip seconds buffer
        self.wait_seconds = 5

        # failsafe to ensure the video speed up does not run forever
        #
        # allow 5h videos, plus reserve consisting of the self.wait_seconds
        self.max_iterations = int(60 * 60 * 5 / self.skip_seconds)


static_config = StaticConfig()
video_ids = Inventory().full_capture()

# define the ids we want to capture
config = Configuration()

# test settings
if True:
    video_ids = Inventory().small_capture()
    config.wait_after_video_load = 10
    config.wait_after_ensured_video_load = 10
    config.wait_after_repositioning = 10

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

            # go to middle of video to have a clean capture when starting at 0
            if not browser.set_video_time(100):
                print("could not reposition video")
                continue

            print("repositioned video, waiting to settle for " + str(config.wait_after_repositioning) + "s")
            time.sleep(config.wait_after_repositioning)

            # get available bitrates
            bitrates = browser.get_available_bitrates()
            if bitrates is None:
                print("no bitrates found")
                continue

            for bitrate in bitrates:
                # set bitrate, start capture, & go to start of video
                browser.set_bitrate(bitrate)
                proxy.start_new_capture()
                browser.set_video_time(0)

                print("capturing with bitrate " + str(bitrate) + "k")

                # speed up capture after waiting for it to settle
                print("starting with speed up in " + str(config.wait_after_repositioning) + "s")
                time.sleep(config.wait_after_repositioning)
                browser.speed_up_playback(config.wait_after_repositioning, config.skip_seconds, config.wait_seconds,
                                          config.max_iterations)

                # create the filename
                fileName = str(video_id) + '_'
                fileName += str(bitrate) + "_ "
                fileName += datetime.datetime.now().isoformat().replace(":", "_")

                # save the capture with the active config
                configuration = config.__dict__
                configuration["bitrate"] = bitrate
                proxy.save_active_capture(static_config.captures_dir + "/" + fileName, configuration)

print("finished")
