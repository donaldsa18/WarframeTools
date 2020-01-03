from PyQt5.QtWidgets import QApplication, QTableWidget, QGridLayout, QWidget, QVBoxLayout, QLabel, QAbstractItemView, QTableWidgetItem, QHBoxLayout, QSlider, QGridLayout, QGroupBox, QCheckBox, QHeaderView
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
import qdarkstyle

icon_path = '.\warframe.ico'

app = QApplication([])
app.setWindowIcon(QIcon(icon_path))
dark_stylesheet = qdarkstyle.load_stylesheet_pyqt5()
app.setStyleSheet(dark_stylesheet)

window = QWidget()
layout = QVBoxLayout()

image_label = QLabel()
image = QPixmap('..\\temp\\crop_27.bmp')
image_label.setPixmap(image)

bot_layout = QHBoxLayout()
warframe_height = 1080
warframe_width = 1920

table = QTableWidget(6,3)
table.setHorizontalHeaderLabels(['Name','Plat','Ducats'])
table.setEditTriggers(QAbstractItemView.NoEditTriggers)
header = table.horizontalHeader()
header.setSectionResizeMode(0, QHeaderView.Stretch)
header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

slider_names = ['x','y','w','h']
sliders = {x:QSlider(Qt.Horizontal) for x in slider_names}
slider_labels = {x:QLabel(x) for x in slider_names}
slider_values = {x:QLabel("0") for x in slider_names}
for slider_name in slider_names:
	sliders[slider_name].setMinimum(0)
	sliders[slider_name].setSingleStep(1)
	sliders[slider_name].valueChanged.connect(slider_values[slider_name].setNum)
	slider_values[slider_name].setFixedWidth(35)
sliders['x'].setMaximum(int(warframe_width/2))
sliders['y'].setMaximum(int(warframe_height/2))
sliders['w'].setMaximum(warframe_width)
sliders['h'].setMaximum(warframe_height)

grid = QGridLayout()
grid.setColumnStretch(3,5)


check_box = QCheckBox("Prefer platinum")
check_box.setChecked(True)
grid.addWidget(check_box,0,0,1,3)
i = 1
for slider_name in slider_names:
	grid.addWidget(slider_labels[slider_name],i,0)
	grid.addWidget(slider_values[slider_name],i,1)
	grid.addWidget(sliders[slider_name],i,2)
	i = i + 1


group_box = QGroupBox("Preferences")
group_box.setLayout(grid)
group_box.setFixedWidth(190)
bot_layout.addWidget(table)
bot_layout.addWidget(group_box)

bot_box = QGroupBox()
bot_box.setLayout(bot_layout)

layout.addWidget(image_label)
layout.addWidget(bot_box)

window.setLayout(layout)
window.setWindowTitle('Warframe Prime Helper')
window.resize(image.width(),image.height()+290)

window.show()

app.exec_()