from PyQt5.QtWidgets import QApplication, QTableWidget, QWidget, QVBoxLayout, QLabel, QAbstractItemView, QHBoxLayout, \
    QSlider, QGridLayout, QGroupBox, QCheckBox, QHeaderView, QPushButton, QProgressBar, QTableWidgetItem
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import Qt, QThread
import qdarkstyle
from functools import partial
from ocr import OCR


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()

        self.icon_path = 'warframe.ico'

        self.layout = QVBoxLayout()

        self.image_label = QLabel()
        image = QPixmap('temp\\crop_27.bmp')
        self.image_label.setPixmap(image)

        self.image_label2 = QLabel()
        self.image_label2.setPixmap(image)

        bot_layout = QHBoxLayout()
        warframe_height = 1080
        warframe_width = 1920

        self.table = QTableWidget(6, 3)
        self.table.setHorizontalHeaderLabels(['Name', 'Plat', 'Ducats'])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.slider_names = ['x', 'y', 'w', 'h', 'v1', 'v2']
        self.sliders = {x: QSlider(Qt.Horizontal) for x in self.slider_names}
        slider_labels = {x: QLabel(x) for x in self.slider_names}
        self.slider_default_values = {'x': 521, 'y': 400, 'w': 908, 'h': 70, 'v1': 197, 'v2': 180}
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


        self.is_slider_max_set = False

        grid = QGridLayout()
        grid.setColumnStretch(3, 7)
        #grid.setContentsMargins(7, 7, 7, 7)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_button)
        self.is_paused = False
        grid.addWidget(self.pause_button, 0, 0, 1, 3)

        self.plat_check_box = QCheckBox("Prefer platinum")
        self.plat_check_box.setChecked(True)
        grid.addWidget(self.plat_check_box, 1, 0, 1, 3)

        self.hide_crop_check_box = QCheckBox("Hide Crop")
        self.hide_crop_check_box.setChecked(False)
        self.hide_crop_check_box.stateChanged.connect(self.toggle_cropped_img)
        grid.addWidget(self.hide_crop_check_box, 2, 0, 1, 3)

        self.hide_filter_check_box = QCheckBox("Hide Filtered")
        self.hide_filter_check_box.setChecked(False)
        self.hide_filter_check_box.stateChanged.connect(self.toggle_filtered_img)
        grid.addWidget(self.hide_filter_check_box, 2, 2, 1, 3)

        update_layout = QGridLayout()
        update_layout.setColumnStretch(4, 2)
        update_layout.setContentsMargins(7, 7, 7, 60)

        update_prices_button = QPushButton("Update Prices")
        update_prices_progress = QProgressBar()
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
        update_box.setFixedWidth(190)
        update_box.setFixedHeight(212)
        i = 4
        for slider_name in self.slider_names:
            grid.addWidget(slider_labels[slider_name], i, 0)
            grid.addWidget(self.slider_values[slider_name], i, 1)
            grid.addWidget(self.sliders[slider_name], i, 2)
            i = i + 1

        group_box = QGroupBox("Preferences")
        group_box.setLayout(grid)
        group_box.setFixedWidth(190)
        group_box.setFixedHeight(212)

        bot_layout.addWidget(self.table)
        bot_layout.addWidget(group_box)
        bot_layout.addWidget(update_box)

        bot_box = QGroupBox()
        bot_box.setLayout(bot_layout)
        bot_box.setFixedHeight(257)

        self.crop_img = QGroupBox("Crop")
        crop_img_layout = QVBoxLayout()
        crop_img_layout.addWidget(self.image_label)
        self.crop_img.setLayout(crop_img_layout)

        self.filter_img = QGroupBox("Filtered")
        filter_img_layout = QVBoxLayout()
        filter_img_layout.addWidget(self.image_label2)
        self.filter_img.setLayout(filter_img_layout)

        self.layout.addWidget(self.crop_img)
        self.layout.addWidget(self.filter_img)
        self.layout.addWidget(bot_box)

        self.filled_rows = 0
        self.max = -1
        self.max_row = -1
        self.setLayout(self.layout)
        self.setWindowTitle('Warframe Prime Helper')

        self.ocr = None

        self.show()
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

    def set_ocr_connection(self, ocr):
        for slider_name in self.slider_names:
            self.sliders[slider_name].valueChanged.connect(partial(self.set_ocr_crop, ocr, slider_name))
        self.ocr = ocr

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
        if not self.hide_crop_check_box.isChecked():
            h, w, ch = screenshot.shape
            bytes_per_line = ch * w
            screenshot_pix = QPixmap(QImage(screenshot, w, h, bytes_per_line, QImage.Format_RGB888))
            self.image_label.setPixmap(screenshot_pix)

        if not self.hide_filter_check_box.isChecked():
            h, w = filtered.shape
            bytes_per_line = w
            filtered_pix = QPixmap(QImage(filtered, w, h, bytes_per_line, QImage.Format_Grayscale8))
            self.image_label2.setPixmap(filtered_pix)


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


app = QApplication([])
window = Window()
app.setWindowIcon(QIcon(window.icon_path))
dark_stylesheet = qdarkstyle.load_stylesheet_pyqt5()
app.setStyleSheet(dark_stylesheet)
thread = OCRThread(window)
window.set_ocr_connection(thread.ocr)
thread.start()
app.exec_()
