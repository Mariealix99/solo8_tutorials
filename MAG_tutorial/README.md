# [MAG tutorial](tutorial)

This Data Analysis Tutorial for MAG will guide you though getting hold of MAG
data from the ESA Solar Orbiter Archive (SOAR) and using that data. We will
describe the different types of MAG data products that are available on the
SOAR, and what data each of the products contain. We will also provide several
examples of how you can use MAG data products.

## Setup Instructions

### Create a Conda Environment

To run these notebooks, we recommend creating a dedicated conda environment with all required packages. You can do this in two ways:

**Option 1: Use the provided environment file (Recommended)**

```bash
conda env create -f environment.yml
conda activate solo8-mag
jupyter notebook
```

This will create an environment called `solo8-mag` with all necessary dependencies, including:
- Python 3.12
- JupyterLab and Jupyter
- SunPy with all extras
- Data analysis tools (astropy, scipy, numpy, matplotlib)
- Strauss library for sonification notebook
- FFmpeg for multimedia support

**Option 2: Install in existing environment**

If you already have the `solo8` environment from the main repository, you can install additional packages:

```bash
conda activate solo8
pip install git+https://github.com/james-trayford/strauss.git@animation ffmpeg-python wavio
```

### System Dependencies

The sonification notebook requires FFmpeg. If not already installed:

**macOS (via Homebrew):**
```bash
brew install ffmpeg
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## User Guide

### `data.ipynb`

In this notebook you will be guided through downloading MAG data using the
Web API provided by the SOAR and also downloading MAG data using SunPy.

### `analysis.ipynb`

In this notebook you will be guided through a practical example of aquiring
SPICE data to calculate the Parker Spiral angle from MAG data.

### `metadata.ipynb`

In this notebook you will look in detail at MAG data files, learn mroe about
the metadata that is included with every publicly released L2 MAG data product
and how to use this information to better understand, and correctly use MAG
data products.

### `sonification.ipynb`

In this notebook you will learn about sonification - converting data into sound. 
We use the Strauss library to create audio representations of Solar Orbiter data. 
This notebook demonstrates creative approaches to data exploration and accessibility 
through multimodal representations.

**Note:** The animation features in this notebook require additional TTS (text-to-speech) 
dependencies that have compatibility constraints. The core sonification functionality 
works without these dependencies.

## License

[MAG tutorial](tutorial) is released under the [MIT license][license].

[license]: LICENSE.md
[tutorial]: https://github.com/SolarOrbiterWorkshop/solo8_tutorials/tree/main/MAG_tutorial
[sml]: http://www.imperial.ac.uk/space-and-atmospheric-physics/research/areas/space-magnetometer-laboratory/
