import os


class StaticConfig:
    root_dir = os.path.abspath(os.path.dirname("."))

    captures_dir = root_dir + "/" + "capture"
    skip_seconds = 120
    wait_seconds = 4

    capture_version = 1
    attack_version = 1

    analyze_dir = root_dir + "/" + "analyze"

    browsermob_dir = root_dir + "/" + "tools/browsermob-proxy-2.1.4"
    netflix_extension_path = root_dir + "/" + "tools/netflix-1080p-1.2.9.crx"

    config_dir = root_dir + "/" + "config"
    temp_dir = root_dir + "/" + "temp"

    attack_dir = root_dir + "/" + "attack"

    plot_dir = root_dir + "/" + "plot"

    credentials_file_path = config_dir + "/" + "credentials.json"
    cookie_file_path = temp_dir + "/" + "cookies.pkl"

    network_device = "wlp4s0"


class Inventory:
    def __init__(self):
        # netflix test video
        self.test_video = 80018499

        # action
        self.transformers = 70103763
        self.civil_war = 80088567

        # anime
        self.naruto = 70105699
        self.berserk = 70276596

        # documentaries
        self.minimalism = 80114460
        self.expedition_happiness = 80225528
