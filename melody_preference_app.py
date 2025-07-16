{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 # melody_preference_app.py\
# 8\uc0\u47560 \u46356  \u46160  \u47708 \u47196 \u46356 \u47484  \u49373 \u49457 \u54644  \u49548 \u47532 \u47196  \u46308 \u47140 \u51452 \u44256 , \u49324 \u50857 \u51088  \u49440 \u53469 \u51012  SQLite DB\u50640  \u51200 \u51109 \
\
import streamlit as st\
import random\
import datetime\
import sqlite3\
import os\
import uuid\
from pydub.generators import Sine\
from pydub import AudioSegment\
import base64\
\
# \uc0\u51204 \u52404  \u49444 \u51221 \
TEMPO = 120  # BPM\
QUARTER_MS = int(60_000 / TEMPO)  # 1\uc0\u48516 \u51020 \u54364 (quarter note) ms\
DURATION_BEATS = \{1: 4, 2: 2, 4: 1, 8: 0.5, 16: 0.25\}\
DURATION_MS = \{denom: int(QUARTER_MS * beats) for denom, beats in DURATION_BEATS.items()\}\
\
# \uc0\u51020 \u50669 \u45824 : C3(130.81Hz) ~ B5(987.77Hz) \u50557  3\u50725 \u53440 \u48652 \
OCTAVE_NOTES = [\
    ('C3', 130.81), ('D3', 146.83), ('E3', 164.81), ('F3', 174.61), ('G3', 196.00), ('A3', 220.00), ('B3', 246.94),\
    ('C4', 261.63), ('D4', 293.66), ('E4', 329.63), ('F4', 349.23), ('G4', 392.00), ('A4', 440.00), ('B4', 493.88),\
    ('C5', 523.25), ('D5', 587.33), ('E5', 659.25), ('F5', 698.46), ('G5', 783.99), ('A5', 880.00), ('B5', 987.77)\
]\
NOTE_NAMES, NOTE_FREQS = zip(*OCTAVE_NOTES)\
\
# DB \uc0\u52488 \u44592 \u54868 \
DB_PATH = 'melody_preferences.db'\
conn = sqlite3.connect(DB_PATH, check_same_thread=False)\
c = conn.cursor()\
c.execute(\
    '''CREATE TABLE IF NOT EXISTS preferences (\
           id INTEGER PRIMARY KEY AUTOINCREMENT,\
           melody_a TEXT,\
           melody_b TEXT,\
           preferred TEXT,\
           timestamp TEXT\
       )'''\
)\
conn.commit()\
\
# \uc0\u47004 \u45924  \u47708 \u47196 \u46356  \u49373 \u49457  (8\u47560 \u46356 , 4/4\u48149 \u51088  \u44592 \u51456  \u52509  32\u48708 \u53944 )\
def generate_melody():\
    melody = []\
    total_beats = 32\
    while total_beats > 0:\
        denom = random.choice(list(DURATION_BEATS.keys()))\
        beats = DURATION_BEATS[denom]\
        if beats <= total_beats:\
            pitch = random.choice(NOTE_NAMES)\
            melody.append((pitch, denom))\
            total_beats -= beats\
    return melody\
\
# \uc0\u47708 \u47196 \u46356 \u47484  \u50724 \u46356 \u50724 (mp3)\u47196  \u48320 \u54872 \
def melody_to_audio(melody, filename):\
    audio = AudioSegment.silent(duration=0)\
    for note, denom in melody:\
        freq = NOTE_FREQS[NOTE_NAMES.index(note)]\
        tone = Sine(freq).to_audio_segment(duration=DURATION_MS[denom]).apply_gain(-3)\
        audio += tone\
    audio.export(filename, format='mp3')\
\
# \uc0\u50724 \u46356 \u50724  \u54540 \u47112 \u51060 \u50612  HTML\
def get_audio_html(file_path):\
    with open(file_path, 'rb') as f:\
        data = f.read()\
    b64 = base64.b64encode(data).decode()\
    return f'<audio controls src="data:audio/mp3;base64,\{b64\}"></audio>'\
\
# Streamlit UI\
st.title('\uc0\u55356 \u57269  Melody Preference Trainer')\
st.write('\uc0\u46160  \u47708 \u47196 \u46356 \u47484  \u46307 \u44256  \u45908  \u51339 \u51008  \u47708 \u47196 \u46356 \u47484  \u49440 \u53469 \u54616 \u49464 \u50836 . \u49440 \u53469  \u45936 \u51060 \u53552 \u45716  DB\u50640  \u51200 \u51109 \u46121 \u45768 \u45796 .')\
\
# \uc0\u47708 \u47196 \u46356  \u49373 \u49457  \u48143  \u54028 \u51068  \u51456 \u48708 \
melody_A = generate_melody()\
melody_B = generate_melody()\
file_A = f'melody_A_\{uuid.uuid4().hex\}.mp3'\
file_B = f'melody_B_\{uuid.uuid4().hex\}.mp3'\
melody_to_audio(melody_A, file_A)\
melody_to_audio(melody_B, file_B)\
\
col1, col2 = st.columns(2)\
with col1:\
    st.markdown('**Melody A**')\
    st.markdown(get_audio_html(file_A), unsafe_allow_html=True)\
with col2:\
    st.markdown('**Melody B**')\
    st.markdown(get_audio_html(file_B), unsafe_allow_html=True)\
\
# \uc0\u49440 \u53469  \u51200 \u51109  \u54632 \u49688 \
def save_preference(choice):\
    timestamp = datetime.datetime.now().isoformat()\
    c.execute(\
        "INSERT INTO preferences (melody_a, melody_b, preferred, timestamp) VALUES (?, ?, ?, ?)",\
        (str(melody_A), str(melody_B), choice, timestamp)\
    )\
    conn.commit()\
    # \uc0\u51076 \u49884  \u54028 \u51068  \u49325 \u51228 \
    for f in [file_A, file_B]:\
        try:\
            os.remove(f)\
        except:\
            pass\
    st.success(f'\uc0\u49440 \u53469  \u51200 \u51109 \u46120 : \{choice\}')\
    st.experimental_rerun()\
\
# \uc0\u48260 \u53948 \
col3, col4 = st.columns(2)\
with col3:\
    if st.button('A \uc0\u49440 \u53469 '):\
        save_preference('A')\
with col4:\
    if st.button('B \uc0\u49440 \u53469 '):\
        save_preference('B')\
\
# \uc0\u44592 \u47197  \u49688  \u54364 \u49884 \
c.execute('SELECT COUNT(*) FROM preferences')\
count = c.fetchone()[0]\
st.markdown('---')\
st.write(f'\uc0\u52509  \u49440 \u53469  \u49688 : \{count\}')}