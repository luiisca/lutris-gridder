from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": [
        "aiohttp",
        "inquirer",
        "PIL",
        "requests",
        "rich",
        "rich_pixels",
    ],
    "includes": [
        "PIL.Image",
        "rich.console",
        "rich.layout",
        "rich.live",
        "rich.panel",
        "rich.text",
        "asyncio",
        "sqlite3",
    ],
}

setup(
    name="lutris-gridder",
    version="1.1.0",
    description="Download and transform cover art from SteamGridDB for Lutris games",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            script="src/cover_downloader.py", 
            target_name="lutris-gridder",
        )
    ]
)
