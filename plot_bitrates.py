import matplotlib.pyplot as plt
import hashlib
import sqlite3
import json

from python_libs.config import StaticConfig, Inventory

config = StaticConfig()
inventory = Inventory()

# get sqlite connection
db_file_name = config.captures_dir + "/data.sqlite"
connection = sqlite3.connect(db_file_name)
cursor = connection.cursor()

cursor.execute("SELECT DISTINCT movie_id, bitrate FROM captures ORDER BY movie_id")
db_movies = cursor.fetchall()
total_body_sizes = {}
movie_counter = 0
last_movie_id = 0
x = []
y = []
for db_movie in db_movies:
    movie_id = db_movie[0]
    if movie_id != last_movie_id:
        last_movie_id = movie_id
        movie_counter += 1

    bitrate = db_movie[1]
    x.append(movie_counter)
    y.append(bitrate)

# prepare plot
fig = plt.figure(figsize=(10, 10))
plt.xlabel("movies")
plt.ylabel("bitrates")
plt.plot(x, y, label=str("bitrates per movie"), marker='.', linewidth=0)

# save
plt.savefig(config.plot_dir + "/bitrates.png", dpi=300)
plt.close()
print("generated plot")
