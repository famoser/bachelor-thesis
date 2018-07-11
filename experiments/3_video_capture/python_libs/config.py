import os


class StaticConfig:
    def __init__(self):
        self.root_dir = os.path.abspath(os.path.dirname("."))

        self.captures_dir = self.root_dir + "/" + "capture"

        self.analyze_dir = self.root_dir + "/" + "analyze"

        self.browsermob_dir = self.root_dir + "/" + "tools/browsermob-proxy-2.1.4"
        self.netflix_extension_path = self.root_dir + "/" + "tools/netflix-1080p-1.2.9.crx"

        self.config_dir = self.root_dir + "/" + "config"
        self.temp_dir = self.root_dir + "/" + "temp"

        self.attack_dir = self.root_dir + "/" + "attack"

        self.plot_dir = self.root_dir + "/" + "plot"
        self.log_dir = self.root_dir + "/" + "log"

        self.credentials_file_path = self.config_dir + "/" + "credentials.json"
        self.chrome_cookie_file_path = self.temp_dir + "/" + "chrome_cookies.pkl"
        self.firefox_cookie_file_path = self.temp_dir + "/" + "firefox_cookies.pkl"

        self.network_device = "wlp4s0"


class Inventory:
    def __init__(self):
        # cartoon
        self.family_guy = 80111454
        self.bojack_horseman = 70298930

        # action
        self.transformers = 70103763
        self.civil_war = 80088567

        # anime
        self.naruto = 70105699
        self.berserk = 70276596

        # documentaries
        self.minimalism = 80114460
        self.expedition_happiness = 80225528

        # netflix test video
        self.test_video = 80018499

        # further test videos
        self.reasons_why = 80117471
        self.classroom = 80045949
        self.classroom = 70047101
        self.transformers_dark = 70153859
        self.captain_america = 70293704
        self.bayblade = 70172977
        self.edge_of_tomorrow = 70298735
        self.drugs_inc = 70307424
        self.overlord = 80131661
        self.suits = 70283145
        self.mission_impossible = 70041961
        self.thor = 70276333
        self.avicii = 80097519
        self.flash = 80057443
        self.simpsons_movie = 70058029
        self.arto_of_design = 80093803
        self.cloverfiled = 80134431
        self.narcos = 80025313
        self.kein_mann = 80175421
        self.fantastic_4 = 70047104
        self.babylon = 70098331
        self.gone_too_soon = 80213148
        self.godzilla = 70297757
        self.ninja_turtle = 80005628
        self.catch_me_if_you_can = 60024942
        self.star_trek = 70101276
        self.defiant_ones = 80227519
        self.nothing_left = 80141340
        self.pacific_rim = 70267241
        self.spy_game = 60021779
        self.how_to_be_single = 80075563
        self.jack_the_giant_slayer = 70213512
        self.ibiza = 80195049
        self.lang_of_the_lost = 70104316
        self.django = 70230640
        self.top_gear = 70253790
        self.the_rain = 80154735
    def full_capture(self):
        return self.__dict__

    def get_name_of(self, id):
        inv_map = {v: k for k, v in self.__dict__.items()}
        return inv_map[id]

    def small_capture(self):
        return {"family": self.family_guy, "bojack": self.bojack_horseman}
