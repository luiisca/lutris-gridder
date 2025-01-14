# A setup script to demonstrate the use of pillow
#
# Run the build process by running the command 'python setup.py build'
#
# If everything works well you should find a subdirectory in the build
# subdirectory that contains the files needed to run the script without Python

from cx_Freeze import setup

setup(
    name="lutris_gridder",
    version="1.1.0",
    description="Download and transform cover art from SteamGridDB for your Lutris games library",
    executables=["src/cover_downloader.py"],
)
