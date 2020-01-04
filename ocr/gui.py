from PyQt5.QtWidgets import QApplication, QTableWidget, QWidget, QVBoxLayout, QLabel, QAbstractItemView, QHBoxLayout, \
    QSlider, QGridLayout, QGroupBox, QCheckBox, QHeaderView, QPushButton, QProgressBar
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
import qdarkstyle
from ocr import OCR


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()

        self.icon_path = 'warframe.ico'

        layout = QVBoxLayout()

        image_label = QLabel()
        image = QPixmap('temp\\crop_27.bmp')
        image_label.setPixmap(image)

        bot_layout = QHBoxLayout()
        warframe_height = 1080
        warframe_width = 1920

        table = QTableWidget(6, 3)
        table.setHorizontalHeaderLabels(['Name', 'Plat', 'Ducats'])
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        slider_names = ['x', 'y', 'w', 'h']
        sliders = {x: QSlider(Qt.Horizontal) for x in slider_names}
        slider_labels = {x: QLabel(x) for x in slider_names}
        slider_values = {x: QLabel("0") for x in slider_names}
        for slider_name in slider_names:
            sliders[slider_name].setMinimum(0)
            sliders[slider_name].setSingleStep(1)
            sliders[slider_name].valueChanged.connect(slider_values[slider_name].setNum)
            slider_values[slider_name].setFixedWidth(35)
        sliders['x'].setMaximum(int(warframe_width / 2))
        sliders['y'].setMaximum(int(warframe_height / 2))
        sliders['w'].setMaximum(warframe_width)
        sliders['h'].setMaximum(warframe_height)

        grid = QGridLayout()
        grid.setColumnStretch(3, 7)
        grid.setContentsMargins(7, 7, 7, 30)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_button)

        grid.addWidget(self.pause_button, 0, 0, 1, 3)

        check_box = QCheckBox("Prefer platinum")
        check_box.setChecked(True)
        check_box.toggle()

        grid.addWidget(check_box, 1, 1, 1, 3)

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
        i = 2
        for slider_name in slider_names:
            grid.addWidget(slider_labels[slider_name], i, 0)
            grid.addWidget(slider_values[slider_name], i, 1)
            grid.addWidget(sliders[slider_name], i, 2)
            i = i + 1

        group_box = QGroupBox("Preferences")
        group_box.setLayout(grid)
        group_box.setFixedWidth(190)
        group_box.setFixedHeight(212)

        bot_layout.addWidget(table)
        bot_layout.addWidget(group_box)
        bot_layout.addWidget(update_box)

        bot_box = QGroupBox()
        bot_box.setLayout(bot_layout)
        bot_box.setFixedHeight(257)

        layout.addWidget(image_label)
        layout.addWidget(bot_box)

        self.setLayout(layout)
        self.setWindowTitle('Warframe Prime Helper')
        self.resize(image.width(), image.height() + 290)

        self.show()

    def toggle_button(self):
        if self.pause_button.text() == "Pause":
            self.pause_button.setText("Resume")
        else:
            self.pause_button.setText("Pause")

app = QApplication([])
window = Window()
app.setWindowIcon(QIcon(window.icon_path))
dark_stylesheet = qdarkstyle.load_stylesheet_pyqt5()
app.setStyleSheet(dark_stylesheet)
app.exec_()
