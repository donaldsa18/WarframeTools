import cv2
import numpy as np
import os
import pywintypes
#import pytesseract
tessdata_path = r"C:\Users\Anthony\VirtualBox VMs\Shared\warframe\WarframeTools\ocr\tesseract4win64-4.0-beta\tessdata"
if os.path.isdir('tessdata'):
    os.environ['TESSDATA_PREFIX'] = os.path.abspath(tessdata_path)
from tesserocr import PyTessBaseAPI, PSM, OEM
from PIL import Image
import re
import imutils
from datetime import datetime
import string
import difflib
import csv
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import win32gui
import win32ui
import win32con
from pathlib import Path


def borders(mask):
    rows = mask.sum(axis=0)
    cols = mask.sum(axis=1)

    nonzero_rows = np.nonzero(rows)
    nonzero_cols = np.nonzero(cols)

    y1 = max(nonzero_cols[0][0] - 1, 0)
    y2 = min(nonzero_cols[0][-1] + 1, mask.shape[0])
    x1 = max(nonzero_rows[0][0] - 1, 0)
    x2 = min(nonzero_rows[0][-1] + 1, mask.shape[1])

    return x1, y1, x2, y2


def sanitize(input_str):
    return regex_alphabet.sub('', input_str)


def sanitize_digit(input_str):
    return regex_digit.sub('', input_str)


primes_txt = '..\ducats\primes.txt'
with open(primes_txt, 'r') as f:
    prime_dict = [line.strip() for line in f]


def dict_match(text):
    words = text.split()
    dict_words = []
    for word in words:
        try_words = [word, word.replace("n", "ri"), word.replace("L", "T"), word.replace("t", "r")]
        for try_word in try_words:
            close_words = difflib.get_close_matches(try_word, prime_dict, n=1, cutoff=0.7)
            if len(close_words) != 0:
                dict_words.append(close_words[0])
                break
    corrected = " ".join(dict_words)
    return corrected


regex_alphabet = re.compile('[^a-zA-Z\s]')
regex_digit = re.compile('[^0-9]')

lower_white = np.array([0, 0, 219])
upper_white = np.array([180, 255, 255])


def find_numbers(cnts):
    numbers = {}
    last_y = col_h * 4
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        if y % col_h < 20 and x % col_w < 20 and last_y - y > col_h / 2:
            if 8 <= h <= 17:
                if w < 8:
                    x = x + w - 8
                    w = 8
                if h < 15:
                    y = y + h - 15
                    h = 15
                numbers[int(y / col_h)] = (x, y, w, h)
                last_y = y
    return numbers


digit_imgs = []


def init_digit_imgs():
    for i in range(2, 10):
        img_name = 'digits/{}.bmp'.format(i)
        if Path(img_name).is_file():
            img = cv2.imread(img_name, cv2.IMREAD_GRAYSCALE)
            digit_imgs.append(img)
        else:
            digit_imgs.append(None)


h_max = 70
w_max = 60
datetime_format = "%Y-%m-%d %I.%M.%S%p"
pad = 2

tesseract_api = PyTessBaseAPI(tessdata_path, "eng")

def extract_number(hsv, n, x, y, w, h):
    # get the number by itself
    crop = hsv[y - pad:y + h + pad, x - pad:x + w + pad]
    # cv2.imwrite('digit_{}_firstcrop.bmp'.format(n), crop)
    # resize
    newW = crop.shape[1] * 4
    newH = crop.shape[0] * 4
    resized = cv2.resize(crop, (int(newW), int(newH)))
    mask_resized = cv2.inRange(resized, lower_white, upper_white)

    # crop again
    x1, y1, x2, y2 = borders(mask_resized)
    mask_cropped = mask_resized[y1:y2, x1:x2]
    # cv2.imwrite('digit_{}_secondcrop.bmp'.format(n), mask_cropped)

    # add a border around the image
    top = 1 + h_max - (y2 - y1)
    right = 1 + w_max - (x2 - x1)
    if top < 1:
        print("Error: h={}".format(y2 - y1))
    if right < 1:
        print("Error: w={}".format(x2 - x1))
    mask_border = cv2.copyMakeBorder(mask_cropped, 1 + h_max - (y2 - y1), 1, 1, 1 + w_max - (x2 - x1),
                                     cv2.BORDER_CONSTANT, value=[0, 0, 0])

    inv = cv2.bitwise_not(mask_border)

    return inv


def combine_imgs(num_imgs):
    sorted_keys = sorted(num_imgs.keys())
    max_height = max(img.shape[0] for img in num_imgs.values())
    imgs_list = []
    for key in sorted_keys:
        cur_height = num_imgs[key].shape[0]
        if cur_height != max_height:
            img = cv2.copyMakeBorder(num_imgs[key], max_height - cur_height, 0, 0, 0, cv2.BORDER_CONSTANT,
                                     value=[255, 255, 255])
            imgs_list.append(img)
        else:
            imgs_list.append(num_imgs[key])
    combined_digits = np.concatenate(imgs_list, axis=1)
    # cv2.imwrite('combined_digits.bmp', combined_digits)
    return combined_digits


def match_img(num_imgs):
    num_results = {x: 1 for x in range(0, 4)}
    for key in num_imgs.keys():
        poss = []
        for i in range(0, 8):
            # check if the image is there
            if num_imgs[key] is not None and digit_imgs[i] is not None:
                if digit_imgs[i].shape != num_imgs[key].shape:
                    print("Error: number {} {} has different dimensions from {} {}".format(i, digit_imgs[i].shape, key,
                                                                                           num_imgs[key].shape))
                diff = cv2.subtract(digit_imgs[i], num_imgs[key])
                avg = diff.mean()
                poss.append((i, avg))
        poss.sort(key=lambda tup: tup[1])
        num_results[key] = poss[0][0] + 2
    return num_results


def title_case(input_str):
    return string.capwords(input_str.lower())


price_csv = '..\\warframemarket\\allprice.csv'
with open(price_csv, mode='r') as csv_file:
    reader = csv.reader(csv_file)
    next(reader)
    primes = [row[0] for row in reader if "Prime" in row[0] and "Set" not in row[0]]


def parse_primes(dict_text):
    read_primes_start = []
    read_primes_end = []
    added_prime = True

    while added_prime and len(dict_text) > 0:
        added_prime = False
        for p in primes:
            if dict_text.startswith(p):
                read_primes_start.append(p)
                dict_text = dict_text.replace("{} Blueprint".format(p), '')
                dict_text = dict_text.replace(p, '').strip()
                added_prime = True

            if dict_text.endswith(p):
                read_primes_end.insert(0, p)
                dict_text = dict_text.replace("{} Blueprint".format(p), '')
                dict_text = dict_text.replace(p, '').strip()
                added_prime = True

    if len(dict_text) > 0:
        read_primes_start.append("ERROR: {}".format(dict_text))

    return read_primes_start + read_primes_end


common_errors = {
    'ERROR: Kogake Prime': 'Kogake Prime Boot',
    'ERROR: Silva Aegis Prime Blade': 'Silva & Aegis Prime Blade',
    'ERROR: Silva Aegis Prime Blueprint': 'Silva & Aegis Prime Blueprint',
    'ERROR: Kavasa Prime Buckle': 'Kavasa Prime Buckle'
}


def read_col(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_white, upper_white)
    # cv2.imwrite('mask.bmp',mask)
    cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    numbers = find_numbers(cnts)

    num_imgs = {n: extract_number(hsv, n, x, y, w, h) for n, (x, y, w, h) in numbers.items()}

    num_results = match_img(num_imgs)

    img_pil = Image.fromarray(mask)
    tesseract_api.SetImage(img_pil)
    ocr_str = tesseract_api.GetUTF8Text()
    sanitized = sanitize(ocr_str)
    dict_text = dict_match(sanitized)
    read_primes = parse_primes(dict_text)

    print("{} numbers seen {} primes seen".format(len(num_imgs), len(read_primes)))
    lock.acquire()
    for i in range(0, len(read_primes)):
        if read_primes[i] not in inventory:
            if read_primes[i] in common_errors:
                read_primes[i] = common_errors[read_primes[i]]
            line = "{},{}\n".format(read_primes[i], num_results[i])
            inventory_csv.write(line)
            inventory[read_primes[i]] = num_results[i]
    lock.release()


def screenshot():
    w = 1266
    h = 724
    x_offset = 107
    y_offset = 226

    hwnd = None
    while not hwnd:
        hwnd = win32gui.FindWindow(None, "Warframe")
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

    bmpRGB = dataBitMap.GetBitmapBits(True)
    img = np.frombuffer(bmpRGB, dtype='uint8')
    img.shape = (h, w, 4)
    cv2.imwrite("primescreenshot.bmp", img)

    # Free Resources
    dcObj.DeleteDC()
    cDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, wDC)
    win32gui.DeleteObject(dataBitMap.GetHandle())
    return img


# cv2.namedWindow('primes', cv2.WINDOW_NORMAL)

col_w = 185
col_h = 189
inventory = {}
lock = None
reached_end = False
inventory_csv = open('inventory_gen.csv', 'w')
inventory_csv.write("Have,Quantity\n")
lock = threading.Lock()

last_move_time = None
last_y = 0
last_row = None
order = 1


def check_screenshot():
    global last_row, last_move_time, last_y, order
    new_screenshot = screenshot()
    if last_row is None:
        last_row = new_screenshot[col_h * 3:, :]
        last_move_time = datetime.now()
        return True, new_screenshot
    else:
        result = cv2.matchTemplate(last_row, new_screenshot, cv2.TM_SQDIFF_NORMED)
        mn, _, mnLoc, _ = cv2.minMaxLoc(result)
        # print("R={} loc={}".format(mn, mnLoc))
        y1 = mnLoc[1] + col_h
        y2 = y1 + 2 * col_h
        if last_y != y1:
            last_move_time = datetime.now()
            last_y = y1
        if mnLoc[1] <= col_h:
            print("found next row")
            last_row = new_screenshot[mnLoc[1] + col_h * 2:mnLoc[1] + col_h * 4, :]
            order += 1
            return True, new_screenshot[y1:y2, :]
        elif (datetime.now() - last_move_time).total_seconds() > 1 and order > 1:
            return False, new_screenshot[y1:, :]
    return True, None


def main():
    init_digit_imgs()

    # surround in try catch since threads don't receive keyboard interrupts
    num_threads = 7

    keep_going = True
    try:
        with ThreadPoolExecutor(max_workers=num_threads) as ex:
            while keep_going:
                keep_going, prime_img = check_screenshot()
                if prime_img is not None:
                    for img_x in range(0, prime_img.shape[1], 185):
                        img = prime_img[:, img_x:img_x + col_w]
                        ex.submit(read_col, img)
                time.sleep(0.1)
    except KeyboardInterrupt as e:
        print(e)


main()
