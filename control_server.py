import flask
import subprocess
import requests
import datetime
import os

browsermob_executable = "libs/browsermob-proxy-2.1.4/bin/browsermob-proxy"
port = "8081"

app = flask.Flask(__name__)


@app.route("/start")
def start():
    # test if already running
    try:
        test_url = 'http://localhost:8080/proxy'
        response = requests.get(test_url)
        if response.status_code == 200:
            return "already running"
    except:
        pass

    # start browserproxy java
    subprocess.Popen([browsermob_executable])

    # wait for it to be settled
    os.system("sleep 5")

    # create new proxy
    start_url = 'http://localhost:8080/proxy'
    start_data = '{"port": ' + port + '}'
    response = requests.post(start_url, start_data)
    assert (response.status_code == 200)

    return "started at " + port


@app.route("/stop")
def stop():
    try:
        stopUrl = 'http://localhost:8080/proxy/' + port
        requests.delete(stopUrl)
    except:
        pass

    while 1:
        try:
            os.system("kill -9 `pgrep browsermob`")
            os.system("kill -9 `pgrep java`")
            result = subprocess.check_output(["pidof", "-s", "/bin/sh " + browsermob_executable]).decode()
            if not result:
                break

            os.system("kill " + result)
            print("killed " + result)
        except subprocess.CalledProcessError as e:
            break
            pass

    return "stopped"


@app.route("/start/capture")
def start_capture():
    capture_mode = flask.request.args.get('capture_mode')
    video_id = flask.request.args.get('video_id')

    har_url = 'http://localhost:8080/proxy/' + str(port) + '/har'
    har_data = '{}'  # '{"captureHeaders":true, "captureCookies":true}'
    response = requests.put(har_url, har_data)
    assert (response.status_code == 204)


@app.route("/stop/capture")
def stop_capture():
    save_url = 'http://localhost:8080/proxy/' + str(port) + '/har'
    response = requests.get(save_url)
    file_name = datetime.datetime.now().isoformat()
    with open(file_name + '.json', "w") as text_file:
        print(response.content.decode(), file=text_file)


if __name__ == '__main__':
    app.run(debug=True)
