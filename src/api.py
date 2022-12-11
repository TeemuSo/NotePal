import time
import requests
import openai
import os
import pandas as pd
import numpy as np

ASSEMBLYAI_APIKEY = os.getenv('ASSEMBLYAI_APIKEY')
OPENAI_APIKEY = os.getenv('OPENAI_APIKEY')
AUDIO_UPLOAD_URL = 'https://api.assemblyai.com/v2/upload'
TRANSCRIPTION_URL = "https://api.assemblyai.com/v2/transcript/"

def TRANSCRIPTION_RESULTS_URL(
    audio_id): return f"https://api.assemblyai.com/v2/transcript/{audio_id}"


GPT_PROMPT = "Summarize in markdown: \n"

if ASSEMBLYAI_APIKEY:
    print(f"ASSEMBLY AI API key: {ASSEMBLYAI_APIKEY}")

if OPENAI_APIKEY:
    print(f"OPENAI API key: {OPENAI_APIKEY}")


headers = {
    "authorization": ASSEMBLYAI_APIKEY,
    "content-type": "application/json"
}

def yield_file_data(filename, chunk_size=5242880):
    with open(filename, 'rb') as _file:
        while True:
            data = _file.read(chunk_size)
            if not data:
                break
            yield data
            
def aai_upload_file(filename):
    """Requires filename pointing to local file.
    Returns url for accessing the """
    start_t = time.time()
    response = requests.post(AUDIO_UPLOAD_URL,
                        headers=headers,
                        data=yield_file_data(filename))

    # Save url for audio
    audio_url = response.json()['upload_url']
    end_t = time.time()
    # print(f"File uploaded in {(end_t - start_t) / 1000}s")
    
    return audio_url

def openai_gpt(prompt):
    openai.api_key = OPENAI_APIKEY

    response = openai.Completion.create(
      model="text-davinci-003",
      prompt=prompt,
      temperature=0.7,
      max_tokens=256,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    
    # We could ask multiple suggestions from the GPT
    choice = response['choices'][0]
    
    return choice['text']

def _parse_aai_results(response):
    """" Parse results that AAI returns """
    response_json = response.json()
    text     = response_json['text']
    summary  = response_json['summary']
    speakers = response_json['utterances']
    chapters = response_json['chapters']
    
    # See how long each speaker has spoken
    speaker_durations = [(seg['speaker'], (seg['end'] - seg['start']) / 1000)
     for seg in speakers]
 
    total_durations = pd.DataFrame(speaker_durations).groupby(0).sum().values # Group-by speaker, and sum the speaker durations

    # If both have spoken over 30 seconds, then add diarization
    if np.all(total_durations > 30):
        # Add speakers to the conversation
        diarization = [f"{x['speaker']}: {x['text']}" for x in speakers]
    else:
        diarization = None
    return text, summary, diarization, chapters

def aai_get_results(transcription_id):
    """Get AAI results.
    
    Returns:
        text : string 
        """
    endpoint = TRANSCRIPTION_RESULTS_URL(transcription_id)
    response = requests.get(endpoint, headers=headers)
    
    while response.json()['status'] != "completed":
        time.sleep(0.5)
        response = requests.get(endpoint, headers=headers)
    
    text, summary, speaker_texts, chapters = _parse_aai_results(response)
    
    return text, summary, speaker_texts, chapters
    
def aai_transcribe(audio_url):
    json = {
        "audio_url": audio_url,
#         "summarization": True, # Only either summarization or autochapters
        "summary_model": "informative",
        "summary_type": "bullets",
        "speaker_labels": True,
        "auto_chapters": True
    }

    response = requests.post(TRANSCRIPTION_URL, json=json, headers=headers)
    transcription_id = response.json()['id']
    return response, transcription_id


def get_transcripts():
    response = requests.get(TRANSCRIPTION_URL, headers=headers)
    return response.json()['transcripts']

def get_transcript_results(transcript):
    resource_url = transcript['resource_url']
    results = requests.get(resource_url, headers=headers)
    raw_text, aai_summary, diarization, chapters = _parse_aai_results(results)
    openai_summary = openai_gpt(GPT_PROMPT + raw_text)

    return raw_text, aai_summary, openai_summary, diarization, chapters

def transcribe(mic_filename, audio_upload_filename, video_upload_filename):
    # Choose, which file should we transcribe
    # Microphone has highest priority, incase we add both files.
    if video_upload_filename != None:
        filename = video_upload_filename
    if audio_upload_filename != None:
        filename = audio_upload_filename
    if mic_filename != None:
        filename = mic_filename
            
    audio_url = aai_upload_file(filename)
    response, transcription_id = aai_transcribe(audio_url)
    raw_text, aai_summary, diarization, chapters = aai_get_results(transcription_id)
    
    if diarization:
        gpt_prompt = diarization
    else:
        gpt_prompt = raw_text
        diarization = "# Couldn't diarize. Add at least 30 seconds of speech for each participant."
    # Text processing
    openai_summary = openai_gpt(GPT_PROMPT + gpt_prompt)
    
    return raw_text, aai_summary, openai_summary, diarization, chapters