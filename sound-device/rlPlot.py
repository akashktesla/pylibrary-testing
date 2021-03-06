import queue
import sys

from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd



list_devices = False
channels = [1]
device = None
window = 200
interval = 30
blocksize = None
samplerate = None
downsample = 10
mapping = [c - 1 for c in channels]  # Channel numbers start with 1
q = queue.Queue()

def int_or_str(text):
    try:
        return int(text)
    except ValueError:
        return text

def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    # Fancy indexing with mapping creates a (necessary!) copy:
    q.put(indata[::downsample, mapping])


def update_plot(frame):
    global plotdata
    while True:
        try:
            data = q.get_nowait()
        except queue.Empty:
            break
        shift = len(data)
        plotdata = np.roll(plotdata, -shift, axis=0)
        plotdata[-shift:, :] = data
    for column, line in enumerate(lines):
        line.set_ydata(plotdata[:, column])

    print(lines)
    return lines


try:
    if samplerate is None:
        device_info = sd.query_devices(device, 'input')
        samplerate = device_info['default_samplerate']
    length = int(window * samplerate / (1000 * downsample))
    plotdata = np.zeros((length, len(channels)))

    fig, ax = plt.subplots()
    lines = ax.plot(plotdata)
    if len(channels) > 1:
        ax.legend(['channel {}'.format(c) for c in channels],
                  loc='lower left', ncol=len(channels))

    print(plotdata)
    ax.axis((0, len(plotdata), -1, 1))
    ax.set_yticks([0])
    ax.yaxis.grid(True)
    ax.tick_params(bottom=False, top=False, labelbottom=False, right=False, left=False, labelleft=False)
    fig.tight_layout(pad=0)
    stream = sd.InputStream(device= device, channels=max(channels),samplerate= samplerate, callback=audio_callback)
    ani = FuncAnimation(fig, update_plot, interval= interval, blit=True)
    with stream:
        print(plotdata)
        plt.show()

except Exception as e:
    print(type(e).__name__ + ': ' + str(e))