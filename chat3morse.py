import socket
import re
import sounddevice as sd
import numpy as np
from scipy.signal import square

# Morse code dictionary with predefined durations (dot: 1 unit, dash: 3 units)
MORSE_CODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
    'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
    'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.'
}

DURATIONS = {'.': 1, '-': 3}  # Durations in terms of dot units

def text_to_morse(text):
    morse_text = []
    for char in text.upper():
        if char == ' ':
            morse_text.append('')  # Space between words
        elif char in MORSE_CODE:
            morse_text.append(MORSE_CODE[char])
    return ' '.join(morse_text)

def encode_morse_to_beats(morse):
    beats = []
    for word in morse.split("  "):  # Splitting words
        for char_pattern in word.split(" "):  # Splitting letters
            for symbol in char_pattern:
                beats.extend([True] * DURATIONS[symbol])  # Add beat for symbol
                beats.append(False)  # Inter-symbol gap
            beats.extend([False] * 2)  # Gap between letters
        beats.extend([False] * 4)  # Gap between words
    return beats

def generate_square_wave(beats, tone, dot_duration=0.080, sample_rate=44100, volume=0.5):
    dot_samples = int(dot_duration * sample_rate)
    dash_samples = 3 * dot_samples
    silent_samples = dot_samples

    dot_wave = volume * square(2 * np.pi * tone * np.arange(dot_samples) / sample_rate, duty=0.5).astype(np.float32)
    dash_wave = volume * square(2 * np.pi * tone * np.arange(dash_samples) / sample_rate, duty=0.5).astype(np.float32)
    silence_wave = np.zeros(silent_samples, dtype=np.float32)

    waveform = []
    for is_tone in beats:
        waveform.append(dot_wave if is_tone else silence_wave)

    return np.concatenate(waveform)

def play_waveform(waveform, sample_rate=44100):
    sd.play(waveform, samplerate=sample_rate)
    sd.wait()

# Twitch IRC setup
server = 'irc.chat.twitch.tv'
port = 6667
nickname = 'xxx'
token = 'xxx'
channel = '#xxx'

sock = socket.socket()
sock.connect((server, port))
sock.send(f"PASS {token}\n".encode('utf-8'))
sock.send(f"NICK {nickname}\n".encode('utf-8'))
sock.send(f"JOIN {channel}\n".encode('utf-8'))

try:
    while True:
        resp = sock.recv(2048).decode('utf-8')
        
        if 'PRIVMSG' in resp:
            username, channel, message = re.search(r':(.*)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', resp).groups()
            print(f"Channel: {channel} \nUsername: {username} \nMessage: {message}")
            
            morse_code = text_to_morse(message)
            print(f"Morse code: {morse_code}")
            
            beats = encode_morse_to_beats(morse_code)
            waveform = generate_square_wave(beats, tone=650, dot_duration=0.040, volume=0.2)
            play_waveform(waveform)

        elif resp.startswith('PING'):
            sock.send(f"PONG :{resp.split(':')[1]}\n".encode('utf-8'))

except KeyboardInterrupt:
    sock.close()
