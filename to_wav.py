import os
import subprocess
def oga_to_wav_convert(oga_file: str, wav_file: str, wav_hz=16000):
    wav_file_dir = os.path.dirname(wav_file)
    if not os.path.exists(wav_file_dir):
        os.makedirs(wav_file_dir)
    oga_to_wav_comand = f'ffmpeg -i {oga_file} -ar {wav_hz} {wav_file}'
    subprocess.call(oga_to_wav_comand, shell=True)