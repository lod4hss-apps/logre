# LOGRE (LOcal GRaph Editor)

Logre is an open source tool to work with graphs.

The idea behind the tool is to provide a simple GUI to understand, visualize and edit data in various SPARQL endpoints.

It has been created initially for Geovistory projects, but thanks to its modularity, it can be used by any project.

There are two ways of using Logre:
- Locally (install it yourself on your computer, see below section)
- On the deployed application (see [the online app](https://logre-public.streamlit.app/))

Both of those are exactly the same application, the difference is that the online version allows you to directly use it, without having to install anything.


## How to install and start locally

**Prerequisite**

To run Logre, you will need to have:
- `make` (native on MacOS and Linux, for Windows users, install it with `winget install ezwinports.make`).
- `python3.10` or newer; ***may*** also work with older version.

**Install**

- Open a Terminal, and change directory to the place where you want to install logre
- Run `git clone https://github.com/geovistory/logre.git`
- Run `cd logre`
- Optinal: run `make install` (optional: when starting the tool, the install process runs anyway)
- Optional: run `make get-sdhss-shacls`: this will fetch all SHACLs profiles from SDHSS

**Start**

In your folder, simply run `make start`, this will update the dependencies, and start the GUI


Happy Graph editing!