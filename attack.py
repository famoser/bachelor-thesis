import datetime
import time
import humanfriendly

from python_libs.config import StaticConfig
from python_libs.config import Inventory
from python_libs.netflix_browser import NetflixBrowser
from python_libs.browser_proxy import BrowserProxy
from python_libs.bandwidth_manipulator import BandwidthManipulator


class Configuration:
    def __init__(self):
        self.capture_duration = 60
        self.increase_throughput_step_size = 100
        self.start_throughput = 800
        self.stop_throughput = 1200
        self.wait_after_page_load = 40
        self.wait_after_throughput_adjustment = 20


static_config = StaticConfig()
video_ids = Inventory().small_capture()

# define the ids we want to capture
config = Configuration()

# calculate length of capture for user
loop_count = (config.stop_throughput - config.start_throughput) / config.increase_throughput_step_size
video_count = len(video_ids)
loop_length = config.capture_duration + config.wait_after_throughput_adjustment
full_length = video_count * (config.wait_after_page_load + loop_count * loop_length)
print("this capture will run for " + humanfriendly.format_timespan(full_length))

# initialize the bandwidth
with BandwidthManipulator() as bandwidth:
    # initialize the proxy
    with BrowserProxy() as proxy:
        # initialize the browser
        with NetflixBrowser(proxy.get_port()) as browser:

            # get all video ids from the inventory, and perform the "attack"
            video_ids = video_ids
            for video in video_ids:
                video_id = video_ids[video]
                current_amount = config.start_throughput

                # inform user
                print("capturing " + video + " with id " + str(video_id))
                print("starting capture at " + str(current_amount) + "k")
                print("waiting for " + str(config.wait_after_page_load) + "s till capture starts")

                # set initial amount & navigate
                bandwidth.set_rate(str(current_amount) + "k")
                if not browser.navigate(video_id):
                    print("could not navigate to video")
                    continue

                # let netflix adjust after page load
                time.sleep(config.wait_after_page_load)

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
                    if current_amount > config.stop_throughput:
                        break

                    # set new bandwidth and repeat
                    current_amount += config.increase_throughput_step_size

                    # set new throughput & wait for it to settle
                    print("new bandwidth is " + str(current_amount) + "k")
                    print("waiting for it to settle for " + str(config.capture_duration) + "s")
                    bandwidth.set_rate(str(current_amount) + "k")
                    time.sleep(config.wait_after_throughput_adjustment)

print("finished")
