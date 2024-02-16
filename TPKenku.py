#!/usr/env/bin python3
import re, threading
from time import sleep
import TouchPortalAPI as TP
import KenkuPy as Kenku
import json as json

APP_ID = "KenkuFMRemote"

__kill_thread = False

# Setup the callbacks and connection
TPClient = TP.Client(APP_ID)

def get_indexed_names(arr) :
    ret = []
    for i in range(0, len(arr)):
        ret.append(f'[{i}] {arr[i]}')
    return ret

def get_index_from_str(text) -> int:
    r = re.match(r'^\[(\d+)\]', text)
    return int(r.groups(1)[0])


def call_api(board, action = None, method = Kenku.METHOD_GET, data = {}, wait = False):
    r = Kenku.api(board.lower(), action, method, data)

def query_api():
    Kenku.query_status()
    track = Kenku.get_playing_track()
    TPClient.stateUpdate("Kenku_is_Playing", str(Kenku.get_playing()).capitalize())
    TPClient.stateUpdate("Kenku_Current_Track_Name", track['title'] if track is not None else "")
    TPClient.stateUpdate("Kenku_Current_Track_Id", track['id'] if track is not None else "")

    # Get the playing sounds
    soundData = Kenku.get_playing_sounds()
    sounds = []
    for sound in soundData:
        sounds.append(sound['id'])

    TPClient.stateUpdate("Kenku_Playing_Sounds", ",".join(sounds))
    

def query_loop():
    while not __kill_thread.is_set():
        Kenku.query_status()
        query_api()
        sleep(1)

def update_play_item(data):
    # User selected board type
    if ( data['listId'] == "BoardType" ):
        boardtype = data['values'][0]['value']

        boards = Kenku.get_board_list(boardtype)
        
        TPClient.choiceUpdateSpecific("PlaylistName", get_indexed_names([b.title for b in boards]), data['instanceId'] )
        TPClient.choiceUpdateSpecific("SoundId", [], data['instanceId'] )
            
    # User selected a playlist
    elif ( data['listId'] == "PlaylistName" ):
        # Get the 
        boardtype = data['values'][0]['value']
        pidx = get_index_from_str(data['values'][1]['value'])

        # Get the specific list of tracks
        tracklist = Kenku.get_board_track_list(boardtype, pidx)
            
        # Get the track list
        tracks = get_indexed_names([t.title for t in tracklist])
        TPClient.choiceUpdateSpecific("SoundId", tracks, data['instanceId'] )

def update_stop_sound(data):
    if ( data['listId'] == "StopSound_PlaylistName" ):
        if 'value' not in data['values'][0]:
            return
        pidx = get_index_from_str(data['values'][0]['value'])

        tracks = Kenku.get_board_track_list(Kenku.SOUNDBOARD, pidx)

        TPClient.choiceUpdateSpecific("SoundId", get_indexed_names([t.title for t in tracks]), data['instanceId'] )

@TPClient.on(TP.TYPES.onConnect)
def onConnect(data):
    global __kill_thread
    __kill_thread = threading.Event()
    
    settings = data['settings']
    for setting in settings:
        if 'Kenku Remote Address' in setting:
            Kenku.set_address(setting['Kenku Remote Address'])
    soundboards = Kenku.get_board_list(Kenku.SOUNDBOARD)
    boardnames = get_indexed_names([sb.title for sb in soundboards])
    if len(boardnames):
        TPClient.choiceUpdate("StopSound_PlaylistName", boardnames)

    threading.Thread(target=query_loop()).start()

@TPClient.on(TP.TYPES.onAction)
def onAction(data):
    if data['actionId'] == "Kenku_PlayItem":
        board = data['data'][0]['value']
        pidx = get_index_from_str(data['data'][1]['value'])
        titleidx = get_index_from_str(data['data'][2]['value'])

        # Get the playlist or soundboard
        playlist = Kenku.get_board(board, pidx)

        # get the id from the playlist
        if titleidx >= len(playlist.tracks):
            return
        
        call_api(board.lower(), Kenku.ACTION_PLAY, "PUT", data={"id":playlist.tracks[titleidx]}, wait=True)

    if data['actionId'] == "Kenku_PlayId":
        board = data['data'][0]['value']
        id = data['data'][1]['value']
        call_api(board.lower(), Kenku.ACTION_PLAY, "PUT", data={"id":id}, wait=True)

    elif data['actionId'] == "Kenku_ToggleSound":
        soundId = data['data'][0]['value']
        sounds = Kenku.get_playing_sounds()
        for sound in sounds:
            # If the sound is found, stop it.
            if sound['id'] == soundId:
                call_api(Kenku.SOUNDBOARD, Kenku.ACTION_STOP, Kenku.METHOD_PUT, data={"id":soundId})
                return
        
        # The sound was not playing so start it
        call_api(Kenku.SOUNDBOARD, Kenku.ACTION_PLAY, "PUT", data={"id":soundId})

    elif data['actionId'] == "Kenku_StopSound":
        playlistidx = get_index_from_str(data['data'][0]['value'])
        soundidx = get_index_from_str(data['data'][1]['value'])
        tracks = Kenku.get_board_track_list(Kenku.SOUNDBOARD, playlistidx)
        call_api(Kenku.SOUNDBOARD, Kenku.ACTION_STOP, Kenku.METHOD_PUT, data={"id":tracks[soundidx].id})
    
    elif data['actionId'] == "Kenku_StopAllSound":
        for s in Kenku.get_sounds():
            call_api(Kenku.SOUNDBOARD, Kenku.ACTION_STOP, Kenku.METHOD_PUT, data={"id":s.id})

    elif data['actionId'] == "Kenku_PauseTrack":
        call_api(Kenku.PLAYLIST, Kenku.ACTION_PAUSE, Kenku.METHOD_PUT, wait=True)

    elif data['actionId'] == "Kenku_ResumeTrack":
        call_api(Kenku.PLAYLIST, Kenku.ACTION_RESUME, Kenku.METHOD_PUT, wait=True)

    elif data['actionId'] == "Kenku_NextTrack":
        call_api(Kenku.PLAYLIST, Kenku.ACTION_NEXT, Kenku.METHOD_POST, wait=True)

    elif data['actionId'] == "Kenku_PrevTrack":
        call_api(Kenku.PLAYLIST, Kenku.ACTION_PREV, Kenku.METHOD_POST, wait=True)

    elif data['actionId'] == "Kenku_SetVolume":
        if not data['data'][0]['value'].isnumeric():
            return
        vol = float(data['data'][0]['value'])/100.0
        call_api(Kenku.PLAYLIST, Kenku.OPTION_VOLUME, Kenku.METHOD_PUT, data={"volume":vol}, wait=True)

    elif data['actionId'] == "Kenku_MutePlayback":
        state = data['data'][0]['value']
        call_api(Kenku.PLAYLIST, Kenku.OPTION_MUTE, Kenku.METHOD_PUT, data={"mute":state == "On"}, wait=True)

    elif data['actionId'] == "Kenku_Shuffle":
        state = data['data'][0]['value']
        call_api(Kenku.PLAYLIST, Kenku.OPTION_SHUFFLE, Kenku.METHOD_PUT, data={"shuffle":state == "On"}, wait=True)

    elif data['actionId'] == "Kenku_Repeat":
        state = data['data'][0]['value']
        call_api(Kenku.PLAYLIST, Kenku.OPTION_REPEAT, Kenku.METHOD_PUT, data={"repeat":state.lower()}, wait=True)

@TPClient.on(TP.TYPES.onListChange)
def onListChange(data):
    if ( data['pluginId'] != APP_ID ):
        return

    elif ( data['actionId'] == "Kenku_PlayItem" ):
        update_play_item(data)

    elif ( data['actionId'] == "Kenku_StopSound" ):
        update_stop_sound(data)

@TPClient.on(TP.TYPES.onSettingUpdate)
def onSettingUpdate(data):    
    for setting in data['values']:
        if 'Kenku Remote Address' in setting:
            Kenku.set_address(setting['Kenku Remote Address'])

@TPClient.on(TP.TYPES.onShutdown)
def onShutdown(data):
    __kill_thread.set()

# Begin the actual client connection.
try:
    TPClient.connect()
except:
    __kill_thread.set()