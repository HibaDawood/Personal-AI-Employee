import os
import shutil
from pathlib import Path
import time
from datetime import datetime
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileDropHandler(FileSystemEventHandler):
    """
    Custom event handler for file system events in the Drop_Zone folder.
    When a file is added to Drop_Zone, it copies the file to Needs_Action
    and creates a metadata file with details about the dropped file.
    """
    
    def __init__(self):
        """
        Initialize the handler with logging and folder paths.
        """
        # Setup logging
        self.logger = self.setup_logging()
        
        # Define folder paths
        self.drop_zone = Path("Drop_Zone")
        self.needs_action = Path("Needs_Action")
        
        # Create directories if they don't exist
        self.needs_action.mkdir(exist_ok=True)
        
        self.logger.info("FileDropHandler initialized")
    
    def setup_logging(self):
        """
        Setup logging to both console and file in Logs folder.
        """
        # Create Logs directory if it doesn't exist
        logs_dir = Path("Logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Create a logger
        logger = logging.getLogger('FileSystemWatcher')
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Create file handler
        log_file = logs_dir / f"filesystem_watcher_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def on_created(self, event):
        """
        Handle file creation events in the watched directory.
        When a file is dropped in Drop_Zone, copy it to Needs_Action
        and create a metadata file.
        """
        # Ignore directory events and hidden files
        if event.is_directory or event.src_path.startswith('.'):
            return
        
        # Convert to Path object for easier manipulation
        file_path = Path(event.src_path)
        
        # Verify the file exists before processing
        if not file_path.exists():
            self.logger.warning(f"File {file_path} does not exist, skipping...")
            return
        
        try:
            # Copy the file to Needs_Action folder
            destination_path = self.needs_action / file_path.name
            shutil.copy2(file_path, destination_path)
            
            # Get file size in KB
            file_size_kb = file_path.stat().st_size / 1024
            
            # Create timestamp
            timestamp = datetime.now().isoformat()
            
            # Create metadata file
            self.create_metadata_file(file_path, file_size_kb, timestamp)
            
            # Log the action
            self.logger.info(f"File {file_path.name} copied to Needs_Action and metadata created")
            
        except Exception as e:
            self.logger.error(f"Error processing file {event.src_path}: {str(e)}")
    
    def on_moved(self, event):
        """
        Handle file move events in the watched directory.
        This handles cases where files are moved into the Drop_Zone.
        """
        # This handles files moved into the drop zone
        if hasattr(event, 'dest_path'):
            dest_path = Path(event.dest_path)
            if not dest_path.is_file():
                return
            
            # Process the moved file similar to created
            try:
                # Copy the file to Needs_Action folder
                destination_path = self.needs_action / dest_path.name
                shutil.copy2(dest_path, destination_path)
                
                # Get file size in KB
                file_size_kb = dest_path.stat().st_size / 1024
                
                # Create timestamp
                timestamp = datetime.now().isoformat()
                
                # Create metadata file
                self.create_metadata_file(dest_path, file_size_kb, timestamp)
                
                # Log the action
                self.logger.info(f"File {dest_path.name} moved to Drop_Zone, copied to Needs_Action and metadata created")
                
            except Exception as e:
                self.logger.error(f"Error processing moved file {event.dest_path}: {str(e)}")

    def create_metadata_file(self, file_path, file_size_kb, timestamp):
        """
        Create a metadata markdown file for the dropped file.
        
        Args:
            file_path (Path): Path to the original file
            file_size_kb (float): Size of the file in kilobytes
            timestamp (str): ISO format timestamp
        """
        try:
            # Create the metadata file name
            metadata_filename = f"FILE_{file_path.name.replace('.', '_')}.md"
            metadata_path = self.needs_action / metadata_filename
            
            # Format the content
            content = f"""---
type: file_drop
original_name: {file_path.name}
size: {file_size_kb:.2f}
dropped_at: {timestamp}
status: pending
---

## File Details
A new file was dropped for processing.

## Suggested Actions
- [ ] Review file contents
- [ ] Process accordingly
- [ ] Move to Done when complete
"""
            
            # Write the metadata file
            with open(metadata_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            self.logger.error(f"Error creating metadata file for {file_path.name}: {str(e)}")


def main():
    """
    Main function to start the file system watcher.
    Monitors the Drop_Zone folder for new files and processes them.
    """
    # Create the Drop_Zone directory if it doesn't exist
    drop_zone = Path("Drop_Zone")
    drop_zone.mkdir(exist_ok=True)
    
    # Create an event handler
    event_handler = FileDropHandler()
    
    # Create an observer
    observer = Observer()
    observer.schedule(event_handler, str(drop_zone), recursive=False)
    
    # Start the observer
    observer.start()
    
    # Log startup
    event_handler.logger.info(f"Started watching {drop_zone.absolute()} for file drops")
    event_handler.logger.info("Press Ctrl+C to stop the watcher")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Stop the observer when interrupted
        observer.stop()
        event_handler.logger.info("File system watcher stopped by user")
    
    # Wait for the observer to finish
    observer.join()


if __name__ == "__main__":
    main()