# Barotrauma Modding Tool
![GitHub release (latest by date)](https://img.shields.io/github/v/release/themanyfaceddemon/Mod_Loader?label=release)

### Overview
`Barotrauma Modding Tool` - This tool is designed to ease the headache of managing modifications. It currently supports the following features:

- **Mod Conflict Detection**: Scans and identifies overwrites between mods to streamline conflict management.
- **Dependency-Aware Sorting**: Automatically sorts mods based on registered dependencies, ensuring they load in the correct order.
- **Easy Integration for Modders**: Simple setup that doesn’t require interaction with the main repository. Examples can be found [here](#examples)

---

## Examples
- [Example of metadata for sorting modifications](./examples/metadata.xml)
- [Example of disabled xml files from modifications](./examples/modparts.xml)
- [Examples README](./examples/README.md): Detailed explanation of the example files and their usage.

---

## Requirements
- [Python 3.12 or higher](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
---

## Installation

### Option 1: Download the Release

1. Go to the [release page](https://github.com/themanyfaceddemon/Barotrauma_Modding_Tool/releases/latest) on GitHub.
2. Download the latest version of the package suitable for your operating system.
3. Extract the archive to a convenient location on your computer.
4. Run the executable file.

---

### Option 2: Clone the Repository and Build

If you want to build `Barotrauma Modding Tool` from the source, follow these steps:

#### 1. Install Python

Download and install [Python 3.12 or higher](https://www.python.org/downloads/) if it is not already installed.

#### 2. Install Git

Download and install [Git](https://git-scm.com/downloads) for repository management and cloning the code.

#### 3. Clone the Repository

Open your terminal or command prompt and run the following command to clone the repository:

```bash
git clone https://github.com/themanyfaceddemon/Barotrauma_Modding_Tool.git
```

#### 4. Install Dependencies

Navigate to the project directory and install the required Python dependencies:

```bash
cd Barotrauma_Modding_Tool
pip install -r requirements.txt
```

---

### Running the Application

#### For Windows

Run the application using the `run_app.bat` file:

```bash
run_app.bat
```

#### For Linux and macOS

Run the application using the `run_app.sh` file:

```bash
./run_app.sh
```

> [!NOTE]
> Make the script executable before running:
> ```bash
> chmod +x run_app.sh
> ```

---

## Support

If you encounter issues with `Barotrauma Modding Tool`, please open an issue in the repository or contact the developers for assistance.
---

## License
See the [LICENSE](./LICENSE) file for details.
