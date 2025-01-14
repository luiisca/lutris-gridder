# Lutris Cover Art Downloader

A Python tool to automatically download and transform cover art from SteamGridDB for your Lutris games library.

![Before and After](https://api.placeholder.com/600x300)

## Features

- Downloads cover art and banners from SteamGridDB
- Supports both vertical covers (600x900) and horizontal banners (460x215)
- Automatic or manual cover selection mode
- Crops and resizes images to maintain consistent dimensions
- Clean terminal UI with image previews
- Supports batch processing of your entire library
- Respects existing covers with option to replace all

## Requirements

- Python 3.7+
- Lutris installed and configured
- SteamGridDB API key

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/lutris-cover-art-downloader
   cd lutris-cover-art-downloader
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Getting Started

1. Get a SteamGridDB API key:
   - Visit [SteamGridDB](https://www.steamgriddb.com/)
   - Create an account or log in
   - Go to Preferences > API
   - Generate a new API key

2. Run the script:
   ```bash
   python3 lutris_cover_art.py
   ```

3. On first run:
   - Enter your SteamGridDB API key when prompted
   - The key will be saved for future use

## Usage

The script will guide you through several options:

1. Select cover art type:
   - Banner (460x215) - Horizontal banners for grid view
   - Vertical (600x900) - Vertical covers for list view

2. For vertical covers, choose whether to crop images to fit

3. Select download mode:
   - Auto - Automatically uses the first available cover
   - Manual - Shows previews and lets you choose from available covers

4. Choose whether to replace existing covers:
   - Yes - Downloads new covers for all games
   - No - Skips games that already have covers

## The Process

1. The script reads your Lutris database
2. For each game:
   - Searches SteamGridDB for matching artwork
   - Downloads available options
   - Processes images to match Lutris requirements
   - Saves artwork in the correct Lutris cache directory

## Directory Structure

Covers are saved in the following locations:
- Vertical covers: `~/.cache/lutris/coverart/`
- Banners: `~/.cache/lutris/banners/`

## Configuration

The script stores its configuration in:
```
~/.config/lutris-gridder/api_key.json
```

## Known Issues

- Some games might not be found on SteamGridDB
- Image processing may take longer for larger libraries
- Restart Lutris to see the changes take effect

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [SteamGridDB](https://www.steamgriddb.com/) for providing the artwork database
- [Lutris](https://lutris.net/) for the amazing game platform
- All the artists who contribute artwork to SteamGridDB
