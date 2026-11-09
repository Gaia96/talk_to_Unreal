# 01 · Prerequisites

You need four things: Unreal Engine 5.6, a C++ toolchain (to compile one plugin), Python 3.10 or newer, and Git.

## Hardware

Two programs run on your machine: the Unreal editor and the Python server. Their needs add up, and the server is the unusual one.

### Unreal Engine 5.6 (figures published by Epic)

| System | Minimum (Epic) | Recommended (Epic) |
|---|---|---|
| Windows | Windows 10 64-bit, quad-core Intel or AMD at 2.5 GHz or faster, 8 GB RAM, DirectX 11 or 12 graphics card | Windows 11, quad-core at 2.5 GHz or faster, 32 GB RAM, 8 GB or more of video memory, DirectX 12 card |
| Linux | as above | Ubuntu 22.04, quad-core at 2.5 GHz or faster, 32 GB RAM, 8 GB or more of video memory (GeForce RTX 2080 class). Vulkan drivers: NVIDIA 570 or newer, AMD RADV 24.2.8 or newer |
| macOS | Apple Silicon (M1 or M2), 16 GB of memory, macOS Sonoma 14 or newer | Apple Silicon M3, 32 GB or more |

Sources: [Hardware and Software Specifications](https://dev.epicgames.com/documentation/unreal-engine/hardware-and-software-specifications-for-unreal-engine), [Linux requirements](https://dev.epicgames.com/documentation/unreal-engine/linux-development-requirements-for-unreal-engine), [macOS requirements](https://dev.epicgames.com/documentation/unreal-engine/macos-development-requirements-for-unreal-engine), as read in November 2026. Epic's pages change with each release and some figures differ between pages (for example the macOS minimum version): check them before you buy or install anything.

### The Python server (measured by the authors)

Measured on an Intel Core i7-14650HX (24 threads) with an NVIDIA RTX 4050 Laptop GPU (6 GB), NVIDIA driver 580, Linux:

| | On the GPU (NVIDIA, CUDA) | On the CPU |
|---|---|---|
| Memory taken by the server | 2.3 GB of video memory | 2.6 GB of RAM after start, 3.8 GB after a few queries |
| Time per query (server side, after the first one) | about 35 ms | about 0.6 s |
| First start | downloads 4.5 GB of models | same |

On a slower CPU the time per query grows; with fewer cores, expect seconds, not tenths of a second. The server runs without a GPU, and on a Mac it always runs on the CPU.

### What this guide asks of the PC

All on one machine (Unreal editor + server):

| | Minimum | Comfortable |
|---|---|---|
| CPU | 64-bit, 4 cores at 2.5 GHz or faster | 8 cores or more |
| RAM | **16 GB**: the editor plus about 4 GB for the server on the CPU. This figure is our estimate from the measurements above; it was not tested on a 16 GB machine. 8 GB is not enough for both. | 32 GB |
| Graphics | A GPU supported by Unreal 5.6 (DirectX 12 / Vulkan / Metal), **6 GB of video memory**: the amount of the machine this guide was run on. Less was not tested. | 8 GB or more |
| Free disk | 90 GB: measured on Linux, engine 64 GB, Python environment with CUDA PyTorch 5.8 GB, Hugging Face cache 6.5 GB (the two models used here are about 4.5 GB of it). The Windows and macOS engine installs have a similar order of size. | An SSD |
| Internet | Needed once, for the engine, the plugin, PyTorch and the models. Afterwards the project runs offline. | |
| System | Windows 10 or 11 64-bit; Linux with Vulkan drivers as above; macOS on Apple Silicon | |

**If the GPU is shared between the editor and the server** and runs out of video memory, start the server on the CPU ([04](04-python-server.md#43-start-the-server)).

### If the PC is below this minimum

**Do not install an older Unreal version.** The guide does not apply to it, and the server (the heavy part) is exactly as heavy. Options that keep Unreal 5.6 and the guide:

- **Server on the CPU** (`CUDA_VISIBLE_DEVICES=-1`): no video memory used, slower queries.
- **Lighter cross-encoder** (`RERANKER=cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`): about a fifth of the size, less reliable ([04](04-python-server.md#43-start-the-server)).
- **Server on another computer** (a lab machine or a colleague's PC) while Unreal runs on yours: see [08](08-extend.md#ideas-and-warnings), *Another machine*. Not tested for this guide.

If even the Unreal editor does not run on the machine, this project cannot be done on it.

## Unreal Engine 5.6

Install **5.6**, not an older and not a newer version. The plugin used in [03](03-varest-plugin.md) has one branch per engine version (checked in November 2026: branches `5.4` to `5.8`, none for 4.x), and the whole guide, including the pasteable graphs, is written for 5.6.

**Windows**

1. Install the Epic Games Launcher from <https://www.unrealengine.com/download> and sign in with an Epic account.
2. Library → **+** next to *Engine Versions* → choose **5.6.x** → **Install**. Leave the default components.
3. Default location: `C:\Program Files\Epic Games\UE_5.6`. In every terminal where you run commands from this guide:

```powershell
$UE_ROOT = "C:\Program Files\Epic Games\UE_5.6"
```

**macOS**

1. Install the Epic Games Launcher from <https://www.unrealengine.com/download> and sign in.
2. Library → **+** next to *Engine Versions* → **5.6.x** → **Install**.
3. Default location: `/Users/Shared/Epic Games/UE_5.6`.

```bash
export UE_ROOT="/Users/Shared/Epic Games/UE_5.6"
```

**Linux**

Epic does not ship the launcher for Linux. Download the prebuilt Linux engine **5.6.x** from <https://www.unrealengine.com/linux> (requires an Epic account), extract it anywhere without spaces in the path, and set:

```bash
export UE_ROOT="$HOME/UnrealEngine/Linux_Unreal_Engine_5.6.0"   # adjust to where you extracted it
```

The path above is only an example: use the folder where **you** extracted the engine. Check it:

```bash
ls "$UE_ROOT/Engine/Build/BatchFiles/Linux/Build.sh"
```

The command must print the path of the file. If it says *No such file or directory*, `UE_ROOT` points to the wrong folder.

`export` sets the variable only in the terminal where you typed it, and it can be typed from any directory. A new terminal window starts without it: type the line again, or append it to `~/.bashrc` (Linux) or `~/.zshrc` (macOS) to have it in every new terminal. On Windows, use `$UE_ROOT = "..."` in each PowerShell window, or add it to your PowerShell profile (`notepad $PROFILE`).

Also check that `"$UE_ROOT/Engine/Binaries/Linux/UnrealEditor"` exists. The binary engine bundles its own compiler toolchain; nothing else needs to be installed to build a plugin.

## C++ toolchain (needed to compile VaRestX)

Everything you build in the editor in [02](02-unreal-project.md) and [06](06-blueprints.md) is Blueprints and content, which needs no compiler. The VaRestX plugin, however, is distributed as source and **must be compiled once** ([03](03-varest-plugin.md)), so a C++ toolchain is required on Windows and macOS.

**Windows**: install **Visual Studio 2022** (Community is enough) from <https://visualstudio.microsoft.com/>. In the installer, select the workload **Game development with C++**. Also tick, in *Individual components*, **.NET Framework 4.8 SDK** and the latest **Windows 11 SDK** (or Windows 10 SDK). Epic's list of exact requirements for 5.6 is in the documentation page *Setting Up Visual Studio Development Environment for C++ Projects in Unreal Engine*; follow it if it differs from the list above.

**macOS**: install **Xcode** from the App Store, start it once to accept the licence, and install the command-line tools:

```bash
xcode-select --install
```

**Linux**: nothing to install.

## Python 3.10 or newer

The server was run with Python 3.12. Use 3.10 to 3.12.

**Windows**: install from <https://www.python.org/downloads/windows/>. Tick **Add python.exe to PATH** in the installer. Check:

```powershell
py -3.12 --version
```

**macOS**: install from <https://www.python.org/downloads/macos/>, or with Homebrew (`brew install python@3.12`). Check:

```bash
python3 --version
```

**Linux**: Debian/Ubuntu/Mint:

```bash
sudo apt install python3 python3-venv python3-pip
python3 --version
```

## Git

**Windows**: <https://git-scm.com/download/win> (default options). **macOS**: `git --version` offers to install it with the command-line tools. **Linux**: `sudo apt install git`.

```bash
git --version
```

## Get this repository

Everything in the guide happens inside a local copy of this repository: the Unreal project of [02](02-unreal-project.md) is created in it, and the commands of [03](03-varest-plugin.md) and [04](04-python-server.md) are run from it. Make the copy once, now, and in the right place.

### Choose where to put it

The copy will grow to several GB once you create the Unreal project in it. Choose the folder with these rules:

- **A short path with no spaces**, for example `C:\dev` on Windows or `~/dev` on Linux and macOS. Unreal Engine and its build tools fail on long paths (Windows limits a full path to 260 characters) and on spaces in some steps.
- **Not inside a synchronised folder**: OneDrive, Dropbox, Google Drive, iCloud (on Windows, `Documents` and `Desktop` are often OneDrive folders). The sync client locks and uploads thousands of generated files and breaks builds.
- **Not inside another Git repository.**

### Clone it

Open a terminal (PowerShell on Windows, Terminal on macOS and Linux) and run:

**Windows (PowerShell)**

```powershell
mkdir C:\dev
cd C:\dev
git clone https://github.com/Gaia96/talk_to_Unreal.git
cd talk_to_Unreal
```

**Linux and macOS**

```bash
mkdir -p ~/dev
cd ~/dev
git clone https://github.com/Gaia96/talk_to_Unreal.git
cd talk_to_Unreal
```

Use the `https://` address above. The `git@github.com:...` (SSH) address needs a key configured on your GitHub account and is not needed for a public repository.

Check that you are in the right folder:

```bash
ls
```

(on Windows PowerShell `dir`). The listing must show `docs`, `server` and `project-files`. The folder `ColorCubeChat` is not there yet: you create it in [02](02-unreal-project.md). From now on, "the repository root" in this guide means this folder.

If `git clone` answers *destination path 'talk_to_Unreal' already exists and is not an empty directory*, you already cloned it (or unpacked something with that name) here: either `cd talk_to_Unreal` and continue, or rename the old folder.

### Do not use "Download ZIP"

GitHub's green **Code** button also offers *Download ZIP*. It gives you the files but no Git history, so you cannot update later with `git pull`, and the unpacked folder is called `talk_to_Unreal-main`, which does not match the name used in the guide. Use `git clone`.

### Keep your own work apart

You will probably change files in this repository (the catalog in `server/catalog/`, your own scenario, notes). Two ways to do it without trouble:

- **Fork first.** On GitHub press **Fork**, then clone *your* fork (`https://github.com/<your-user>/talk_to_Unreal.git`) with the commands above. You can then `git push` your changes to your own copy. You cannot push to the original repository, and that is intended.
- **Or work on a branch** of the plain clone: `git switch -c my-work`. Your changes stay on that branch and the original `main` stays clean.

Two things are never committed, because `.gitignore` excludes them: the Unreal project folder `ColorCubeChat/` (large, generated) and the Python virtual environment `.venv/`. If `git status` lists either of them, do not force-add them with `git add -f`.

### Get later corrections

The guide is updated when errors are found. To get the new version, from the repository root:

```bash
git status
git pull
```

`git status` must say *nothing to commit, working tree clean* before you pull. Your `ColorCubeChat/` folder is not affected by `git pull`. If you changed tracked files and `git pull` refuses to run, save your changes first: `git stash`, then `git pull`, then `git stash pop`.

## Editor language

Set the Unreal editor to English before you follow [06](06-blueprints.md) (the guide uses the English node names). You can do it after you create the project, in [02](02-unreal-project.md): Edit → **Editor Preferences** → type `language` in the search box → **Region & Language** → **Editor Language** = **English**. Restart the editor when asked. The setting belongs to your user, not to the project.

Next: [02 · The Unreal project](02-unreal-project.md).
