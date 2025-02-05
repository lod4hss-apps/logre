# LOGRE (LOcal GRaph Editor)

Logre is an open source tool to work with graphs.

The idea behind the tool is to provide a simple GUI to visualize, edit, understand data in various SPARQL endpoints.

It has been created initially for Geovistory projects, but thanks to its modularity, it can be used by any project.

There is two ways of using Logre:
- Locally (install it yourself on you computer, see *How to use/install* section)
- On the deployed application (see []())

Both of those are exactly the same application, the difference is that the online version allows you to directly use it, without having to install anything.


## How to use/install

**Prerequisite**

To run Logre, you will need to have:
- `make` (native on MacOS and Linux, for Windows users, install it with `winget install ezwinports.make`).
- Python3.10 or newer; **May** also work with older version.

**Install**

- Open a Terminal, and change directory to the place where you want to have your tool
- Run `git clone https://github.com/geovistory/logre.git`
- Run `cd logre`
- Run `make install` (optional: when starting the tool, the install process runs anyway)

**Start**

- In your folder, simply run `make start`, this will update the dependencies, and start the GUI


Happy Graph editing!