#!/usr/bin/env python3
"""
Lutris Cover Art Downloader
A tool to download and transform cover art from SteamGridDB for Lutris games.
"""

import sys
import logging
from dataclasses import dataclass
from typing import Optional, List, Tuple
import requests
import sqlite3
from PIL import Image
from pathlib import Path
import json
import inquirer

# Configuration


@dataclass
class Config:
    BANNER_DIMENSIONS: Tuple[int, int] = (574, 215)  # 8:3 ratio
    COVER_DIMENSIONS: Tuple[int, int] = (675, 900)   # 3:4 ratio
    API_BASE_URL: str = "https://www.steamgriddb.com/api/v2"
    CONFIG_DIR: Path = Path.home() / ".config" / "lutris-gridder"
    API_KEY_FILE: Path = CONFIG_DIR / "api_key.json"


class ImageProcessor:
    """Handles all image processing operations."""

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


class SteamGridDBAPI:
    """Handles all API interactions with SteamGridDB."""

    def __init__(self, auth_token: str):
        self.auth_headers = {'Authorization': f'Bearer {auth_token}'}
        self.base_url = Config.API_BASE_URL

    def search_games(self, game_names: List[str]):
        """Search for a list of game names and return the first found game ID."""
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
                if games := data["data"]:
                    return games
                else:
                    logging.warning(f"No results found for game: {game_name}")
                    return self.search_games(game_names[1:])
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {str(e)}")
            return self.search_games(game_names[1:])

    def get_cover_url(self, games: List, dimension_str: str) -> Optional[str]:
        """Get the cover URL for a specific game."""
        try:
            response = requests.get(
                # TODO: may wanna come back to dimensions={dimensions}
                f"{self.base_url}/grids/game/{
                    games[0]["id"]}?dimensions={dimension_str}",
                headers=self.auth_headers
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("data"):
                return self.get_cover_url(games[1:], dimension_str)

            return data["data"][0]["url"]

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get cover URL: {str(e)}")
            return self.get_cover_url(games[1:], dimension_str)


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

    def _get_cover_type(self) -> Tuple[str, Path, Tuple[int, int]]:
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
            return (
                "460x215",
                Path.home() / ".cache/lutris/banners",
                Config.BANNER_DIMENSIONS
            )
        else:
            return (
                "600x900",
                Path.home() / ".cache/lutris/coverart",
                Config.COVER_DIMENSIONS
            )
    def _get_crop_to_fit(self) -> bool:
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
            return True
        else:
            return False

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

    def process_games(self):
        """Main method to process all games and download/transform cover art."""
        dimension_str, cover_path, target_dimensions = self._get_cover_type()
        crop_to_fit = False
        if target_dimensions == Config.COVER_DIMENSIONS:
            crop_to_fit = self._get_crop_to_fit()

        cover_path.mkdir(parents=True, exist_ok=True)

        games = self.lutris_db.get_all_games()
        total_games = len(games)

        print(f"\nProcessing {total_games} games...")

        for index, (game_name, game_slug) in enumerate(games, 1):
            cover_file = cover_path / f"{game_slug}.jpg"

            if cover_file.exists():
                print(f"[{index}/{total_games}] Cover exists for: {game_name}")
                continue

            print(f"[{index}/{total_games}] Processing: {game_name}")

            games = self.api.search_games([game_name, game_slug])
            if not games:
                continue

            cover_url = self.api.get_cover_url(games, dimension_str)
            if not cover_url:
                continue

            try:
                # Download the cover
                response = requests.get(cover_url)
                response.raise_for_status()

                # Save the original
                cover_file.write_bytes(response.content)

                # Transform the aspect ratio
                if crop_to_fit:
                    ImageProcessor.crop_to_fit(
                    cover_file, target_dimensions)

                print(f"Successfully processed img for: {game_slug}")

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

        downloader.process_games()

        print("\nAll done! Restart Lutris for the changes to take effect.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
