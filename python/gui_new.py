from __future__ import print_function
from __future__ import division
import PyQt5.QtWidgets as QtGui
import pyqtgraph as pg

class GUI(QtGui.QWidget):
    plot = []
    curve = []
    text = []

    def __init__(self, width=800, height=450, title=''):
        super(GUI, self).__init__()
        # Create GUI window
        self.resize(width, height)
        self.setWindowTitle(title)
        self.setStyleSheet("background-color:black;")
        self.setAutoFillBackground(True)
        self.show()

        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
    
    def add_plot(self, title=""):
        new_plot = pg.PlotWidget(title=title)
        self.grid.addWidget(new_plot)
        self.plot.append(new_plot)
        self.curve.append([])
        return len(self.plot)-1
    
    def add_curve(self, plot_index, pen=(255, 255, 255)):
        self.curve[plot_index].append(self.plot[plot_index].plot(pen=pen))
        return len(gui.curve)-1

    def add_text(self, text):
        new_text = QtGui.QLabel()
        new_text.setText(text)
        self.grid.addWidget(new_text)
        self.text.append(new_text)
        return len(self.text)-1


if __name__ == '__main__':
    import time
    import numpy as np
    # Example test gui
    app = QtGui.QApplication([])
    gui = GUI(title='Test')
    # plots
    gui.add_plot(title='Sin Plot')
    gui.add_curve(plot_index=0)
    gui.add_plot(title='Cos Plot')
    gui.add_curve(plot_index=1)
    gui.add_curve(plot_index=1, pen=(255, 0, 0))
    # text
    gui.add_text(text='test')
    while True:
        try:
            t = time.time()
            x = np.linspace(t, 2 * np.pi + t, 28)
            gui.curve[0][0].setData(x=x, y=np.sin(x))
            gui.curve[1][0].setData(x=x, y=np.cos(x))
            gui.curve[1][1].setData(x=x, y=np.sin(x)/2)
            app.processEvents()
            time.sleep(1.0 / 30.0)
        except KeyboardInterrupt:
            break