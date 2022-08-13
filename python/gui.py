from __future__ import print_function
from __future__ import division
import time
import numpy as np
import PyQt5.QtWidgets as QtGui
import pyqtgraph as pg

class GUI:
    plot = []
    curve = []
    text = []
    slider = []
    button = []

    def __init__(self, width=800, height=450, title=''):
        # Create GUI window
        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsView()
        self.win.resize(width, height)
        self.win.setWindowTitle(title)
        # Create GUI layout
        self.layout = pg.GraphicsLayout(border=(100,100,100))
        self.win.setCentralItem(self.layout)
        self.win.show()

    def add_plot(self, title):
        new_plot = self.layout.addPlot(title=title)
        self.plot.append(new_plot)
        self.curve.append([])

    def add_text(self, text):
        new_text = self.layout.addLabel(text=text)
        self.text.append(new_text)
    
    def add_Slider(self, fun=None, orientation='bottom'):
        new_slider = pg.TickSliderItem(orientation=orientation, allowAdd=False)
        new_slider.tickMoveFinished = fun
        self.layout.addItem(new_slider)
        self.slider.append(new_slider)

    def add_curve(self, plot_index, pen=(255, 255, 255)):
        self.curve[plot_index].append(self.plot[plot_index].plot(pen=pen))

    def rander(self):
        self.app.processEvents()


if __name__ == '__main__':
    # Example test gui
    N = 48
    gui = GUI(title='Test')
    # Sin plot
    gui.add_plot(title='Sin Plot')
    gui.add_curve(plot_index=0)
    gui.layout.nextRow()
    # Cos plot
    gui.add_plot(title='Cos Plot')
    gui.add_curve(plot_index=1)
    gui.add_curve(plot_index=1, pen=(255, 0, 0))
    gui.layout.nextRow()
    # text
    gui.add_text(text='test')
    gui.layout.nextRow()
    # slider
    def testfun(tick):
        gui.text[0].setText('test: {} - {}'.format(gui.slider[0].tickValue(0), gui.slider[0].tickValue(1)))
    gui.add_Slider(fun=testfun)
    gui.slider[0].addTick(0.1)
    gui.slider[0].addTick(0.8)
    gui.layout.nextRow()
    while True:
        t = time.time()
        x = np.linspace(t, 2 * np.pi + t, N)
        gui.curve[0][0].setData(x=x, y=np.sin(x))
        gui.curve[1][0].setData(x=x, y=np.cos(x))
        gui.curve[1][1].setData(x=x, y=np.sin(x)/2)
        try:
            gui.rander()
            time.sleep(1.0 / 30.0)
        except KeyboardInterrupt:
            break
