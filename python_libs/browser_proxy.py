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

config = StaticConfig()


class BrowserProxy:
    __port = None
    __capture_url = None

    def __enter__(self):
        self.__start_browsermob()
        self.__initialize_browsermob()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__kill_browsermob()

    @staticmethod
    def __start_browsermob():
        """
        starts the browsermob executable
        """
        subprocess.Popen([config.browsermob_dir + "/bin/browsermob-proxy"])
        i = 3
        while i > 0:
            print("waiting " + str(i))
            time.sleep(1)
            i -= 1

    def __initialize_browsermob(self):
        """
        initialized the capture at the first free port
        """
        # start the proxy, and save the port it returns
        response = request.post('http://localhost:8080/proxy', '{}')
        start_response = json.loads(response.content)
        self.__port = start_response["port"]
        assert (response.status_code == 200)

        # this url will now be used to retrieve capture state
        self.__capture_url = 'http://localhost:8080/proxy/' + str(self.__port) + '/har'

        # initialize capture
        response = request.put(self.__capture_url, '{}')
        assert (response.status_code == 204)
        print('initialized capture at port ' + str(self.__port))

    @staticmethod
    def __kill_browsermob():
        """
        kills the browsermob executable
        """

        # get all current active processes by name
        dictionary = {}
        for process in psutil.process_iter():
            dictionary[process.pid] = process

        # first kill browser mob, then kill the java process that follows
        killed_browser_mob = None
        for pid in sorted(dictionary):
            if 'browsermob-prox' in dictionary[pid].name():
                dictionary[pid].kill()
                killed_browser_mob = True
                print("found & killed old process")
            # kill the first java process after browsermob-prox was started
            if "java" in dictionary[pid].name() and killed_browser_mob:
                dictionary[pid].kill()
                print("found & killed old java process")
                return

    def get_port(self) -> int:
        """
        get the port the proxy is running at
        :return: the port
        """
        return self.__port

    def save_capture_state(self, file_path: str) -> bool:
        """
        saves the current capture state to a file, and clears it afterwards
        :param file_path: the path of the file to use, .json is appended
        :return: if the state was retrieved successfully
        """

        # retrieve the state
        response = request.get(self.__capture_url)

        # check if request was successful
        if response.status_code == 200:
            with open(file_path + '.json', "w") as text_file:
                print(response.content.decode(), file=text_file)

            return True

        return False

    def clear_capture_state(self):
        """
        retrieves the current capture state, and discards it
        :return: if the state was retrieved successfully
        """

        # discard current state by retrieving the state and not using it
        response = request.get(self.__capture_url)
        return response.status_code == 200
