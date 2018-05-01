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
        # how long a capture captures packets
        #
        # video packets loaded in packets of length 3
        # choosing 59 here to avoid one packet too much due to slightly offset timing
        self.capture_duration = 119

        # each capture increases by this amount
        #
        # because at the low spectrum bitrate changes fast, we need a relatively low value here
        self.throughput_step_size = 60

        # the throughput allowed when starting the capture
        #
        # start at 800 because lower the player something does not load at all
        self.min_throughput = 800

        # the max throughput, after which the capture is stopped
        #
        # not much change is expected higher than this number
        self.max_throughput = 2400

        # if the capture should start with the low bandwidth and the increase
        # or the other way around
        #
        # set to False because it is unclear how low bandwidth netflix can handle
        self.low_to_high = False

        # how long the process sleeps after video url load
        #
        # choosing 60 because at low bandwidth it needs a lot of time to adapt (ca 50s)
        self.wait_after_video_load = 30

        # there are certain checks executed to ensure the video is playing
        # after these checks, wait for another few seconds to again ensure the video is buffered etc
        #
        # choosing 60 for consistency
        self.wait_after_ensured_video_load = 30

        # how long the process sleeps after video repositioning (done at the start of capture)
        #
        # choosing the same value like after video load
        self.wait_after_repositioning = 30

        # how long no capture happens after adjusting the bandwidth
        #
        # this should give the player enough time to adjust its bitrate
        self.wait_after_throughput_adjustment = 40  #

        # where the video capture starts
        #
        # choosing 0 to be able to capture as short videos as possible
        self.initial_video_position = 0


static_config = StaticConfig()
video_ids = Inventory().full_capture()

# define the ids we want to capture
config = Configuration()

# test settings
if False:
    video_ids = Inventory().small_capture()
    config.wait_after_video_load = 20
    config.wait_after_ensured_video_load = 20
    config.wait_after_repositioning = 20
    config.capture_duration = 20
    config.wait_after_throughput_adjustment = 20
    config.throughput_step_size = 500
    config.min_throughput = 0
    config.max_throughput = 3000

# calculate length of capture for user
loop_count = (config.max_throughput - config.min_throughput) / config.throughput_step_size
video_count = len(video_ids)
loop_length = config.capture_duration + config.wait_after_throughput_adjustment
full_length = video_count * (config.wait_after_video_load + config.wait_after_repositioning + loop_count * loop_length)
print("this capture will run for " + humanfriendly.format_timespan(full_length))

# initialize the bandwidth
with BandwidthManipulator() as bandwidth:
    # initialize the proxy
    with BrowserProxy("attack") as proxy:

        # initialize the browser
        with NetflixBrowser(proxy.get_port()) as browser:
            # advising user to reset his mouse pointer
            print("please move your mouse to the center of the chromium window,"
                  ", where the netflix play button will appear, and keep it there")

            # get all video ids from the inventory, and perform the "attack"
            video_ids = video_ids
            for video in video_ids:
                video_id = video_ids[video]
                if config.low_to_high:
                    current_amount = config.min_throughput
                else:
                    current_amount = config.max_throughput

                # inform user
                print("## capturing " + video + " with id " + str(video_id) + " ###")

                # setting initial bandwidth
                print("starting capture at " + str(current_amount) + "k")
                bandwidth.set_rate(str(current_amount) + "k")

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

                # wait till repositioning is done
                if not browser.set_video_time(config.initial_video_position):
                    print("could not reposition video")
                    continue

                print("repositioned video, waiting to settle for " + str(config.wait_after_repositioning) + "s")
                time.sleep(config.wait_after_repositioning)

                # now start the capture
                proxy.start_new_capture()

                while True:
                    print("capturing at " + str(current_amount) + "k for " + str(config.capture_duration) + "s")

                    # start the capture & wait
                    proxy.start_new_capture()
                    time.sleep(config.capture_duration)

                    # create the filename
                    fileName = str(video_id) + '_'
                    fileName += str(current_amount) + "_ "
                    fileName += datetime.datetime.now().isoformat().replace(":", "_") + "_"
                    fileName += str(static_config.attack_version)

                    # save the capture with the active config
                    configuration = config.__dict__
                    configuration["current_amount"] = current_amount
                    proxy.save_active_capture(static_config.attack_dir + "/" + fileName, configuration)

                    # break if finished
                    if config.low_to_high:
                        # set new bandwidth and repeat
                        if current_amount >= config.max_throughput:
                            break
                        current_amount += config.throughput_step_size
                    else:
                        if current_amount <= config.min_throughput:
                            break
                        current_amount -= config.throughput_step_size

                    # set new throughput & wait for it to settle
                    print("new bandwidth is " + str(current_amount) + "k")
                    print("waiting for it to settle for " + str(config.capture_duration) + "s")
                    bandwidth.set_rate(str(current_amount) + "k")
                    time.sleep(config.wait_after_throughput_adjustment)

print("finished")
