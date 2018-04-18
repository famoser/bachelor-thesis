import datetime

from python_libs.config import StaticConfig
from python_libs.config import Inventory
from python_libs.netflix_browser import NetflixBrowser
from python_libs.browser_proxy import BrowserProxy


class Configuration:
    def __init__(self):
        self.min_rate = 1
        self.max_rate = 4


config = Configuration()
static_config = StaticConfig()
video_ids = Inventory().small_capture()

# initialize the proxy
with BrowserProxy("capture") as proxy:
    proxy_port = proxy.get_port()

    # initialize the browser
    with NetflixBrowser(proxy_port) as browser:

        # capture netflix ids
        for video in video_ids:
            video_id = video_ids[video]

            # capture rate
            current_rate = config.min_rate
            successful = True
            while current_rate <= config.max_rate and successful:
                # continue only if no errors found
                successful = browser.play_in_browser(video_id, current_rate)

                # create the filename
                fileName = str(video_id) + '_'
                fileName += str(current_rate) + "_ "
                fileName += datetime.datetime.now().isoformat().replace(":", "_") + "_"
                fileName += str(static_config.capture_version)

                # save the capture
                configuration = config.__dict__
                configuration["current_rate"] = current_rate
                proxy.save_active_capture(static_config.captures_dir + "/" + fileName, configuration)

                # increment counter
                current_rate += 1

            if not successful:
                print("something failed; stopped capture early")
