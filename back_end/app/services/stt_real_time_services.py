import argparse, os 
import whisper
import faster_whisper
from queue import Queue
import speech_recognition as sr
from services.model_manager import *
def main():
    
    nearest_checkpoint = None
    
    data_queue = Queue()
    
    phrases_data_holder = bytes()
    
    recorder = sr.Recognizer()
    
    recorder.energy_threshold = args.energy_threshold
    
    recorder.dynamic_energy_threshold = False
    
    source = sr.Microphone(sample_rate = 16000)
    
    #load/model
    audio_model = WhisperModelManager("CACHE_DIR").load_model("MODEL_NAME")
    
    record_timeout = args.record_timeout
    phrase_timeout = args.phrase_timeout
    
    transcription = [" "]
    
    with source:
        recorder.adjust_for_ambient_noise(source)
        
    def record_callback(_, audio: sr.AudioData) ->None:
        data = audio.get_raw_data()
        data_queue.put(data)
        
    recorder.listen_in_background(source, record_callback, phrase_time_limit = record_timeout)
    
    print("Model Loaded.\n")
    
    while True:
        try:
            now = datatime.utcnow()
            
            if not data_queue.empty():
                phrase_complete = False
                
                if phrase_time and now - phrase_time > timedelta(seconds = phrase_timeout):
                    phrase_bytes = bytes()
                    phrase_complete = True
                    
                phrase_time = now
                
                audio_date = b"".join(data_queue.queue)
                data_queue.queue.clear()
                
                phrase_bytes += audio_data
                
                audio_np = np.frombuffer(phrase_bytes, dtype = np.int16).astype(np.float32) / 32768
                
                results = audio_model.transcribe(audio_np, fp16 = torch.cuda.is_available())
                text = results["text"].strip()
                
                if phrase_complete:
                    transcription.append(text)
                else:
                    transcription[-1] = text
                    
                os.system("cls" if os.name =="nt"ele "clear")
                for line in transcription:
                    print(line)
                    
                print("", end="", flush = True)

            else:
                sleep(0.25)
        except KeyboardInterrupt:
            break
    
    print("\n\nTranscription")
    for line in transcription:
        print(line)              
                
    