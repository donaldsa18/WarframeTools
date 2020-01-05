from PyQt5.QtWidgets import QApplication, QTableWidget, QWidget, QVBoxLayout, QLabel, QAbstractItemView, QHBoxLayout, \
    QSlider, QGridLayout, QGroupBox, QCheckBox, QHeaderView, QPushButton, QProgressBar, QTableWidgetItem, QDialog
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, QTimer, QDateTime
import qdarkstyle
from functools import partial
from ocr import OCR
from api import APIReader
from market_api import MarketReader
import time
import threading
from threading import Lock
from datetime import datetime

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()

        self.icon_path = 'warframe.ico'

        #self.layout = QVBoxLayout()
        self.market_api = None


        self.image_label = QLabel()
        image = QPixmap('temp\\crop_27.bmp')
        self.image_label.setPixmap(image)

        self.image_label2 = QLabel()
        self.image_label2.setPixmap(image)

        bot_layout = QHBoxLayout()
        warframe_height = 1080
        warframe_width = 1920

        self.table = QTableWidget(7, 3)
        self.table.setHorizontalHeaderLabels(['Prime Part', 'Plat', 'Ducats'])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.mission_table = QTableWidget(30, 4)
        self.mission_table.setHorizontalHeaderLabels(['Relic', 'Mission', 'Type', 'Time Left'])
        self.mission_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        mission_header = self.mission_table.horizontalHeader()

        for i in range(4):
            mission_header.setSectionResizeMode(i, QHeaderView.Interactive)
        mission_header.resizeSection(0, 55)
        mission_header.resizeSection(1, 150)
        mission_header.resizeSection(2, 90)
        mission_header.resizeSection(3, 60)
        self.mission_table.setFixedWidth(405)

        self.slider_names = ['x', 'y', 'w', 'h', 'v1', 'v2', 'Screencap (s)', 'Fissure (s)', 'API Threads']
        self.sliders = {x: QSlider(Qt.Horizontal) for x in self.slider_names}
        slider_labels = {x: QLabel(x) for x in self.slider_names}
        self.slider_default_values = {'x': 521, 'y': 400, 'w': 908, 'h': 70, 'v1': 197, 'v2': 180, 'Screencap (s)': 1, 'Fissure (s)': 30, 'API Threads':4}
        self.slider_values = {x: QLabel(str(self.slider_default_values[x])) for x in self.slider_names}

        self.sliders['x'].setMaximum(int(warframe_width / 2))
        self.sliders['y'].setMaximum(int(warframe_height / 2))
        self.sliders['w'].setMaximum(warframe_width)
        self.sliders['h'].setMaximum(warframe_height)
        self.sliders['v1'].setMaximum(255)
        self.sliders['v2'].setMaximum(255)
        self.sliders['Screencap (s)'].setMaximum(5)
        self.sliders['Screencap (s)'].setMinimum(1)
        self.sliders['Fissure (s)'].setMaximum(60)
        self.sliders['Fissure (s)'].setMinimum(10)
        self.sliders['API Threads'].setMaximum(10)
        self.sliders['API Threads'].setMinimum(2)
        for slider_name in self.slider_names:
            if len(slider_name) <= 2:
                self.sliders[slider_name].setMinimum(0)
            self.sliders[slider_name].setSingleStep(1)
            self.slider_values[slider_name].setFixedWidth(35)
            self.sliders[slider_name].setValue(self.slider_default_values[slider_name])

        self.is_slider_max_set = False

        self.pref_grid = QGridLayout()
        self.pref_grid.setColumnStretch(3, 7)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_button)
        self.is_paused = False

        self.plat_check_box = QCheckBox("Prefer platinum")
        self.plat_check_box.setChecked(True)
        #self.pref_grid.addWidget(self.plat_check_box, 1, 0, 1, 3)

        update_layout = QGridLayout()
        update_layout.setColumnStretch(4, 2)
        update_layout.setAlignment(Qt.AlignTop)
        update_layout.setContentsMargins(0, 0, 0, 0)

        self.update_prices_button = QPushButton("Update Prices")
        self.update_prices_button.clicked.connect(self.update_prices)
        self.update_prices_progress = QProgressBar()
        self.update_prices_progress.setFixedWidth(110)
        self.update_prices_progress.setRange(0, 100)
        update_layout.addWidget(self.update_prices_button, 0, 0)
        update_layout.addWidget(self.update_prices_progress, 0, 1)

        self.update_ducats_button = QPushButton("Update Ducats")
        self.update_ducats_button.clicked.connect(self.update_ducats)
        self.update_ducats_progress = QProgressBar()
        self.update_ducats_progress.setFixedWidth(110)
        self.update_ducats_progress.setRange(0, 100)
        update_layout.addWidget(self.update_ducats_button, 1, 0)
        update_layout.addWidget(self.update_ducats_progress, 1, 1)

        last_updated_prices_label = QLabel("Prices Updated")
        self.last_updated_prices_value = QLabel("1/1/2020")
        update_layout.addWidget(last_updated_prices_label, 2, 0)
        update_layout.addWidget(self.last_updated_prices_value, 2, 1)

        last_updated_ducats_label = QLabel("Ducats Updated")
        self.last_updated_ducats_value = QLabel("1/1/2020")
        update_layout.addWidget(last_updated_ducats_label, 3, 0)
        update_layout.addWidget(self.last_updated_ducats_value, 3, 1)

        num_parts_label = QLabel("Prime Parts")
        self.num_parts_value = QLabel("100")
        update_layout.addWidget(num_parts_label, 4, 0)
        update_layout.addWidget(self.num_parts_value, 4, 1)

        latest_item_label = QLabel("Latest Prime")
        self.latest_item_value = QLabel("Ivara Prime")
        update_layout.addWidget(latest_item_label, 5, 0)
        update_layout.addWidget(self.latest_item_value, 5, 1)

        update_box = QGroupBox("Updates")
        update_box.setLayout(update_layout)

        crop_grid = QGridLayout()
        crop_grid.setColumnStretch(3, 4)
        crop_grid.setAlignment(Qt.AlignTop)
        crop_grid.setContentsMargins(0, 0, 0, 0)
        for i in range(4):
            slider_name = self.slider_names[i]
            crop_grid.addWidget(slider_labels[slider_name], i, 0)
            crop_grid.addWidget(self.slider_values[slider_name], i, 1)
            crop_grid.addWidget(self.sliders[slider_name], i, 2)

        crop_box = QGroupBox("Crop Parameters")
        crop_box.setLayout(crop_grid)

        filter_grid = QGridLayout()
        filter_grid.setColumnStretch(3, 2)
        filter_grid.setAlignment(Qt.AlignTop)
        filter_grid.setContentsMargins(0, 0, 0, 0)
        for i in range(2):
            slider_name = self.slider_names[i+4]
            filter_grid.addWidget(slider_labels[slider_name], i, 0)
            filter_grid.addWidget(self.slider_values[slider_name], i, 1)
            filter_grid.addWidget(self.sliders[slider_name], i, 2)

        filter_box = QGroupBox("Filter Parameters")
        filter_box.setLayout(filter_grid)

        self.move_to_top_check_box = QCheckBox("Bring to front")
        self.move_to_top_check_box.setChecked(True)
        self.move_to_top_check_box.stateChanged.connect(self.toggle_move_to_top)

        other_layout = QVBoxLayout()
        other_layout.setAlignment(Qt.AlignTop)
        other_layout.setContentsMargins(0, 0, 0, 0)
        other_layout.addWidget(self.move_to_top_check_box)
        other_layout.addWidget(self.pause_button)

        other_box = QGroupBox("Other")
        other_box.setLayout(other_layout)

        settings_layout_1 = QVBoxLayout()
        settings_layout_1.addWidget(crop_box)
        settings_layout_1.addWidget(filter_box)
        settings_layout_1.addWidget(other_box)

        rate_grid = QGridLayout()
        rate_grid.setColumnStretch(3, 3)
        rate_grid.setContentsMargins(0, 0, 0, 0)
        for i in range(3):
            slider_name = self.slider_names[i+6]
            rate_grid.addWidget(slider_labels[slider_name], i, 0)
            rate_grid.addWidget(self.slider_values[slider_name], i, 1)
            rate_grid.addWidget(self.sliders[slider_name], i, 2)

        rate_box = QGroupBox("Rates")
        rate_box.setLayout(rate_grid)

        settings_layout_2 = QVBoxLayout()
        settings_layout_2.addWidget(update_box)
        settings_layout_2.addWidget(rate_box)
        #settings_layout_2.addWidget(self.pause_button)

        hide_layout = QVBoxLayout()
        hide_layout.setAlignment(Qt.AlignTop)
        hide_layout.setContentsMargins(0, 0, 0, 0)

        self.hide_crop_check_box = QCheckBox("Hide Crop")
        self.hide_crop_check_box.setChecked(False)
        self.hide_crop_check_box.stateChanged.connect(self.toggle_cropped_img)
        hide_layout.addWidget(self.hide_crop_check_box)

        self.hide_filter_check_box = QCheckBox("Hide Filtered")
        self.hide_filter_check_box.setChecked(False)
        self.hide_filter_check_box.stateChanged.connect(self.toggle_filtered_img)
        hide_layout.addWidget(self.hide_filter_check_box)

        self.hide_fissure_check_box = QCheckBox("Hide Fissure Table")
        self.hide_fissure_check_box.setChecked(False)
        self.hide_fissure_check_box.stateChanged.connect(self.toggle_fissure_table)
        hide_layout.addWidget(self.hide_fissure_check_box)

        hide_box = QGroupBox("Hide UI")
        hide_box.setLayout(hide_layout)

        hide_relics_layout = QVBoxLayout()
        hide_relics_layout.setAlignment(Qt.AlignTop)
        hide_relics_layout.setContentsMargins(0, 0, 0, 0)
        relics = ["Axi", "Neo", "Meso", "Lith", "Requiem"]
        self.hide_relics = {}
        for relic in relics:
            self.hide_relics[relic] = QCheckBox(relic)
            self.hide_relics[relic].setChecked(False)
            self.hide_relics[relic].stateChanged.connect(partial(self.set_hidden_relic, relic))
            hide_relics_layout.addWidget(self.hide_relics[relic])

        hide_relics_box = QGroupBox("Hide Relics")
        hide_relics_box.setLayout(hide_relics_layout)

        self.hidden_relics = set()

        settings_layout_3 = QVBoxLayout()
        settings_layout_3.addWidget(hide_box)
        settings_layout_3.addWidget(hide_relics_box)


        self.settings_layout = QHBoxLayout()
        self.settings_layout.addLayout(settings_layout_1)
        self.settings_layout.addLayout(settings_layout_2)
        self.settings_layout.addLayout(settings_layout_3)

        bot_layout.addWidget(self.table)
        bot_layout.addWidget(self.mission_table)
        #bot_layout.addWidget(self.pref_box)
        #bot_layout.addWidget(update_box)

        bot_box = QGroupBox()
        bot_box.setLayout(bot_layout)
        bot_box.setFixedHeight(287)

        self.crop_img = QGroupBox("Crop")
        crop_img_layout = QVBoxLayout()
        crop_img_layout.addWidget(self.image_label)
        self.crop_img.setLayout(crop_img_layout)

        self.filter_img = QGroupBox("Filtered")
        filter_img_layout = QVBoxLayout()
        filter_img_layout.addWidget(self.image_label2)
        self.filter_img.setLayout(filter_img_layout)

        settings_button = QPushButton("\u2699")
        settings_button.setStyleSheet("background-color: rgba(0, 0, 0, 255); font-size: 23px;")
        settings_button.clicked.connect(self.show_preferences)
        settings_button.setFixedWidth(30)
        settings_button.setFixedHeight(30)
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.addSpacing(-14)

        settings_button_hb = QHBoxLayout()
        settings_button_hb.setAlignment(Qt.AlignRight)
        settings_button_hb.addWidget(settings_button)
        settings_button_hb.addSpacing(-13)

        self.layout.addLayout(settings_button_hb)

        self.layout.addWidget(self.crop_img)
        self.layout.addWidget(self.filter_img)
        self.layout.addWidget(bot_box)

        self.filled_rows = 0
        self.max = -1
        self.max_row = -1
        self.setLayout(self.layout)
        self.setWindowTitle('Warframe Prime Helper')

        self.ocr = None
        self.old_screenshot_shape = 0
        self.old_filtered_shape = 0

        self.missions = []

        self.dialog = QDialog()
        self.dialog.setWindowTitle("Preferences")
        self.dialog.setWindowModality(Qt.ApplicationModal)
        self.dialog.setLayout(self.settings_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_mission_table_time)
        self.timer.start(1000)

        self.show()
        self.setFixedSize(self.layout.sizeHint())

        self.ducats_thread = None
        self.prices_thread = None

        self.prices_progress_lock = Lock()
        self.ducats_progress_lock = Lock()

        self.num_primes = 100

        self.api = None

    def update_prices(self):
        self.prices_thread = threading.Thread(name="prices_thread", target=self.market_api.update_prices)
        self.prices_thread.start()

        self.update_prices_button.setEnabled(False)
        self.update_ducats_button.setEnabled(False)

    def update_ducats(self):
        self.ducats_thread = threading.Thread(name="ducats_thread", target=self.market_api.update_ducats)
        self.ducats_thread.start()

        self.update_prices_button.setEnabled(False)
        self.update_ducats_button.setEnabled(False)

    def update_primes_info(self, num, latest):
        self.num_parts_value.setNum(num)
        self.latest_item_value.setText(latest)
        self.update_prices_progress.setMaximum(num)
        self.update_ducats_progress.setMaximum(num)
        self.num_primes = num

    def get_datetime(self):
        return datetime.now().strftime("%b %d %Y %H:%M:%S")

    def update_ducats_time(self):
        self.last_updated_ducats_value.setText(self.get_datetime())
        self.ducats_progress_lock.acquire()
        self.update_ducats_progress.setValue(self.num_primes)
        self.ducats_progress_lock.release()

    def update_prices_time(self):
        self.last_updated_prices_value.setText(self.get_datetime())
        self.prices_progress_lock.acquire()
        self.update_prices_progress.setValue(self.num_primes)
        self.prices_progress_lock.release()

    def set_update_prices_progress(self, val):
        if self.prices_progress_lock.acquire():
            self.update_prices_progress.setValue(val)
            self.prices_progress_lock.release()

    def set_update_ducats_progress(self, val):
        if self.ducats_progress_lock.acquire():
            self.update_ducats_progress.setValue(val)
            self.ducats_progress_lock.release()

    def finished_update_progress(self):
        self.update_prices_button.setEnabled(True)
        self.update_ducats_button.setEnabled(True)

    def show_preferences(self):
        self.dialog.exec_()

    def toggle_fissure_table(self, checkbox):
        if self.hide_fissure_check_box.isChecked():
            self.mission_table.hide()
        else:
            self.mission_table.show()
        self.setFixedSize(self.layout.sizeHint())

    def toggle_move_to_top(self, checkbox):
        self.ocr.set_move_to_top(self.move_to_top_check_box.isChecked())

    def toggle_cropped_img(self, checkbox):
        if self.hide_crop_check_box.isChecked():
            self.crop_img.hide()
        else:
            self.crop_img.show()
        self.setFixedSize(self.layout.sizeHint())

    def toggle_filtered_img(self, checkbox):
        if self.hide_filter_check_box.isChecked():
            self.filter_img.hide()
        else:
            self.filter_img.show()
        self.setFixedSize(self.layout.sizeHint())

    def set_sliders_range(self, x, y):
        if not self.is_slider_max_set:
            self.sliders['x'].setMaximum(int(x / 2))
            self.sliders['y'].setMaximum(int(y / 2))
            self.sliders['w'].setMaximum(x)
            self.sliders['h'].setMaximum(y)
            for slider_name in self.slider_names:
                self.sliders[slider_name].setValue(self.slider_default_values[slider_name])
            self.is_slider_max_set = True

    def toggle_button(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.setText("Resume")
        else:
            self.pause_button.setText("Pause")
        if self.ocr is not None:
            if self.is_paused:
                self.ocr.save_screenshot()
                self.ocr.skip_screenshot = True
            else:
                self.ocr.skip_screenshot = False

    def clear_table(self):
        self.table.clearSelection()
        self.table.clearContents()
        self.filled_rows = 0
        self.table.setRowCount(self.filled_rows)

    def is_plat_preferred(self):
        return self.plat_check_box.isChecked()

    def insert_table_row(self, row):
        for i in range(3):
            self.table.setItem(self.filled_rows, i, QTableWidgetItem(str(row[i])))

        val = row[2]
        if self.is_plat_preferred():
            val = row[1]

        if self.max > val:
            self.max = val
            self.max_row = self.filled_rows

        self.filled_rows = self.filled_rows + 1
        self.table.setRowCount(self.filled_rows)

    def update_mission_table(self, missions):
        self.missions = list(missions)
        cur_time = time.time()
        for i in range(len(missions)):
            for j in range(3):
                self.mission_table.setItem(i, j, QTableWidgetItem(str(self.missions[i][j])))

            self.mission_table.setItem(i, 3, QTableWidgetItem(self.get_duration_str(self.missions[i][3]-cur_time)))
            if self.missions[i][0] in self.hidden_relics:
                self.mission_table.setRowHidden(i, True)
            else:
                self.mission_table.setRowHidden(i, False)

        self.mission_table.setRowCount(len(self.missions)-1)

    def update_mission_table_time(self):
        cur_time = time.time()
        needs_update = False
        for i in range(len(self.missions)):
            self.mission_table.setItem(i, 3, QTableWidgetItem(self.get_duration_str(self.missions[i][3]-cur_time)))
            if self.missions[i][3]-cur_time < 0:
                needs_update = True
        if needs_update:
            self.api.filter_expired_missions()

    def update_mission_table_hidden(self):
        for i in range(len(self.missions)):
            if self.missions[i][0] in self.hidden_relics:
                self.mission_table.setRowHidden(i, True)
            else:
                self.mission_table.setRowHidden(i, False)

    def get_duration_str(self, duration):
        m, s = divmod(int(duration), 60)
        h, m = divmod(m, 60)
        return '{:d}:{:02d}:{:02d}'.format(h, m, s)

    def set_ocr_connection(self, ocr):
        for slider_name in self.slider_names:
            self.sliders[slider_name].valueChanged.connect(partial(self.set_ocr_crop, ocr, slider_name))
        self.ocr = ocr
        self.market_api = MarketReader(ocr=self.ocr, gui=self)

    def set_api(self, wf_api):
        self.api = wf_api

    def set_hidden_relic(self, relic, checkbox):
        if self.hide_relics[relic].isChecked():
            self.hidden_relics.add(relic)
        else:
            self.hidden_relics.remove(relic)
        self.update_mission_table_hidden()

    def set_ocr_crop(self, ocr, dim, val):
        self.slider_values[dim].setNum(val)
        if val < 0 or val > 100000 or val is None:
            return
        if dim == 'x':
            ocr.set_x_offset(val)
        if dim == 'y':
            ocr.set_y_offset(val)
        if dim == 'w':
            ocr.set_w(val)
        if dim == 'h':
            ocr.set_h(val)
        if dim == 'v1':
            ocr.set_v1(val)
        if dim == 'v2':
            ocr.set_v2(val)
        if dim == 'Screencap (s)':
            ocr.set_interval(val)
        if dim == 'Fissure (s)':
            self.api.set_rate(val)
        if dim == 'API Threads':
            self.market_api.set_num_threads(val)

    def select_max(self):
        # TODO doesnt work
        self.table.clearSelection()
        self.table.selectRow(self.max_row)

    def update_images(self, screenshot, filtered):
        screenshot_shape = None
        filtered_shape = None
        if not self.hide_crop_check_box.isChecked():
            screenshot_shape = screenshot.shape
            h, w, ch = screenshot.shape
            bytes_per_line = ch * w
            screenshot_pix = QPixmap(QImage(screenshot, w, h, bytes_per_line, QImage.Format_RGB888))
            if w != 908 or h != 70:
                screenshot_pix = screenshot_pix.scaled(908, 70, Qt.KeepAspectRatio)
            self.image_label.setPixmap(screenshot_pix)

        if not self.hide_filter_check_box.isChecked():
            filtered_shape = filtered.shape
            h, w = filtered.shape
            bytes_per_line = w
            filtered_pix = QPixmap(QImage(filtered, w, h, bytes_per_line, QImage.Format_Grayscale8))
            if w != 908 or h != 70:
                filtered_pix = filtered_pix.scaled(908, 70, Qt.KeepAspectRatio)
            self.image_label2.setPixmap(filtered_pix)
        self.update_window_size(screenshot_shape, filtered_shape)

    def update_window_size(self, screenshot_shape, filtered_shape):
        should_update = False
        if screenshot_shape is not None and screenshot_shape == self.old_screenshot_shape:
            self.old_screenshot_shape = screenshot_shape
            should_update = True
        if filtered_shape is not None and filtered_shape == self.old_filtered_shape:
            self.old_filtered_shape = filtered_shape
            should_update = True
        if should_update:
            self.setFixedSize(self.layout.sizeHint())

    def __exit__(self):
        self.market_api.exit_now = True
        self.ocr.exit_now = True
        #self.prices_thread.join()
        #self.ducats_thread.join()


class OCRThread(QThread):
    def __init__(self, gui):
        QThread.__init__(self)
        self.ocr = OCR(debug=False, gui=gui)

    def __del__(self):
        self.ocr.exit_now = True
        self.ocr_thread.join()
        self.wait()

    def run(self):
        self.ocr_thread = threading.Thread(name="ocr_thread", target=self.ocr.main)
        self.ocr_thread.start()
        while self.ocr is not None and not self.ocr.exit_now:
            time.sleep(1)


class APIThread(QThread):
    def __init__(self, gui):
        QThread.__init__(self)
        self.api = APIReader(gui=gui)
        self.api_thread = None

    def __del__(self):
        self.api.cancel_event()
        self.wait()

    def run(self):
        self.api_thread = threading.Thread(name="api_thread", target=api.run)
        self.api.run()


if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    app.setWindowIcon(QIcon(window.icon_path))
    dark_stylesheet = qdarkstyle.load_stylesheet_pyqt5()
    app.setStyleSheet(dark_stylesheet)

    ocr_thread = OCRThread(window)
    window.set_ocr_connection(ocr_thread.ocr)
    ocr_thread.start()

    api = APIReader(gui=window)
    api_thread = APIThread(window)
    window.set_api(api)
    api_thread.start()

    market_api = window.market_api

    app.exec_()
    market_api.exit_now = True
    ocr_thread.terminate()
    api_thread.terminate()


    # use to figure out if any threads are keeping python open
    # time.sleep(1)
    # print(str({t.ident: t.name for t in threading.enumerate()}))
