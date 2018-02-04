import queue

from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd

from log import get_logger

logger = get_logger(__name__)

# TODO: should this be LIFO to reflect the latest state?
q = queue.Queue()  # infinite FIFO queue

downsample = 10
window = 200  # visible time slot (ms)
sample_rate = 44100  # 44.1 kHz
device = 1  # machine dependent
channels = 2
mapping = [i for i in range(channels)]
interval = 30  # minimum time between plot updates (ms)


def audio_callback(indata, frames, time, status):
    """ Receive audio input and add downsized one to the Queue """
    item = indata[::downsample, mapping]
    q.put(item)

    logger.debug('indata {} -> {}'.format(indata.shape, item.shape))
    logger.debug('qsize: {}'.format(q.qsize()))


def init_plot():
    """ Initialise the plot area """
    ax.set_ylim((-1.0, 1.0))
    ax.axhline(0, color='black', lw=1)

    return lines


def update_plot(frame):
    """ Update the plot by picking up the real-time input from Queue """
    while True:
        try:
            # raises Empty exception immediately if queue has no item
            data = q.get_nowait()
        except queue.Empty:
            break

        shift = len(data)
        remaining = length - shift

        for idx, line in enumerate(lines):
            original_data = line.get_data()[1]  # [0] is axis
            plot_data = np.concatenate((original_data[-remaining:],
                                        data[:, idx]))

            line.set_ydata(plot_data)

    return lines


if __name__ == '__main__':
    # length = 882 in case of 200 ms of window
    length = int(window * sample_rate / 1000 / downsample)
    plotdata = np.zeros((length, channels))

    fig, ax = plt.subplots()
    lines = ax.plot(plotdata)  # list of Line2D object

    stream = sd.InputStream(samplerate=sample_rate, callback=audio_callback,
                            device=device,
                            channels=channels)
    ani = FuncAnimation(fig, update_plot, interval=interval, blit=True,
                        init_func=init_plot)

    with stream:
        plt.show()
