"""
File Utilities - Consistent naming and path management
"""
from pathlib import Path
from datetime import datetime
import os


class FileManager:
    """
    Manages file organization with consistent naming conventions

    Folder Structure:
    - input/       - Original documents (user uploads)
    - processed/   - Detected entities (JSON + annotated PDF)
    - output/      - Redacted documents (final output)

    Naming Convention:
    - Input:     original_filename.pdf
    - Processed: YYYYMMDD_HHMMSS_original_filename_PROCESSED.pdf
    - Output:    YYYYMMDD_HHMMSS_original_filename_REDACTED.pdf
    - Mapping:   YYYYMMDD_HHMMSS_original_filename_MAPPING.csv
    """

    def __init__(self, base_dir: str = None):
        """
        Initialize file manager

        Args:
            base_dir: Base directory for all operations (default: current dir)
        """
        if base_dir is None:
            base_dir = Path(__file__).parent
        else:
            base_dir = Path(base_dir)

        self.base_dir = base_dir
        self.input_dir = base_dir / "input"
        self.processed_dir = base_dir / "processed"
        self.output_dir = base_dir / "output"

        # Create directories if they don't exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories"""
        for directory in [self.input_dir, self.processed_dir, self.output_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_timestamp() -> str:
        """
        Get current timestamp in YYYYMMDD_HHMMSS format

        Returns:
            Timestamp string
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def extract_base_name(file_path: str) -> str:
        """
        Extract base filename without extension and timestamp

        Args:
            file_path: Full or relative path to file

        Returns:
            Base filename (e.g., "document.pdf" → "document")
        """
        path = Path(file_path)
        name = path.stem

        # Remove timestamp prefix if present (YYYYMMDD_HHMMSS_)
        if len(name) > 16 and name[8] == '_' and name[15] == '_':
            # Check if starts with valid timestamp pattern
            if name[:8].isdigit() and name[9:15].isdigit():
                name = name[16:]  # Remove "YYYYMMDD_HHMMSS_" prefix

        # Remove suffixes (_REDACTED, _PROCESSED, _MAPPING)
        for suffix in ['_REDACTED', '_PROCESSED', '_MAPPING']:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        return name

    def generate_processed_path(self, input_file: str) -> Path:
        """
        Generate path for processed file (with detected entities)

        Args:
            input_file: Original input file path

        Returns:
            Path to processed file
        """
        base_name = self.extract_base_name(input_file)
        ext = Path(input_file).suffix
        timestamp = self.get_timestamp()

        filename = f"{timestamp}_{base_name}_PROCESSED{ext}"
        return self.processed_dir / filename

    def generate_output_path(self, input_file: str) -> Path:
        """
        Generate path for redacted output file

        Args:
            input_file: Original input file path

        Returns:
            Path to redacted output file
        """
        base_name = self.extract_base_name(input_file)
        ext = Path(input_file).suffix
        timestamp = self.get_timestamp()

        filename = f"{timestamp}_{base_name}_REDACTED{ext}"
        return self.output_dir / filename

    def generate_mapping_path(self, input_file: str) -> Path:
        """
        Generate path for mapping table CSV

        Args:
            input_file: Original input file path

        Returns:
            Path to mapping CSV file
        """
        base_name = self.extract_base_name(input_file)
        timestamp = self.get_timestamp()

        filename = f"{timestamp}_{base_name}_MAPPING.csv"
        return self.output_dir / filename

    def generate_entities_json_path(self, input_file: str) -> Path:
        """
        Generate path for entities JSON file (saved in processed/)

        Args:
            input_file: Original input file path

        Returns:
            Path to entities JSON file
        """
        base_name = self.extract_base_name(input_file)
        timestamp = self.get_timestamp()

        filename = f"{timestamp}_{base_name}_ENTITIES.json"
        return self.processed_dir / filename

    def move_to_input(self, file_path: str) -> Path:
        """
        Move uploaded file to input directory

        Args:
            file_path: Path to uploaded file

        Returns:
            New path in input directory
        """
        source = Path(file_path)
        destination = self.input_dir / source.name

        # Move file if not already in input directory
        if source.parent != self.input_dir:
            if destination.exists():
                # If file exists, add timestamp to avoid overwrite
                timestamp = self.get_timestamp()
                base_name = source.stem
                ext = source.suffix
                destination = self.input_dir / f"{timestamp}_{base_name}{ext}"

            source.rename(destination)

        return destination

    def get_file_paths(self, input_file: str) -> dict:
        """
        Get all related file paths for a document

        Args:
            input_file: Input file path

        Returns:
            Dict with all file paths:
            {
                'input': Path to input file,
                'processed': Path to processed file,
                'output': Path to redacted output,
                'mapping': Path to mapping CSV,
                'entities_json': Path to entities JSON
            }
        """
        return {
            'input': Path(input_file),
            'processed': self.generate_processed_path(input_file),
            'output': self.generate_output_path(input_file),
            'mapping': self.generate_mapping_path(input_file),
            'entities_json': self.generate_entities_json_path(input_file)
        }

    def list_files(self, directory: str = 'input') -> list:
        """
        List all files in a directory

        Args:
            directory: 'input', 'processed', or 'output'

        Returns:
            List of file paths
        """
        dir_map = {
            'input': self.input_dir,
            'processed': self.processed_dir,
            'output': self.output_dir
        }

        target_dir = dir_map.get(directory, self.input_dir)

        if not target_dir.exists():
            return []

        return [f for f in target_dir.iterdir() if f.is_file()]

    def clean_directory(self, directory: str, older_than_days: int = None):
        """
        Clean files from a directory (optionally only files older than X days)

        Args:
            directory: 'input', 'processed', or 'output'
            older_than_days: Only delete files older than this many days (None = all)
        """
        dir_map = {
            'input': self.input_dir,
            'processed': self.processed_dir,
            'output': self.output_dir
        }

        target_dir = dir_map.get(directory)
        if not target_dir or not target_dir.exists():
            return

        if older_than_days is None:
            # Delete all files
            for file in target_dir.iterdir():
                if file.is_file():
                    file.unlink()
        else:
            # Delete only old files
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=older_than_days)

            for file in target_dir.iterdir():
                if file.is_file():
                    file_time = datetime.fromtimestamp(file.stat().st_mtime)
                    if file_time < cutoff:
                        file.unlink()


# Example usage
if __name__ == "__main__":
    fm = FileManager()

    # Test filename generation
    test_file = "CV_Luca_Cervone_Ita.pdf"

    print("File Manager - Naming Convention Test")
    print("=" * 60)
    print(f"\nInput file: {test_file}")

    paths = fm.get_file_paths(test_file)

    print(f"\nGenerated paths:")
    print(f"  Input:        {paths['input']}")
    print(f"  Processed:    {paths['processed'].name}")
    print(f"  Output:       {paths['output'].name}")
    print(f"  Mapping:      {paths['mapping'].name}")
    print(f"  Entities JSON: {paths['entities_json'].name}")

    print(f"\nExample filenames:")
    timestamp = FileManager.get_timestamp()
    print(f"  {timestamp}_CV_Luca_Cervone_Ita_PROCESSED.pdf")
    print(f"  {timestamp}_CV_Luca_Cervone_Ita_REDACTED.pdf")
    print(f"  {timestamp}_CV_Luca_Cervone_Ita_MAPPING.csv")
