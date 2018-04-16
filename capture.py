import datetime

from python_libs.config import StaticConfig
from python_libs.config import Inventory
from python_libs.netflix_browser import NetflixBrowser
from python_libs.browser_proxy import BrowserProxy

config = StaticConfig()
inventory = Inventory()

# initialize the proxy
with BrowserProxy() as proxy:
    proxy_port = proxy.get_port()

    # initialize the browser
    with NetflixBrowser(proxy_port) as browser:

        # capture netflix ids
        for video in inventory.__dict__:
            video_id = inventory.__dict__[video]

            # capture rate 1-4
            rate = 1
            successful = True
            while rate <= 4 and successful:
                # continue only if no errors found
                successful = browser.play_in_browser(video_id, rate)

                # create the filename
                fileName = str(video_id) + '_'
                fileName += str(rate) + "_ "
                fileName += datetime.datetime.now().isoformat().replace(":", "_") + "_"
                fileName += str(config.capture_version)

                # save the capture
                proxy.save_active_capture(config.captures_dir + "/" + fileName)

                # increment counter
                rate += 1

            if not successful:
                print("something failed; stopped capture early")
