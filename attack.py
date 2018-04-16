import datetime
import time

from python_libs.config import StaticConfig
from python_libs.config import Inventory
from python_libs.netflix_browser import NetflixBrowser
from python_libs.browser_proxy import BrowserProxy
from python_libs.bandwidth_manipulator import BandwidthManipulator

config = StaticConfig()
inventory = Inventory()

print(config.root_dir)

# define the ids we want to capture

sleep_interval = 60
increase_amount = 100
start_amount = 800
stop_amount = 1200
burn_initially = 30

# initialize the bandwidth
with BandwidthManipulator() as bandwidth:

    # initialize the proxy
    with BrowserProxy() as proxy:
        proxy_port = proxy.get_port()

        # initialize the browser
        with NetflixBrowser(proxy_port) as browser:

            # get all video ids from the inventory, and perform the "attack"
            video_ids = inventory.__dict__
            for video in video_ids:
                video_id = video_ids[video]
                print("capturing " + video + " with id " + str(video_id))
                current_amount = start_amount

                # initial amount
                bandwidth.set_rate(str(current_amount) + "k")

                # continue only if no errors found
                if not browser.navigate(video_id):
                    print("could not navigate to video")

                # skip initial adjusting
                time.sleep(burn_initially)
                proxy.clear_capture_state()

                while True:
                    print("capturing at " + str(current_amount) + "k for " + str(sleep_interval) + "s")
                    time.sleep(sleep_interval)

                    # create the filename
                    fileName = str(video_id) + '_'
                    fileName += str(current_amount) + "_ "
                    fileName += datetime.datetime.now().isoformat().replace(":", "_") + "_"
                    fileName += str(config.attack_version)

                    # save the capture
                    proxy.save_capture_state(config.attack_dir + "/" + fileName)

                    # break if finished
                    if current_amount == stop_amount:
                        break

                    # set new bandwidth and repeat
                    current_amount += increase_amount
                    # initial amount
                    bandwidth.set_rate(str(current_amount) + "k")

print("finished")
