import matplotlib.pyplot as plt
import hashlib
import sqlite3
import json

from python_libs.config import StaticConfig

config = StaticConfig()

# get sqlite connection
db_file_name = config.captures_dir + "/data.sqlite"
connection = sqlite3.connect(db_file_name)
cursor = connection.cursor()

# create single subplot
fig, axes = plt.subplots(1, 1)
movie_ids = ""

cursor.execute("SELECT DISTINCT movie_id FROM captures")
db_movies = cursor.fetchall()
library = []
for db_movie in db_movies:
    movie_id = db_movie[0]
    print("checking " + str(movie_id))

    cursor.execute("SELECT size, bitrate FROM "
                   "(SELECT DISTINCT MAX(p.range_end) as size, c.bitrate as bitrate "
                   "FROM packets p "
                   "INNER JOIN captures c ON c.id = p.capture_id "
                   "WHERE c.movie_id = ? AND p.body_size > 0 AND p.is_video = 1 "
                   "GROUP BY c.bitrate) "
                   "ORDER BY bitrate",
                   [movie_id])
    db_bitrate_levels = cursor.fetchall()

    x = []
    y = []
    local_library = []
    for db_bitrate_level in db_bitrate_levels:
        x.append(db_bitrate_level[1])
        y.append(db_bitrate_level[0])

        item = {"x": db_bitrate_level[1], "y": db_bitrate_level[0], "video_id": movie_id}
        library.append(item)
        local_library.append(item)

    # plot with label = movie_id
    axes.plot(x, y, label=str(movie_id), marker='.', linewidth=1)
    movie_ids += str(movie_id)

    # save json library
    with open(config.plot_dir + "/capture_bitrate_levels_" + str(movie_id) + ".json", 'w') as outfile:
        json.dump(local_library, outfile)

    cursor.execute("SELECT p.range_end - p.range_start as size, c.bitrate as bitrate "
                   "FROM packets p "
                   "INNER JOIN captures c ON c.id = p.capture_id "
                   "WHERE c.movie_id = ? AND p.body_size > 0 AND p.is_video = 1",
                   [movie_id])
    db_bitrate_levels = cursor.fetchall()
    local_library = []
    for db_bitrate_level in db_bitrate_levels:
        x.append(db_bitrate_level[1])
        y.append(db_bitrate_level[0])

        item = {"x": db_bitrate_level[1], "y": db_bitrate_level[0]}
        local_library.append(item)

    with open(config.plot_dir + "/capture_packets_" + str(movie_id) + ".json", 'w') as outfile:
        json.dump(local_library, outfile)

# place label to the right
plt.legend(loc=(1.04, 0))
plt.tight_layout()
plt.subplots_adjust(right=0.75)

# save
unique = hashlib.md5(movie_ids.encode()).hexdigest()
plt.savefig(config.plot_dir + "/capture_bitrate_levels_" + unique + ".png")
plt.close()

# save json library
with open(config.plot_dir + "/capture_bitrate_levels_" + unique + ".json", 'w') as outfile:
    json.dump(library, outfile)
