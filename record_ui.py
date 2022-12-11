from tkinter import *
import pyaudio
import wave
import threading
import os
from pydub import AudioSegment
from src.api import aai_upload_file, aai_transcribe

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
WAVE_OUTPUT_FILENAME = "recording.wav"


recording = False
my_thread = None

root = Tk()
root.title("NotePal recorder")
root.geometry("400x300")

def record_audio():
    global recording
    p = pyaudio.PyAudio()
    system_audio = False
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if (dev['name'] == 'Stereo Mix (Realtek(R) Audio)' and dev['hostApi'] == 0):
            audio_index = dev['index']
            system_audio = True

    if not system_audio:
        print("Stereo Mix device not found. System audio not available, continuing with microphone audio only. You can Enable Stereo Mix in audio settings.")

    if system_audio:
        audio_stream = p.open(format = FORMAT,
                        channels = CHANNELS,
                        rate = RATE,
                        input = True,
                        input_device_index=audio_index,
                        frames_per_buffer = CHUNK)

    mic_stream = p.open(format = FORMAT,
                    channels = CHANNELS,
                    rate = RATE,
                    input = True,
                    frames_per_buffer = CHUNK)

    print("* recording")
    frames = []
    frames2 = []

    while recording:
        if system_audio:
            data = audio_stream.read(CHUNK)
            frames.append(data)
        data2 = mic_stream.read(CHUNK)
        frames2.append(data2)

    print("* done recording")
    if system_audio:
        audio_stream.stop_stream()
        audio_stream.close()
    mic_stream.stop_stream()
    mic_stream.close()
    p.terminate()

    if system_audio:
        wf = wave.open('audio.wav', 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

    wf = wave.open('mic.wav', 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames2))
    wf.close()

    if system_audio:
        audio = AudioSegment.from_file("audio.wav", format="wav")
        os.remove('audio.wav')
    mic = AudioSegment.from_file("mic.wav", format="wav")
    os.remove('mic.wav')

    if system_audio:
        file = audio.overlay(mic, position=0)
    else:
        file = mic
    # export output to file
    file_handle = file.export(WAVE_OUTPUT_FILENAME, format="wav")


def send_audio_to_server():
    url = aai_upload_file(WAVE_OUTPUT_FILENAME)
    aai_transcribe(url)
    record_label.config(text="Recording sent to server")

def press_button_play():
    global recording
    global my_thread

    if not recording:
        recording = True
        record_label.config(text="Recording...")
        my_thread = threading.Thread(target=record_audio)
        my_thread.start()

def press_button_stop():
    global recording
    global my_thread

    if recording:
        recording = False
        record_label.config(text="Recording ready")



button_start = Button(root, text="RECORD", command=press_button_play)
button_start.place(x=50, y=50)

button_stop = Button(root, text="STOP", command=press_button_stop)
button_stop.place(x=50, y=150)

button_send = Button(root, text="SEND", command=send_audio_to_server)
button_send.place(x=50, y=200)

record_label = Label(root, text="")
record_label.place(x=100, y=100)


root.mainloop()