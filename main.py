# import speech_recognition as sr
#
# listener = sr.Recognizer()
# try:
#     with sr.Microphone() as source:
#         listener.adjust_for_ambient_noise(source)
#         print("listening")
#         voice = listener.listen(source)
#         command = listener.recognize_google(voice)
#         print(command)
#         # recognize speech using Sphinx
#         try:
#             print("Sphinx thinks you said " + listener.recognize_sphinx(voice))
#         except sr.UnknownValueError:
#             print("Sphinx could not understand audio")
#         except sr.RequestError as e:
#             print("Sphinx error; {0}".format(e))
# except:
#     pass

# Imports needed for Vosk voice-to-speech engine
import argparse
import queue
import sys
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# Imports needed for selenium controller
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

q = queue.Queue()
wakeWordList = ["hey computer", "a computer", "hate computer", "computer listen", "listen computer"]
# Set up firefox profile
profile = webdriver.FirefoxProfile(
    'C:/Users/ahojj/AppData/Roaming/Mozilla/Firefox/Profiles/wv9a3ewy.default-release')
profile.update_preferences()
desired = DesiredCapabilities.FIREFOX


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))


def detectWakeWord(userVoiceInput):
    for phrase in wakeWordList:
        if phrase in userVoiceInput:
            return True
    return False


def openYoutube():
    driver = webdriver.Firefox(firefox_profile=profile,
                               desired_capabilities=desired)
    searchTerm = "sterakdary"
    driver.get("https://www.youtube.com")
    search = driver.find_element(By.NAME, "search_query")
    search.send_keys(searchTerm)
    # videoElement = WebDriverWait(driver, timeout=3).until(search_query_typed, "Search query text not found")
    # Condition to use in until function. Check for search query to contain the search term
    waitCondition = EC.text_to_be_present_in_element_value((By.NAME, "search_query"), searchTerm)
    videoElement = WebDriverWait(driver, timeout=3).until(waitCondition, "Search query text not found")
    sleep(.3)
    driver.find_element(By.ID, "search-icon-legacy").click()
    videoElement = WebDriverWait(driver, timeout=4).until(
        lambda d: d.find_element(By.CSS_SELECTOR, 'div#contents ytd-item-section-renderer>div#contents a#thumbnail'), "Video thumbnail not found")
    videoElement.click()
    sleep(1)
    ActionChains(driver).send_keys("f").perform()


# START OF MAIN #
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    "-l", "--list-devices", action="store_true",
    help="show list of audio devices and exit")
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    "-f", "--filename", type=str, metavar="FILENAME",
    help="audio file to store recording to")
parser.add_argument(
    "-d", "--device", type=int_or_str,
    help="input device (numeric ID or substring)")
parser.add_argument(
    "-r", "--samplerate", type=int, help="sampling rate")
parser.add_argument(
    "-m", "--model", type=str, help="language model; e.g. en-us, fr, nl; default is en-us")
args = parser.parse_args(remaining)

try:
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, "input")
        # soundfile expects an int, sounddevice provides a float:
        args.samplerate = int(device_info["default_samplerate"])

    if args.model is None:
        model = Model(lang="en-us")
    else:
        model = Model(lang=args.model)

    if args.filename:
        dump_fn = open(args.filename, "wb")
    else:
        dump_fn = None

    with sd.RawInputStream(samplerate=args.samplerate, blocksize=8000, device=args.device,
                           dtype="int16", channels=1, callback=callback):
        print("#" * 80)
        print("Press Ctrl+C to stop the recording")
        print("#" * 80)

        rec = KaldiRecognizer(model, args.samplerate)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                print(rec.Result())
            else:
                result = rec.PartialResult()
                print(result)
                if detectWakeWord(result):
                    print("Big Win Big Win Big Win Big Win Big Win Big Win")
                    openYoutube()
                    rec.Reset()

            if dump_fn is not None:
                dump_fn.write(data)

except KeyboardInterrupt:
    print("\nDone")
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ": " + str(e))
