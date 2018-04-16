import requests as request
import psutil
import subprocess
import time
import json

from .config import StaticConfig

static_config = StaticConfig()


class CaptureStatistics:
    def __init__(self):
        self.start_timestamp = None
        self.end_timestamp = None


class BrowserProxy:
    __port = None
    __capture_url = None
    __current_page_ref = None
    __current_page_count = 0
    __current_capture_start = None
    __log_file = None

    def __enter__(self):
        self.__log_file = open(static_config.log_dir + "/" + "browsermob-proxy.log", "w")
        self.__start_browsermob()
        self.__initialize_browsermob()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__kill_browsermob()
        self.__log_file.close()

    def __start_browsermob(self):
        """
        starts the browsermob executable
        """

        # start executable, and save logfile to
        subprocess.Popen(
            static_config.browsermob_dir + "/bin/browsermob-proxy",
            shell=True, universal_newlines=True, stdout=self.__log_file
        )

        # wait three seconds for it to settle
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

        # start new capture
        # we could also pass "{initialPageRef": "' + self.__set_next_page_ref() + '}" to the request before
        self.start_new_capture()

        print('initialized capture at port ' + str(self.__port))

    def __set_next_page_ref(self):
        self.__current_page_count += 1
        self.__current_page_ref = "page_" + str(self.__current_page_count)
        return self.__current_page_ref

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

    def save_active_capture(self, file_path: str, configuration: dict, start_new: bool = True) -> bool:
        """
        saves the current capture state to a file, and clears it afterwards
        :param start_new: if to start a new capture immediately
        :param configuration: the configuration of the capture for later reference
        :param file_path: the path of the file to use, .json is appended
        :return: if the state was retrieved successfully
        """

        # retrieve the state
        response = request.get(self.__capture_url)
        if response.status_code != 200:
            return False

        # create statistics
        statistics = CaptureStatistics()
        statistics.start_timestamp = self.__current_capture_start
        statistics.end_timestamp = time.time()

        # load json
        content = json.loads(response.content.decode())

        # filter packets for current page ref
        packets = []
        for entry in content["log"]["entries"]:
            if entry["pageref"] == self.__current_page_ref:
                packets.append(entry)

        # save packets & configuration
        save = {"configuration": configuration, "packets": packets, "statistics": statistics.__dict__}
        with open(file_path + '.json', "w") as file:
            json.dump(save, file)

        # start new capture
        if start_new:
            self.start_new_capture()

        return True

    def start_new_capture(self):
        """
        retrieves the current capture state, and discards it
        :return: if the state was retrieved successfully
        """

        # set new state by starting a new capture page
        self.__current_capture_start = time.time()
        response = request.put(self.__capture_url + "/pageRef", '{"pageRef": "' + self.__set_next_page_ref() + '}')
        return response.status_code == 200
