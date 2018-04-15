import os


class StaticConfig:
    root_dir = os.path.basename(os.path.dirname("."))

    captures_dir = root_dir + "/" + "capture"
    skip_seconds = 120
    wait_seconds = 4
    capture_version = "1"

    analyze_dir = root_dir + "/" + "analyze"

    browsermob_dir = root_dir + "/" + "tools/browsermob-proxy-2.1.4"
    netflix_extension_path = root_dir + "/" + "tools/netflix-1080p-1.2.9.crx"

    config_dir = root_dir + "/" + "config"
    temp_dir = root_dir + "/" + "temp"

    credentials_file_path = config_dir + "/" + "credentials.json"
    cookie_file_path = temp_dir + "/" + "cookies.pkl"