# maestroAnalyze
A python program that analyzes output from the Maestro data collection software.

## Dependencies
maestroAnalyze runs on Python 3 and depends on the `pygame` module. Python 3 comes standard in all Linux distributions; Windows users can download it [here](https://www.python.org/ftp/python/3.6.1/python-3.6.1.exe). `pygame` does not come with any python interpreter that I'm aware of, but can be installed relatively easily. On Ubuntu or Ubuntu-based Linux distributions, you can run `sudo apt install python3-pygame`, or if you have the Python 3 version of `pip` (from the package `python3-pip` on Ubuntu-like Linux distros) you can run `pip3 install pygame` to install for one user or `sudo -H pip install pygame` to install for all users. If all else fails (or if you're on Windows and don't have/want `pip`), `pygame` can be downloaded from the official website: [pygame.org](https://www.pygame.org).

## Usage

### Command Line
If Python 3 is in your `$PATH`/`%PATH%` as `python3` and the `maestroAnalyze.py` file is in your current directory, the program can be run like so:
```bash
python3 maestroAnalyze.py <OPTIONS>
```
On Linux, `maestroAnalyze.py` will be executable, so you can just run `./maestroAnalyze.py <OPTIONS>`. 
To see help text explaining how to use the program, pass the `-h` or `--help` flag as an option. It'll look like this:
```bash
user@host$: python3 maestroAnalyze.py --help
usage: maestro.py [-h] [-t] [FILE]

Displays data exported in ASCII format from Maestro software.

positional arguments:
  FILE        The name of the file to read from. If not given, reads from
              stdin.

optional arguments:
  -h, --help  show this help message and exit
  -t          operates in text-mode, outputting some information to stdout and
              exiting.
```

### The Program Window
Some sample data sets are included in this repository. The file `background_sample.Spe` contains a spectrum collected when no sources were present near the detector; it contains only ordinary, "background" radiation. To open this file in maestroAnalyze, simply run `python3 maestroAnalyze.py background_sample.Spe`. You should see a window that looks like the following:
![Sample of background radiation spectrum](https://github.com/ocket8888/maestroAnalyze/blob/master/background_sample.png?raw=true)
Channels (or "bins") are colored as a heat map of their count. Click the green button to switch between a log scale and a linear scale. Notice that many of the fields in the text at the top of the window to the right of the green scaling button are showing a value of "N/A". That is because no channels have been *selected*. To select channels, simply click and drag to highlight a section. Here's a demonstration using the `source_sample.Spe` file, where we try to select a Cesium isotope's photo-peak:
![Sample of drag select](https://github.com/ocket8888/maestroAnalyze/blob/master/source_sample.gif?raw=true)
Additionally, if you had Regions of Interest (ROIs) saved in your spectrum, they will be highlighted in green. For example, this is what you should see if you load `roi_sample.Spe` into maestroAnalyze:
![Sample of background radiation spectrum](https://github.com/ocket8888/maestroAnalyze/blob/master/roi_sample.png?raw=true)
You can use the left and right arrow keys to cycle through selections of each ROI in turn like so:
![Sample of background radiation spectrum](https://github.com/ocket8888/maestroAnalyze/blob/master/roi_sample.gif?raw=true)
