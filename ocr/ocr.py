import cv2
import numpy as np

from time import time
from datetime import datetime

import win32gui
import win32ui
import win32con
import time
import os

from prettytable import PrettyTable
import csv
import string
import re
import difflib

import subprocess
import shlex
from concurrent.futures import ThreadPoolExecutor
from optparse import OptionParser

window_name = "Warframe"
screenshot_name = 'screenshot.bmp'

title = "Warframe Prime Helper"

w = 908
h = 70
x_offset = 521
y_offset = 400

box_w = 223
half_box_w = int(box_w/2)
crop_list = [(0, 27, w, h),  # the entire bottom
             (half_box_w, 0, half_box_w*3, h),  # assumes 3 relics
             (half_box_w*3, 0, half_box_w*5, h),
             (half_box_w*5, 0, half_box_w*7, h),
             (0, 0, box_w, h),  # assumes 2 or 4 relics
             (box_w, 0, box_w*2, h),
             (box_w*2, 0, box_w*3, h),
             (box_w*3, 0, w, h)]


interval = 1

skip_screenshot = True

price_csv = '..\\warframemarket\\allprice.csv'
ducats_csv = '..\\ducats\\ducats.csv'
primes_txt = '..\\ducats\\primes.txt'


# HSV bounds for getting rid of background
lower = np.array([0, 0, 197])
upper = np.array([180, 255, 255])

prices = {}
prime_dict = None
ducats = {}
primes = None

log = None
tesseract_log = None

printable = set(string.printable)

regex_alphabet = re.compile('[^a-zA-Z\s]')

datetime_format = "%Y-%m-%d %I.%M.%S%p"

def safe_cast(val, to_type,default=None):
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default

def init():
    global prime_dict, primes, prices, ducats, log, skip_screenshot, tesseract_log
    # make a dictionary of prices
    with open(price_csv, mode='r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)
        prices = {rows[0]: safe_cast(rows[1],int,0) for rows in reader}
    prices["Forma Blueprint"] = 0

    with open(ducats_csv, mode='r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)
        ducats = {rows[0]: safe_cast(rows[1],int,0) for rows in reader}
    ducats['Forma Blueprint'] = 0

    # make a dictionary of prime words
    with open(primes_txt, 'r', encoding='utf16') as f:
        prime_dict = [line.strip() for line in f]

    primes = [key for key, value in prices.items() if "Prime" in key and "Set" not in key]
    primes.append("Forma Blueprint")

    log = open('log.txt', 'a+')

    tesseract_log = open('tesseract.log', 'a+')
    os.system('cls')
    os.system('TITLE {}'.format(title))

    parser = OptionParser()
    parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False, help="uses the current screenshot for debug purposes")
    (options, args) = parser.parse_args()
    skip_screenshot = options.debug


def window_enumeration_handler(hwnd, top_windows):
    top_windows.append((hwnd, win32gui.GetWindowText(hwnd)))


def bring_to_front():
    top_windows = []
    win32gui.EnumWindows(window_enumeration_handler, top_windows)
    warframe_window = None
    for i in top_windows:
        if title in i[1]:
            win32gui.ShowWindow(i[0], 5)
            win32gui.SetForegroundWindow(i[0])
        #if window_name in i[1]:
        #    warframe_window = i[0]
    #win32gui.SetForegroundWindow(warframe_window)


def dict_match(text):
    words = text.split(" ")
    dict_words = []
    for word in words:
        close_words = difflib.get_close_matches(word, prime_dict, n=1)
        if len(close_words) != 0:
            dict_words.append(close_words[0])
        #else:
        #    dict_words.append('|')
    corrected = " ".join(dict_words)
    return corrected


def screenshot():
    if skip_screenshot:
        return cv2.imread("screenshot.bmp")
    hwnd = None
    while not hwnd:
        hwnd = win32gui.FindWindow(None, window_name)
        if not hwnd:
            time.sleep(15)
    rect = win32gui.GetWindowRect(hwnd)
    x = rect[0]
    y = rect[1]
    top = y_offset + y
    left = x_offset + x
    wDC = win32gui.GetWindowDC(hwnd)
    dcObj = win32ui.CreateDCFromHandle(wDC)
    cDC = dcObj.CreateCompatibleDC()
    dataBitMap = win32ui.CreateBitmap()
    dataBitMap.CreateCompatibleBitmap(dcObj, w, h)

    cDC.SelectObject(dataBitMap)
    cDC.BitBlt((0, 0), (w, h), dcObj, (left, top), win32con.SRCCOPY)

    # make numpy img
    bmpRGB = dataBitMap.GetBitmapBits(True)
    img = np.fromstring(bmpRGB, dtype='uint8')
    img.shape = (h, w, 4)

    # Free Resources
    dcObj.DeleteDC()
    cDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, wDC)
    win32gui.DeleteObject(dataBitMap.GetHandle())

    return cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)


def filter_img(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)

    return mask


def title_case(input_str):
    return string.capwords(input_str.lower())


def sanitize(input_str):
    return regex_alphabet.sub('', input_str)


tesseract_cmd = 'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe'


def run_tesseract(input_filename, output_filename_base, lang=None, boxes=False, config=None):
    '''
    runs the command:
        `tesseract_cmd` `input_filename` `output_filename_base`

    returns the exit status of tesseract, as well as tesseract's stderr output

    '''
    command = [tesseract_cmd, input_filename, output_filename_base]

    if lang is not None:
        command += ['-l', lang]

    if boxes:
        command += ['batch.nochop', 'makebox']

    if config:
        command += shlex.split(config)
    proc = subprocess.Popen(command, stderr=subprocess.PIPE)
    return (proc.wait(), proc.stderr.read())


def read_box(crop, filtered, read_primes, text, table, old_read_primes):
    input_name = 'temp\\crop_{}.bmp'.format(crop[0]+crop[1])
    output_name = 'temp\\tessout_{}'.format(crop[0]+crop[1])
    cv2.imwrite(input_name, filtered[crop[1]:crop[3], crop[0]:crop[2]])

    status, e = run_tesseract(input_name, output_name)
    cur_time = datetime.now().strftime(datetime_format)
    if status:
        log.write("{}: Failed to read image x={}\n".format(cur_time, crop[0]))
        log.flush()
        tesseract_log.write("{}: {}\n".format(cur_time, e.strip()))
        if not skip_screenshot:
            cv2.imwrite('screenshots/{}-error.bmp'.format(cur_time), filtered)
        return
    #else:
    #    log.write("{}: Succeeded reading image x={}\n".format(cur_time, crop[0]))
    #    log.flush()
        
    full_output_name = "{}.txt".format(output_name)
    
    with open(full_output_name, 'r') as file:
        ocr_output = file.read().strip()
    os.remove(full_output_name)
    # ocr_output = image_to_string(cropped_img)

    sanitized = sanitize(ocr_output)
    ocr_text = title_case(sanitized)
    text[crop[0]+crop[1]] = ocr_text
    dict_text = dict_match(ocr_text)
    update_table(dict_text, table, read_primes, old_read_primes)


def update_table(ocr_text, table, read_primes, old_read_primes):
    for p in primes:
        if p in ocr_text:
            if p not in read_primes:
                read_primes.append(p)
                if len(old_read_primes) == 0:
                    table.add_row([p, prices[p], ducats[p]])
                    os.system('cls')
                    print(table)
                    bring_to_front()


def image_identical(img1, img2):
    diff = cv2.subtract(img1, img2)
    return diff.mean() < 1


def read_screen(old_read_primes, old_filtered):
    screenshot_img = screenshot()
    filtered = filter_img(screenshot_img)

    if image_identical(filtered, old_filtered):
        return old_read_primes.copy(), filtered

    start = datetime.now()
    cur_time = start.strftime(datetime_format)

    # make formatted table
    table = PrettyTable()
    table.field_names = ['Prime', 'Plat','Ducats']
    table.sortby = 'Plat'

    read_primes = []
    text = {}

    # surround in try catch since threads don't receive keyboard interrupts
    try:
        with ThreadPoolExecutor(max_workers=len(crop_list)) as ex:
            for crop in crop_list:
                ex.submit(read_box, crop, filtered, read_primes, text, table, old_read_primes)
    except KeyboardInterrupt:
        return
    #for crop in crop_list:
    #    read_box(crop, filtered, read_primes, text, table, old_read_primes)
    #read_primes.sort()

    if len(read_primes) == 0 and len(old_read_primes) != 0:
        os.system('cls')
    #log.write("{}: OCR='{}' Primes={}\n".format(cur_time, text, read_primes))
    #log.flush()
    if read_primes != old_read_primes:
        if len(read_primes) != 0:
            if not skip_screenshot:
                cv2.imwrite('screenshots/{}.bmp'.format(cur_time), screenshot_img)
            end = datetime.now()
            duration = (end - start).total_seconds()
            log.write("{}: OCR='{}' Primes={} duration={}s\n".format(cur_time, text, read_primes, duration))
            log.flush()
    return read_primes, filtered


def main():
    init()
    old_read_primes = []
    old_filtered = 0
    while True:
        start = datetime.now()
        old_read_primes, old_filtered = read_screen(old_read_primes, old_filtered)
        end = datetime.now()
        duration = (end - start).total_seconds()
        if duration < interval:
            time.sleep(interval-duration)

main()
