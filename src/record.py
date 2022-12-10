import pyaudio
import wave
from pydub import AudioSegment
import os

def record():
    p = pyaudio.PyAudio()

    audio_index = -1
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if (dev['name'] == 'Stereo Mix (Realtek(R) Audio)' and dev['hostApi'] == 0):
            audio_index = dev['index']

    assert audio_index != -1, "Stereo Mix device not found. Enable Stereo Mix in audio settings."

    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = "output.wav"

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

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = audio_stream.read(CHUNK)
        data2 = mic_stream.read(CHUNK)
        frames.append(data)
        frames2.append(data2)

    print("* done recording")

    audio_stream.stop_stream()
    mic_stream.stop_stream()
    audio_stream.close()
    mic_stream.close()
    p.terminate()

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

    audio = AudioSegment.from_file("audio.wav", format="wav")
    mic = AudioSegment.from_file("mic.wav", format="wav")
    os.remove('audio.wav')
    os.remove('mic.wav')

    overlay = audio.overlay(mic, position=0)
    # export output to file
    file_handle = overlay.export(WAVE_OUTPUT_FILENAME, format="wav")