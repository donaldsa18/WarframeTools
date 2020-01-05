from PyQt5.QtWidgets import QApplication, QTableWidget, QWidget, QVBoxLayout, QLabel, QAbstractItemView, QHBoxLayout, \
    QSlider, QGridLayout, QGroupBox, QCheckBox, QHeaderView, QPushButton, QProgressBar, QTableWidgetItem, QDialog
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, QTimer
import qdarkstyle
from functools import partial
from ocr import OCR
from api import APIReader
import time
import sched


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()

        self.icon_path = 'warframe.ico'

        #self.layout = QVBoxLayout()

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

        self.slider_names = ['x', 'y', 'w', 'h', 'v1', 'v2', 'Screencap', 'Fissure']
        self.sliders = {x: QSlider(Qt.Horizontal) for x in self.slider_names}
        slider_labels = {x: QLabel(x) for x in self.slider_names}
        self.slider_default_values = {'x': 521, 'y': 400, 'w': 908, 'h': 70, 'v1': 197, 'v2': 180, 'Screencap': 1, 'Fissure': 30}
        self.slider_values = {x: QLabel(str(self.slider_default_values[x])) for x in self.slider_names}

        self.sliders['x'].setMaximum(int(warframe_width / 2))
        self.sliders['y'].setMaximum(int(warframe_height / 2))
        self.sliders['w'].setMaximum(warframe_width)
        self.sliders['h'].setMaximum(warframe_height)
        self.sliders['v1'].setMaximum(255)
        self.sliders['v2'].setMaximum(255)
        for slider_name in self.slider_names:
            self.sliders[slider_name].setMinimum(0)
            self.sliders[slider_name].setSingleStep(1)
            #self.sliders[slider_name].valueChanged.connect(self.slider_values[slider_name].setNum)
            self.slider_values[slider_name].setFixedWidth(35)
            self.sliders[slider_name].setValue(self.slider_default_values[slider_name])

        self.sliders['Screencap'].setMaximum(5)
        self.sliders['Screencap'].setMinimum(1)
        self.sliders['Fissure'].setMaximum(60)
        self.sliders['Fissure'].setMinimum(10)


        self.is_slider_max_set = False

        self.pref_grid = QGridLayout()
        self.pref_grid.setColumnStretch(3, 7)
        #grid.setContentsMargins(7, 7, 7, 7)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_button)
        self.is_paused = False
        #self.pref_grid.addWidget(self.pause_button, 0, 0, 1, 3)

        self.plat_check_box = QCheckBox("Prefer platinum")
        self.plat_check_box.setChecked(True)
        #self.pref_grid.addWidget(self.plat_check_box, 1, 0, 1, 3)

        update_layout = QGridLayout()
        update_layout.setColumnStretch(4, 2)
        update_layout.setAlignment(Qt.AlignTop)
        update_layout.setContentsMargins(0, 0, 0, 0)

        update_prices_button = QPushButton("Update Prices")
        update_prices_progress = QProgressBar()
        update_prices_progress.setFixedWidth(110)
        update_layout.addWidget(update_prices_button, 0, 0)
        update_layout.addWidget(update_prices_progress, 0, 1)

        last_updated_label = QLabel("Last Updated")
        last_updated_value = QLabel("1/1/2020")
        update_layout.addWidget(last_updated_label, 1, 0)
        update_layout.addWidget(last_updated_value, 1, 1)

        num_parts_label = QLabel("Prime Parts")
        num_parts_value = QLabel("100")
        update_layout.addWidget(num_parts_label, 2, 0)
        update_layout.addWidget(num_parts_value, 2, 1)

        latest_item_label = QLabel("Latest Prime")
        latest_item_value = QLabel("Ivara Prime")
        update_layout.addWidget(latest_item_label, 3, 0)
        update_layout.addWidget(latest_item_value, 3, 1)

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

        settings_layout_1 = QVBoxLayout()
        settings_layout_1.addWidget(crop_box)
        settings_layout_1.addWidget(filter_box)

        rate_grid = QGridLayout()
        rate_grid.setColumnStretch(3, 2)
        rate_grid.setContentsMargins(0, 0, 0, 0)
        for i in range(2):
            slider_name = self.slider_names[i+6]
            rate_grid.addWidget(slider_labels[slider_name], i, 0)
            rate_grid.addWidget(self.slider_values[slider_name], i, 1)
            rate_grid.addWidget(self.sliders[slider_name], i, 2)

        rate_box = QGroupBox("Rates")
        rate_box.setLayout(rate_grid)

        settings_layout_2 = QVBoxLayout()
        settings_layout_2.addWidget(update_box)
        settings_layout_2.addWidget(rate_box)
        settings_layout_2.addWidget(self.pause_button)

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

    def show_preferences(self):
        self.dialog.exec_()

    def toggle_fissure_table(self, checkbox):
        if self.hide_fissure_check_box.isChecked():
            self.mission_table.hide()
        else:
            self.mission_table.show()
        self.setFixedSize(self.layout.sizeHint())

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
        for i in range(len(self.missions)):
            self.mission_table.setItem(i, 3, QTableWidgetItem(self.get_duration_str(self.missions[i][3]-cur_time)))

    def update_mission_table_hidden(self):
        for i in range(len(self.missions)):
            if self.missions[i][0] in self.hidden_relics:
                self.mission_table.setRowHidden(i, True)
            else:
                self.mission_table.setRowHidden(i, False)

    def get_duration_str(self,duration):
        m, s = divmod(int(duration), 60)
        h, m = divmod(m, 60)
        return '{:d}:{:02d}:{:02d}'.format(h, m, s)

    def set_ocr_connection(self, ocr):
        for slider_name in self.slider_names:
            self.sliders[slider_name].valueChanged.connect(partial(self.set_ocr_crop, ocr, slider_name))
        self.ocr = ocr

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


class OCRThread(QThread):
    def __init__(self, gui):
        QThread.__init__(self)
        self.exit_now = False
        self.ocr = OCR(debug=False, gui=gui)

    def __del__(self):
        self.exit_now = True
        self.wait()

    def run(self):
        self.ocr.main(thread=self)


class APIThread(QThread):
    def __init__(self, gui):
        QThread.__init__(self)
        self.api = APIReader(gui=gui)

    def __del__(self):
        self.wait()

    def run(self):
        self.api.run()

class TableThread(QThread):
    def __init__(self, gui):
        QThread.__init__(self)
        #self.scheduler = sched.scheduler(time.time, time.sleep)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.gui = gui

    def __del__(self):
        self.wait()

    def run(self):
        self.timer.start(1000)

    def update(self):
        self.gui.update_mission_table_time()

app = QApplication([])
window = Window()
app.setWindowIcon(QIcon(window.icon_path))
dark_stylesheet = qdarkstyle.load_stylesheet_pyqt5()
app.setStyleSheet(dark_stylesheet)

thread = OCRThread(window)
window.set_ocr_connection(thread.ocr)
thread.start()

api_thread = APIThread(window)
api_thread.start()

#table_thread = TableThread(window)
#table_thread.start()

app.exec_()
