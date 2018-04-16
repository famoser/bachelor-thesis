import pickle
import os
import json
import time
import requests as request
import datetime
import psutil
import subprocess
import time
import json

from .config import StaticConfig

static_config = StaticConfig()


class BandwidthManipulator:
    __log_file = None

    def __enter__(self):
        self.__log_file =  open(static_config.log_dir + "/" + "tcset.log", "w")
        self.ensure_sudo()
        self.clear_rate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear_rate()
        self.__log_file.close()

    @staticmethod
    def ensure_sudo():
        os.system("sudo ls")

    def set_rate(self, rate: str = "1M"):
        subprocess.Popen(
            "sudo tcset --device " + static_config.network_device +
            " --direction incoming" +
            " --rate " + rate +
            " --overwrite",
            shell=True, universal_newlines=True, stdout=self.__log_file
        )

    def clear_rate(self):
        subprocess.Popen(
            "sudo tcdel --device " + static_config.network_device +
            " --all",
            shell=True, universal_newlines=True, stdout=self.__log_file
        )