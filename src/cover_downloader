#!/usr/bin/env python3
"""
Lutris Cover Art Downloader
A tool to download and transform cover art from SteamGridDB for Lutris games.
"""

import sys
import logging
from dataclasses import dataclass
from typing import Dict, Literal, Optional, List, Tuple
import requests
import sqlite3
from PIL import Image
from pathlib import Path
import json
import inquirer
import tempfile
from rich.layout import Layout
from rich.live import Live
from rich.console import Console, Group
from rich.text import Text
from rich_pixels import Pixels
from rich import box
from rich.panel import Panel
import asyncio
import aiohttp

# Configuration
@dataclass
class Config:
    class BANNER:
        dimensions: Tuple[int, int] = (574, 215) # 8:3 ratio
        api_dimensions: str = "460x215"
        path: Path = Path.home() / ".cache/lutris/banners"
    class COVER:
        dimensions: Tuple[int, int] = (675, 900) # 3:4 ratio
        api_dimensions: str = "600x900"
        path: Path = Path.home() / ".cache/lutris/coverart"
    API_BASE_URL: str = "https://www.steamgriddb.com/api/v2"
    CONFIG_DIR: Path = Path.home() / ".config" / "lutris-gridder"
    API_KEY_FILE: Path = CONFIG_DIR / "api_key.json"
    TYPE: Literal["banner", "cover"] = "banner"
    CROP_TO_FIT: bool = True
    MODE: Literal["auto", "manual"] = "auto"
    REPLACE_ALL: bool = False


class ImageProcessor:
    """Handles all image processing operations."""

    @staticmethod
    async def download_image(session: aiohttp.ClientSession, url: str) -> Optional[bytes]:
        """Asynchronously download an image."""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                return None
        except Exception as e:
            logging.error(f"Failed to download image: {str(e)}")
            return None

    @staticmethod
    def create_horizontal_layout(images: Dict[int, Path], covers: List[dict]) -> Layout:
        """Create a horizontal layout for images that adapts to content height."""
        layout = Layout()
        if Config.TYPE == 'banner':
            # For banners, create a vertical stack without fixed ratios
            panels = []
            for idx, img_path in images.items():
                try:
                    pixels = Pixels.from_image_path(img_path)
                    caption = Text.assemble(
                        ("Selection: ", "bright_white"),
                        (f"Option {idx + 1}\n", "bright_yellow"),
                    )
                    
                    # Create individual panel for each image
                    panel = Panel(
                        Group(
                            pixels,
                            Text(""),  # Spacer
                            caption
                        ),
                        box=box.ROUNDED,
                        padding=(0, 1),
                    )
                    panels.append(panel)
                except Exception as e:
                    logging.error(f"Failed to create panel for image {idx}: {str(e)}")
            
            # Return a group of panels stacked vertically
            return Group(*panels)
        else:
            layout.split_row(*[
                Layout(name=str(idx))
                for idx in range(len(images))
            ])
            for idx, img_path in images.items():
                try:
                    pixels = Pixels.from_image_path(img_path)
                    caption = Text.assemble(
                        ("Selection: ", "bright_white"),
                        (f"Option {idx + 1}\n", "bright_yellow"),
                    )
                    
                    # Combine image and caption in a panel
                    cell_content = Group(
                        pixels,
                        Text(""),  # Spacer
                        caption
                    )
                    layout[str(idx)].update(
                        Panel(
                            cell_content,
                            box=box.ROUNDED,
                            padding=(0, 1),
                        )
                    )
                except Exception as e:
                    logging.error(f"Failed to create layout: {str(e)}")
        
            return layout


    @staticmethod
    def get_new_size(img: Image.Image) -> Tuple[int, int]:
        """Calculate appropriate dimensions for terminal display."""
        console = Console()
        terminal_width = console.width
        preview_height = min(50, console.height - 5)
        
        # Calculate new dimensions preserving aspect ratio
        aspect_ratio = img.width / img.height
        new_width = min(terminal_width, img.width)
        new_height = int(new_width / aspect_ratio)
        
        # If height is too tall, scale down based on height
        if new_height > preview_height:
            new_height = preview_height
            new_width = int(new_height * aspect_ratio)
            
        return new_width, new_height

    @staticmethod
    def process_cover_image(img_path: Path) -> None:
        """Process a single cover image for display."""
        with Image.open(img_path) as img:
            if Config.TYPE == 'banner' or not Config.CROP_TO_FIT:
                img = img.convert('RGB')
            
            # Get appropriate dimensions
            new_width, new_height = ImageProcessor.get_new_size(img)
            
            # Resize image
            resized_img = img.resize((new_width, new_height))
            
            # Save resized image
            resized_img.save(img_path)

    @staticmethod
    async def cover_selection(covers: List[dict], game_name: str) -> Optional[str]:
        """Prompt user to select from available covers with parallel loading."""
        if not covers:
            return None

        print(f"\nLoading covers for {game_name}...")
        
        choices = [(f"Option {i + 1} {cover['url']}", cover['url']) 
                  for i, cover in enumerate(covers[:5])]
        choices.append(("Skip this game", None))
        
        console = Console()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            images: Dict[int, Path] = {}
            
            async with aiohttp.ClientSession() as session:
                download_tasks = []
                for i, cover in enumerate(covers[:5]):
                    task = asyncio.create_task(
                        ImageProcessor.download_image(session, cover['url'])
                    )
                    download_tasks.append((i, task))

                layout = Layout()
                console.height = console.height - 20

                with Live(layout, refresh_per_second=4, console=console, auto_refresh=False) as live:
                    for i, task in download_tasks:
                        try:
                            image_data = await task
                            if image_data:
                                img_path = temp_dir_path / f"image_{i}.jpg"
                                img_path.write_bytes(image_data)
                                
                                if Config.TYPE == 'cover' and Config.CROP_TO_FIT:
                                    ImageProcessor.crop_to_fit(img_path)
                                
                                # Process image for display
                                ImageProcessor.process_cover_image(img_path)
                                
                                images[i] = img_path
                                
                                # Update layout with new image
                                live.update(ImageProcessor.create_horizontal_layout(images, covers), refresh=True)
                        except Exception as e:
                            logging.error(f"Failed to process image {i}: {str(e)}")
            
            questions = [
                inquirer.List('cover',
                             message="Select cover art:",
                             choices=[choice[0] for choice in choices],
                             ),
            ]
            
            answer = inquirer.prompt(questions)["cover"]
            return dict(choices)[answer]

    @staticmethod
    def crop_to_fit(image_path: Path, target_dimensions: Tuple[int, int] = (675, 900)) -> None:
        """
        Transform an image to 675x900 by expanding to fill the dimensions and cropping excess.
        The image will be resized to fill the target dimensions completely while maintaining
        aspect ratio, then cropped to fit exactly.
        
        Args:
            image_path (Path): Path to the input image
            target_dimensions (Tuple[int, int]): Target width and height (default: 675x900)
        
        The function will:
        1. Resize the image to fill target dimensions while maintaining aspect ratio
        2. Crop excess portions to achieve exact target dimensions
        3. Save the result as a JPEG with high quality
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if image is in RGBA
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                target_width, target_height = target_dimensions
                target_ratio = target_width / target_height
                current_ratio = img.width / img.height
                
                # Calculate dimensions that will fill the target area
                if current_ratio > target_ratio:
                    # Image is wider than target ratio - match height first
                    new_height = target_height
                    new_width = int(target_height * current_ratio)
                else:
                    # Image is taller than target ratio - match width first
                    new_width = target_width
                    new_height = int(target_width / current_ratio)
                
                # Resize image while maintaining aspect ratio
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Calculate crop box (centered crop)
                left = (new_width - target_width) // 2
                top = (new_height - target_height) // 2
                right = left + target_width
                bottom = top + target_height
                
                # Crop to target size
                final_img = resized_img.crop((left, top, right, bottom))
                
                # Save the final image
                final_img.save(image_path, "JPEG", quality=95)
                
        except Exception as e:
            logging.error(f"Failed to process image {image_path}: {str(e)}")
            raise

    @staticmethod
    def display_terminal_preview(image_url: str, max_height: int = 20) -> None:
        """Display an image preview in the terminal."""
        try:
            # Download image
            response = requests.get(image_url)
            response.raise_for_status()
            
            # Create temporary file for the image
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            
                # Create console instance
                console = Console()
                
                # Calculate terminal dimensions
                terminal_width = console.width
                preview_height = min(50, console.height - 5)

                if Config.TYPE == 'cover' and Config.CROP_TO_FIT:
                    ImageProcessor.crop_to_fit(Path(tmp_path))

                # Open and resize the image with Pillow
                with Image.open(tmp_path) as img:
                    if Config.TYPE == 'banner' or not Config.CROP_TO_FIT:
                        # Convert to RGB if image is in RGBA
                        img = img.convert('RGB')
                    # Calculate new dimensions while preserving aspect ratio
                    aspect_ratio = img.width / img.height
                    new_width = min(terminal_width, img.width)
                    new_height = int(new_width / aspect_ratio)
                    if new_height > preview_height:
                        new_height = preview_height
                        new_width = int(new_height * aspect_ratio)
                    resized_img = img.resize((new_width, new_height))

                    # Save to a temporary file if needed for rich_pixels
                    resized_img.save(tmp_path)

                # Display the resized image using rich_pixels
                console.print(Pixels.from_image_path(tmp_path))
                    
                # Clean up temporary file
                Path(tmp_path).unlink()
            
        except Exception as e:
            logging.error(f"Failed to display preview: {str(e)}")


class SteamGridDBAPI:
    """Handles all API interactions with SteamGridDB."""

    def __init__(self, auth_token: str):
        self.auth_headers = {'Authorization': f'Bearer {auth_token}'}
        self.base_url = Config.API_BASE_URL

    def search_games(self, game_names: List[str]):
        """Search for a list of game names and return all found games."""
        if not game_names:
            return None

        game_name = game_names[0]
        try:
            response = requests.get(
                f"{self.base_url}/search/autocomplete/{game_name}",
                headers=self.auth_headers
            )
            response.raise_for_status()
            data = response.json()
            if data.get("data"):
                return data["data"]
            else:
                logging.warning(f"No results found for game: {game_name}")
                return self.search_games(game_names[1:])
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {str(e)}")
            return self.search_games(game_names[1:])

    def get_all_covers(self, games: List[dict], dimension_str: str) -> List[dict]:
        """Get all available covers for a specific game."""
        try:
            response = requests.get(
                f"{self.base_url}/grids/game/{games[0]['id']}?dimensions={dimension_str}",
                headers=self.auth_headers
            )
            response.raise_for_status()
            data = response.json()
            if data.get("data"):
                return data["data"]
            else:
                return self.get_all_covers(games[1:], dimension_str)
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get covers: {str(e)}")
            return []


class LutrisDB:
    """Handles all Lutris database operations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._validate_db_path()

    def _validate_db_path(self):
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Lutris database not found at: {self.db_path}")

    def get_all_games(self) -> List[Tuple[str, str]]:
        """Retrieve all game names from the Lutris database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT name, slug FROM games')
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Database error: {str(e)}")
            raise


class Prompter:
    """Handles user input and output."""
    @staticmethod
    def cover_type():
        """Prompt user for cover type and return relevant information."""
        questions = [
            inquirer.List('type',
                          message="Select cover art type:",
                          choices=[
                              'Banner (460x215)',
                              'Vertical (600x900)'
                          ],
                          ),
        ]

        answer = inquirer.prompt(questions)["type"]

        if "Banner" in answer:
            Config.TYPE = "banner"
        else:
            Config.TYPE = "cover"

    @staticmethod
    def crop_to_fit():
        """Prompt user for cover type and return relevant information."""
        questions = [
            inquirer.List('type',
                          message="Crop images to fit?",
                          choices=[
                              'Yes',
                              'No'
                          ],
                          ),
        ]

        answer = inquirer.prompt(questions)["type"]

        if "Yes" in answer:
            Config.CROP_TO_FIT = True
        else:
            Config.CROP_TO_FIT = False

    @staticmethod
    def selection_mode():
        """Prompt user for selection mode and return relevant information."""
        questions = [
            inquirer.List('mode',
                         message="Select cover art download mode:",
                         choices=[
                             'Auto (use first available cover)',
                             'Manual (choose from available covers)'
                         ],
                         ),
        ]
        mode = inquirer.prompt(questions)["mode"]
        if "Auto" in mode:
            Config.MODE = "auto"
        else:
            Config.MODE = "manual"
    
    @staticmethod
    def replace_all():
        """Prompt user for replace all mode."""
        questions = [
            inquirer.List('mode',
                         message="Replace all existing covers?",
                         choices=[
                             'Yes',
                             'No'
                         ],
                         ),
        ]
        mode = inquirer.prompt(questions)["mode"]
        if "Yes" in mode:
            Config.REPLACE_ALL = True
        else:
            Config.REPLACE_ALL = False


class CoverArtDownloader:
    """Main application class for downloading and processing cover art."""

    def __init__(self):
        self.config = self._load_config()
        self.api = SteamGridDBAPI(self.config.get('api_key', ''))
        self.lutris_db = LutrisDB(Path.home() / ".local/share/lutris/pga.db")
        self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def _load_config(self) -> dict:
        """Load configuration from file or create default."""
        Config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        if not Config.API_KEY_FILE.exists():
            Config.API_KEY_FILE.touch()
            with open(Config.API_KEY_FILE, "w") as f:
                f.write(json.dumps({"api_key": ""}, indent=2))

        with open(Config.API_KEY_FILE) as f:
            return json.load(f)

    def _save_config(self, config: dict):
        """Save configuration to file."""
        Config.API_KEY_FILE.write_text(json.dumps(config, indent=2))

    def setup_api_key(self) -> None:
        """Set up the API key interactively. Store API key in the config file."""
        print("\nYou need a SteamGridDB API key to use this script.")
        print("Get one at: https://www.steamgriddb.com/profile/preferences/api")

        api_key = input("\nEnter your SteamGridDB API key: ").strip()

        # Test the API key
        test_api = SteamGridDBAPI(api_key)
        try:
            if test_api.search_games(["test"]):
                self.config['api_key'] = api_key
                self._save_config(self.config)
                self.api = test_api
                print("API key validated and saved successfully!")
            else:
                raise ValueError("Invalid API key")
        except Exception as e:
            print(f"Error validating API key: {str(e)}")
            sys.exit(1)

    async def process_games(self):
        """Main method to process all games and download/transform cover art."""
        Prompter.cover_type()
        if Config.TYPE == "cover":
            Prompter.crop_to_fit()
        Prompter.selection_mode()
        Prompter.replace_all()

        config = Config.COVER if Config.TYPE == "cover" else Config.BANNER
        config.path.mkdir(parents=True, exist_ok=True)
        games = self.lutris_db.get_all_games()
        total_games = len(games)

        print(f"\nProcessing {total_games} games...")

        for index, (game_name, game_slug) in enumerate(games, 1):
            cover_file = config.path / f"{game_slug}.jpg"

            if cover_file.exists() and Config.REPLACE_ALL is False:
                print(f"[{index}/{total_games}] Cover exists for: {game_name}")
                continue

            print(f"[{index}/{total_games}] Processing: {game_name}, {game_slug}")

            found_games = self.api.search_games([game_name, game_slug])
            if not found_games:
                continue

            covers = self.api.get_all_covers(found_games, config.api_dimensions)
            if not covers:
                continue

            try:
                cover_url = None
                if Config.MODE == "manual":
                    cover_url = await ImageProcessor.cover_selection(covers, game_name)
                    if not cover_url:
                        print(f"Skipping {game_name}")
                        continue
                else:
                    cover_url = covers[0]['url']

                # Download the cover
                response = requests.get(cover_url)
                response.raise_for_status()

                # Save the original
                cover_file.write_bytes(response.content)

                # Transform the aspect ratio if needed
                if Config.TYPE == "cover" and Config.CROP_TO_FIT:
                    ImageProcessor.crop_to_fit(cover_file, config.dimensions)

                print(f"Successfully processed cover for: {game_slug}")

            except Exception as e:
                logging.error(f"Failed to process {game_slug}: {str(e)}")
                continue


def main():
    """Entry point of the application."""
    try:
        print("\nWelcome to Lutris Cover Art Downloader!")

        downloader = CoverArtDownloader()

        if not downloader.config.get('api_key'):
            downloader.setup_api_key()

        # Run the async process_games
        asyncio.run(downloader.process_games())

        print("\nAll done! Restart Lutris for the changes to take effect.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
