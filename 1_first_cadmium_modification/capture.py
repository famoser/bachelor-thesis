import datetime

from python_libs.config import StaticConfig
from python_libs.netflix_browser import NetflixBrowser
from python_libs.browser_proxy import BrowserProxy

config = StaticConfig()

print(config.root_dir)

# define the ids we want to capture
netflix_ids = [80111451, 80111452, 80018499]

# initialize the proxy
with BrowserProxy() as proxy:
    proxy_port = proxy.get_port()

    # initialize the browser
    with NetflixBrowser(proxy_port) as browser:

        # capture netflix ids
        for netflix_id in netflix_ids:

            # capture rate 1-4
            rate = 1
            successful = True
            while rate <= 4 and successful:
                # continue only if no errors found
                successful = browser.play_in_browser(netflix_id, rate)

                # create the filename
                fileName = str(netflix_id) + '_'
                fileName += str(rate) + "_ "
                fileName += datetime.datetime.now().isoformat().replace(":", "_") + "_"
                fileName += config.capture_version

                # save the capture
                proxy.save_capture_state(fileName)

                # increment counter
                rate += 1

            if not successful:
                print("something failed; stopped capture early")
