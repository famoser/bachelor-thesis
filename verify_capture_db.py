import sqlite3
import os.path
from python_libs.config import StaticConfig
from python_libs.har_analyzer import HarAnalyzer

config = StaticConfig()
analyzer = HarAnalyzer(config.captures_dir, '.json')


def boolean_to_successful(input: bool, failed_optional: str = ""):
    if input:
        return "SUCCESSFUL"
    else:
        return "FAILED" + failed_optional


# get sqlite connection
db_file_name = config.captures_dir + "/data.sqlite"
connection = sqlite3.connect(db_file_name)

cursor = connection.cursor()

cursor.execute("SELECT DISTINCT movie_id FROM captures")
db_movies = cursor.fetchall()
for db_movie in db_movies:
    movie_id = db_movie[0]
    print("checking " + str(movie_id))

    cursor.execute("SELECT DISTINCT bitrate FROM captures WHERE movie_id = ?", [movie_id])
    db_bitrates = cursor.fetchall()

    print("found " + str(len(db_bitrates)) + " bitrates")

    for db_bitrate in db_bitrates:
        bitrate = db_bitrate[0]
        print("  checking " + str(bitrate))
        cursor.execute("SELECT DISTINCT p.range_start, p.range_end, p.body_size "
                       "FROM packets p "
                       "INNER JOIN captures c ON c.id = p.capture_id "
                       "WHERE c.bitrate = ? AND c.movie_id = ? AND p.body_size > 0 AND p.is_video = 1 "
                       "ORDER BY p.range_start",
                       [bitrate, movie_id])
        db_packets = cursor.fetchall()

        # find start points and their max length
        start_points = {}
        for db_packet in db_packets:
            found = False

            # extend existing start points
            for start_point in start_points:
                if start_points[start_point] == db_packet[0]:
                    start_points[start_point] = db_packet[1] + 1
                    found = True

            # create new start point of not found
            if not found:
                start_points[db_packet[0]] = db_packet[1] + 1

        output = "    continuous ranges: "
        first_time = True
        for start_point in start_points:
            if first_time:
                first_time = False
            else:
                output += ", "
            output += str(start_point) + " - " + str(start_points[start_point])

        print(output)
