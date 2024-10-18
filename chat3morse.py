import socket
import re
import sounddevice as sd
import numpy as np
from scipy.signal import square

def text_to_morse(text):
    morse_code = {'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
                  'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
                  'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
                  'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
                  '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.'}

    morse_text = ''
    for char in text.upper():
        if char == ' ':
            morse_text += '  '  # two spaces between words
        elif char in morse_code:
            morse_text += morse_code[char] + ' '
        else:
            # Handle unrecognized characters (e.g., ignore them)
            pass

    return morse_text.strip()

def encode_morse_to_beats(morse):
    if not len(morse):
        return []
    beats = []
    for word in morse.split("  "):
        for char_pattern in word.split(" "):
            for symbol in char_pattern:
                beats.extend([True] * DURATIONS[symbol])
                beats.append(False)  # Beat between chars
            # Expand beatsep to charsep
            beats.extend([False] * 2)
        # Expand charsep to wordsep
        beats.extend([False] * 4)
    return beats

def generate_square_wave(beats, tone, dot_duration=0.080, sample_rate=44100, volume=0.5):
    dot_samples = int(dot_duration * sample_rate)
    dash_samples = int(3 * dot_duration * sample_rate)

    dot_tone = volume * square(2 * np.pi * tone * np.arange(dot_samples) / sample_rate, duty=0.5).astype(np.float32)
    dash_tone = volume * square(2 * np.pi * tone * np.arange(dash_samples) / sample_rate, duty=0.5).astype(np.float32)
    silent_sample = np.zeros(dot_samples, dtype=np.float32)

    waveform = np.zeros(sum(dot_samples if is_tone else len(silent_sample) for is_tone in beats), dtype=np.float32)
    index = 0

    for is_tone in beats:
        current_sample = dot_tone if is_tone else silent_sample
        waveform[index: index + len(current_sample)] = current_sample
        index += len(current_sample)

    return waveform

def play_waveform(waveform, sample_rate=44100):
    sd.play(waveform, samplerate=sample_rate)
    sd.wait()

# Constants
DURATIONS = {'.': 1, '-': 3}  # Morse code durations

server = 'irc.chat.twitch.tv'
port = 6667
# change these!!!!
nickname = 'xxx' # your own nickname on twitch
token = 'xxx' #generate an oauth code for twitch
channel = '#xxx' #the twitch channel you want to hear

sock = socket.socket()
sock.connect((server, port))
sock.send(f"PASS {token}\n".encode('utf-8'))
sock.send(f"NICK {nickname}\n".encode('utf-8'))
sock.send(f"JOIN {channel}\n".encode('utf-8'))

try:
    while True:
        print("Waiting to receive data from the socket")
        resp = sock.recv(2048).decode('utf-8')
        print("Received data from the socket")
        print(resp)

        # Extract messages and process Morse code
        if 'PRIVMSG' in resp:
            username, channel, message = re.search(r':(.*)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', resp).groups()
            print(f"Channel: {channel} \nUsername: {username} \nMessage: {message}")
            
            # Convert message to Morse code
            morse_code = text_to_morse(message)
            print(f"Morse code: {morse_code}")
            
            # Encode Morse code to beats and generate waveform
            beats = encode_morse_to_beats(morse_code)
            waveform = generate_square_wave(beats, tone=650, dot_duration=0.080, volume=0.2)  # tone is hz, dot_duration is speed.
            play_waveform(waveform)

        # Handle PING messages
        elif resp.startswith('PING'):
            ping_text = resp.split(':', 1)[1]
            print(f"Received PING: {ping_text}")
            # Respond with PONG
            sock.send(f"PONG {ping_text}\n".encode('utf-8'))

except KeyboardInterrupt:
    sock.close()
