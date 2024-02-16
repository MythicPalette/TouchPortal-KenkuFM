import requests, json

#region classes
class Board:
    def __init__(self, json) -> None:
        self.id = json["id"]
        self.title = json["title"]
        self.background = json['background']

        self.tracks = []
        if "tracks" in json:
            for track in json['tracks']:
                self.tracks.append(track)
        
        if "sounds" in json:
            for track in json['sounds']:
                self.tracks.append(track)


class Sound:
    def __init__(self, json) -> None:
        self.id = json['id']
        self.title = json['title']
        self.url = json['url']

        # Only sound files have these.
        if 'loop' in json:
            self.loop = json['loop']
            self.volume = json['volume']
            self.fadeIn = json['fadeIn']
            self.fadeOut = json['fadeOut']
#endregion

#region Constants
PLAYLIST = "playlist"
SOUNDBOARD = "soundboard"

ACTION_PLAY = "play"

ACTION_PAUSE = "playback/pause"
ACTION_RESUME = "playback/play"
ACTION_NEXT = "playback/next"
ACTION_PREV = "playback/previous"
ACTION_STOP = "stop"

OPTION_MUTE = "playback/mute"
OPTION_VOLUME = "playback/volume"
OPTION_SHUFFLE = "playback/shuffle"
OPTION_REPEAT = "playback/repeat"


QUERY_PLAYBACK = "playback"

HEADER = {'Content-Type': 'application/json'}

METHOD_GET = "GET"
METHOD_PUT = "PUT"
METHOD_POST = "POST"
#endregion

#region Config
__user_config_address = "127.0.0.1:3333"
#endregion

__state_playlist_playing = False
__state_volume = 1.0
__state_muted = False
__state_shuffle = False
__state_repeat = "off"
__state_playback_track = None
__state_playback_sounds = []

__tracklist = []
__soundlist = []
__playlists = []
__soundboards = []

def api(board, action, method = METHOD_GET, data = {}, version = "v1"):
    address = f'http://{__user_config_address}/{version}/{board}'
    if action is not None:
        address += f"/{action}"
    try:        
        s_data = json.dumps(data)
        if method == METHOD_GET:
            return requests.get(address, headers=HEADER)
        
        elif method == METHOD_PUT:
            return requests.put(address, headers=HEADER, data=s_data)

        elif method == METHOD_POST:
            return requests.post(address, headers=HEADER, data=s_data)
    except:
        print(f"Unable to reach address {address}")
    
def query_status():
    global __tracklist
    global __playlists
    global __soundlist
    global __soundboards
    global __state_playlist_playing
    global __state_volume
    global __state_muted
    global __state_shuffle
    global __state_repeat
    global __state_playback_track
    global __state_playback_sounds

    try:
        # Get the playlist info
        j = json.loads(api(PLAYLIST, None, METHOD_GET).text)

        __playlists = [Board(pl) for pl in j['playlists']]
        __tracklist = [Sound(t) for t in j['tracks']]

        # Get the soundboard info
        j = json.loads(api(SOUNDBOARD, None, METHOD_GET).text)

        __soundboards = [Board(sb) for sb in j['soundboards']]
        __soundlist = [Sound(s) for s in j['sounds']]

        # Get the playback state of the playlist tracks
        j = json.loads(api(PLAYLIST, QUERY_PLAYBACK, METHOD_GET).text)

        __state_playlist_playing = j['playing']
        __state_volume = j['volume']
        __state_muted = j['muted']
        __state_shuffle = j['shuffle']
        __state_repeat = j['repeat']

        if 'track' in j:
            __state_playback_track = j['track']

        # Get the playback state of the soundboard sounds
        j = json.loads(api(SOUNDBOARD, QUERY_PLAYBACK, METHOD_GET).text)
        __state_playback_sounds = j['sounds']

    except:
        pass

def set_address(address) -> None:
    global __user_config_address
    __user_config_address = address

def get_playing() -> bool:
    return __state_playlist_playing

def get_volume() -> bool:
    return __state_volume

def get_shuffle() -> bool:
    return __state_shuffle

def get_repeat() -> bool:
    return __state_repeat

def get_muted() -> bool:
    return __state_muted

def get_playing_track() -> dict:
    return __state_playback_track

def get_playing_sounds() -> dict:
    return __state_playback_sounds

def get_board_list(type) -> list:
    return __playlists if type.lower() == PLAYLIST else __soundboards

def get_board(type, boardidx) -> Board:
    return get_board_list(type)[boardidx]

def get_board_track_list(type, boardidx):
    board = get_board(type, boardidx)
    tlist = get_tracks() if type.lower() == PLAYLIST else get_sounds()
    ret = []
    for t in board.tracks:
        for tt in tlist:
            if tt.id == t:
                ret.append(tt)
                break

    return ret

def get_sounds():
    return __soundlist

def get_tracks():
    return __tracklist