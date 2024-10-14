import os
import argparse
import shutil
import logging
import math
import re
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from tqdm import tqdm
from pathlib import Path
from flask import Flask, flash,  Response, render_template, send_from_directory, abort, request, redirect, url_for, session, g
from werkzeug.utils import safe_join
from werkzeug.utils import secure_filename
from functools import wraps
import bcrypt
from flask_sqlalchemy import SQLAlchemy
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
from dateutil import parser as date_parser
from datetime import datetime

# Allowed extensions for upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'wav', 'webm', 'mkv', 'avi'}

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Flask app initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    force_password_change = db.Column(db.Boolean, default=False)

# Decorator to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator to require admin access
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Watchdog event handler to detect file changes
class FileChangeHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        # This method is triggered on any file system event (like creation, modification, deletion)
        logging.info(f"File system change detected: {event.src_path}")
        global DIRECTORY_CHANGED
        DIRECTORY_CHANGED = True

# Global flag to detect directory changes
DIRECTORY_CHANGED = False

# Function to monitor the destination directory
def monitor_directory(path):
    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            pass  # Keep this thread alive to continue monitoring
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Check if the uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Video serving route
@app.route('/video/<path:filename>')
@login_required
def serve_video(filename):
    full_path = safe_join(TARGET_DIR, filename)
    
    if not os.path.exists(full_path):
        return abort(404)

    range_header = request.headers.get('Range', None)
    if range_header:
        return partial_response_video(full_path, range_header)
    else:
        return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path))

def partial_response_video(full_path, range_header):
    """Helper function to serve video files with range support."""
    try:
        range_header = range_header.replace("bytes=", "").split("-")
        start = int(range_header[0])
        end = range_header[1]
        
        file_size = os.path.getsize(full_path)
        end = int(end) if end else file_size - 1

        chunk_size = end - start + 1
        with open(full_path, 'rb') as f:
            f.seek(start)
            chunk_data = f.read(chunk_size)

        response = Response(chunk_data, 206, mimetype='video/mp4')
        response.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
        response.headers.add('Accept-Ranges', 'bytes')
        return response
    except Exception as e:
        logging.error(f"Error while serving video: {str(e)}")
        abort(500)



@app.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        is_admin = 'is_admin' in request.form

        new_user = User(username=username, password=hashed_pw, is_admin=is_admin, force_password_change=True)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password):
            session['user_id'] = user.id
            if user.force_password_change:
                return redirect(url_for('change_password'))
            return redirect(url_for('index'))
        else:
            return "Invalid credentials", 403
    return render_template('login.html')

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return "Passwords do not match", 400

        user = User.query.get(session['user_id'])
        hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        user.password = hashed_pw
        user.force_password_change = False
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('change_password.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET'])
@login_required
def index():
    global DIRECTORY_CHANGED
    if DIRECTORY_CHANGED:
        DIRECTORY_CHANGED = False
        logging.info("Refreshing directory content due to changes detected.")
    return serve_directory()

@app.route('/<path:subpath>')
@login_required
def serve_directory(subpath=''):
    """
    Serve files and subdirectories within the target directory, with pagination and filtering.
    """
    full_path = safe_join(TARGET_DIR, subpath)
    page = int(request.args.get('page', 1))  # Default page is 1
    items_per_page = 10
    media_type = request.args.get('media_type', '')  # Get media_type from query params

    if os.path.isdir(full_path):
        try:
            items = sorted(os.listdir(full_path))  # Sort items to keep things consistent

            # Filter by media type if specified
            if media_type:
                if media_type == 'image':
                    items = [item for item in items if item.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
                elif media_type == 'video':
                    items = [item for item in items if item.lower().endswith(('.mp4', '.webm', '.mkv', '.avi'))]
                elif media_type == 'audio':
                    items = [item for item in items if item.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a'))]

            total_items = len(items)
            total_pages = max(math.ceil(total_items / items_per_page), 1)

            # Get the items for the current page
            start_index = (page - 1) * items_per_page
            end_index = start_index + items_per_page
            paginated_items = items[start_index:end_index]

            files_and_dirs = [
                {'name': item, 'is_dir': os.path.isdir(safe_join(full_path, item))}
                for item in paginated_items
            ]

            # Generate page numbers for pagination
            page_numbers = []
            if total_pages <= 13:
                page_numbers = list(range(1, total_pages + 1))
            else:
                if page <= 10:
                    page_numbers = list(range(1, 11)) + ['...', total_pages - 2, total_pages - 1, total_pages]
                elif page > 10 and page <= total_pages - 10:
                    page_numbers = [1, 2, 3, '...'] + list(range(page - 2, page + 3)) + ['...', total_pages - 2, total_pages - 1, total_pages]
                else:
                    page_numbers = [1, 2, 3, '...'] + list(range(total_pages - 9, total_pages + 1))


            # Always pass these pagination parameters to the template
            return render_template(
                'index.html',
                items=files_and_dirs,
                current_dir=subpath,
                current_page=page,
                total_pages=total_pages,
                total_items=total_items,
                page_numbers=page_numbers,
                media_type=media_type  # Pass the media type filter to the template
            )
        except Exception as e:
            return f"Error accessing sub-directory: {str(e)}", 500
    elif os.path.isfile(full_path):
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        return send_from_directory(directory, filename)
    else:
        abort(404)


@app.route('/upload', methods=['GET', 'POST'])
@login_required  # or @admin_required if only admins should upload
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # Save the file temporarily
            temp_path = Path(TARGET_DIR) / 'temp' / secure_filename(file.filename)
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            file.save(temp_path)

            # Organize the file based on its metadata
            try:
                organize_files(str(temp_path.parent), TARGET_DIR)
                flash(f"File {file.filename} successfully uploaded and organized.")
            except Exception as e:
                logging.error(f"Error organizing file {file.filename}: {str(e)}")
                flash(f"Error organizing file: {file.filename}")

            return redirect(url_for('serve_directory', subpath=''))

        flash('File type not allowed')
        return redirect(request.url)

    # Render the upload page (GET request)
    return render_template('upload.html')


@app.route('/delete/<path:filename>', methods=['POST'])
@admin_required  # Only allow admins to delete files
def delete_file(filename):
    try:
        # Get the full path of the file
        full_path = safe_join(TARGET_DIR, filename)

        # Extract the directory part (subpath) from the filename
        subpath = os.path.dirname(filename)

        # Ensure the file exists before trying to delete it
        if not os.path.exists(full_path):
            return abort(404, description="File not found.")

        # Perform the deletion
        os.remove(full_path)
        logging.info(f"File deleted: {full_path}")

        # Redirect back to the current directory (subpath)
        return redirect(url_for('serve_directory', subpath=subpath))

    except Exception as e:
        logging.error(f"Error deleting file {filename}: {str(e)}")
        return abort(500, description="Error deleting file.")

@app.route('/slurp', methods=['GET', 'POST'])
@login_required  # Require the user to be logged in
def slurp_directory():
    if request.method == 'POST':
        directory = request.form['directory']

        # Validate that the directory exists and is accessible
        if not os.path.exists(directory):
            flash(f"Directory '{directory}' does not exist.")
            return redirect(url_for('slurp_directory'))

        if not os.access(directory, os.R_OK):
            flash(f"Directory '{directory}' is not accessible. Check permissions.")
            return redirect(url_for('slurp_directory'))

        # If the directory is valid, start organizing the files
        try:
            organize_files(directory, TARGET_DIR)
            flash(f"Files in '{directory}' were successfully organized.")
        except Exception as e:
            logging.error(f"Error organizing files in directory {directory}: {str(e)}")
            flash(f"Error organizing directory '{directory}': {str(e)}")

        return redirect(url_for('slurp_directory'))

    return render_template('slurp.html')


@app.before_request
def create_default_admin():
    if User.query.count() == 0:
        hashed_password = bcrypt.hashpw('adminpassword'.encode('utf-8'), bcrypt.gensalt())
        admin_user = User(username='admin', password=hashed_password, is_admin=True, force_password_change=True)
        db.session.add(admin_user)
        db.session.commit()

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(User, user_id)



def get_file_type(file_name):
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.heic', '.svg', '.ico'}
    video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.mpeg', '.webm', '.3gp', '.m4v', '.mts', '.m2ts'}
    audio_extensions = {'.mp3', '.wav', '.aac', '.flac', '.ogg', '.wma', '.m4a', '.aiff'}

    ext = file_name.lower()

    if ext.endswith(tuple(image_extensions)):
        return 'image'
    elif ext.endswith(tuple(video_extensions)):
        return 'video'
    elif ext.endswith(tuple(audio_extensions)):
        return 'audio'

    return 'unknown'


def get_date_from_filename(filename):
    try:
        # Try to parse the date from the filename using dateutil's fuzzy parsing
        parsed_date = date_parser.parse(filename, fuzzy=True)

        # Validate the parsed date: Ensure it's within a reasonable range (1900 to 2100)
        if parsed_date.year < 1900 or parsed_date.year > 2100:
            raise ValueError("Parsed date is out of range.")

        return parsed_date
    except (ValueError, OverflowError) as e:
        # If we fail to parse the date or it falls out of range, return None
        return None


def get_media_creation_date(file_path):
    # First, attempt to get the date from the filename
    filename_date = get_date_from_filename(file_path.name)
    if filename_date:
        return filename_date
    
    # If no date could be parsed from the filename, fall back to EXIF or modification metadata
    try:
        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.tiff']:
            img = Image.open(file_path)
            exif_data = img.getexif()  # Use the correct method for getting EXIF
            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name == 'DateTimeOriginal':
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
        elif file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:  # Video formats
            parser = createParser(str(file_path))
            metadata = extractMetadata(parser)
            if metadata and metadata.has("creation_date"):
                return metadata.get("creation_date")
    except (IOError, ValueError) as e:
        logging.error(f"Error extracting metadata from {file_path}: {e}")

    # Fallback to file modification date if no EXIF or video metadata
    return datetime.fromtimestamp(file_path.stat().st_mtime)


def create_thumbnail(image_path, thumb_path, size=(300, 300)):
    try:
        img = Image.open(image_path)
        img.thumbnail(size)
        img.save(thumb_path)
        logging.info(f"Thumbnail created for {image_path}")
    except Exception as e:
        logging.error(f"Error creating thumbnail for {image_path}: {str(e)}")

def get_image_location(file_path):
    try:
        # Only attempt to get EXIF data for formats that support it (e.g., JPG, TIFF)
        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.tiff', '.png']:
            img = Image.open(file_path)
            exif_data = img.getexif()  # Use getexif() instead of _getexif()
            if exif_data and "GPSInfo" in exif_data:
                return "SomeCity"  # Placeholder for reverse geocoding; replace with actual logic if needed.
    except (IOError, ValueError, AttributeError) as e:
        logging.error(f"Error extracting GPS location from {file_path}: {e}")
    
    # Return None if no GPS information is found
    return None

def get_target_path(creation_date, city, file_type, target_dir):
    year = creation_date.strftime('%Y')
    month = creation_date.strftime('%m')
    day = creation_date.strftime('%d')
    target_path = Path(target_dir) / year / month / day
    if city:
        target_path = target_path / city

    if file_type == 'image':
        target_path = target_path / 'images'
    elif file_type == 'video':
        target_path = target_path / 'videos'
    elif file_type == 'audio':
        target_path = target_path / 'audio'

    target_path.mkdir(parents=True, exist_ok=True)
    return target_path

def handle_duplicate(target_path, file_name):
    file_path = Path(target_path) / file_name
    counter = 1
    while file_path.exists():
        file_path = file_path.with_name(f"{file_path.stem}_{counter}{file_path.suffix}")
        counter += 1
    return str(file_path)


def organize_files(source_dir, target_dir, dry_run=False):
    total_files = sum([len(files) for r, d, files in os.walk(source_dir)])

    if total_files == 0:
        logging.warning("No files found in the source directory.")
        return

    with tqdm(total=total_files, desc="Organizing files") as pbar:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                file_type = get_file_type(file)

                if file_type == 'unknown':
                    logging.warning(f"Skipping unknown file type: {file}")
                    pbar.update(1)
                    continue

                creation_date = get_media_creation_date(file_path)
                if not creation_date:
                    logging.warning(f"No creation date found for {file}, skipping.")
                    pbar.update(1)
                    continue

                city = get_image_location(file_path)
                target_path = get_target_path(creation_date, city, file_type, target_dir)

                new_file_name = handle_duplicate(target_path, file)

                if dry_run:
                    logging.info(f"[DRY-RUN] Would move {file_path} to {new_file_name}")
                else:
                    shutil.move(file_path, new_file_name)
                    logging.info(f"Moved {file_path} to {new_file_name}")

                    # Create thumbnail for images
                    if file_type == 'image':
                        thumbnail_dir = target_path / 'thumbnails'
                        thumbnail_dir.mkdir(parents=True, exist_ok=True)
                        thumb_file_name = thumbnail_dir / file
                        create_thumbnail(new_file_name, thumb_file_name)

                pbar.update(1)

def host_directory(target_dir, host='0.0.0.0', port=6688):
    global TARGET_DIR
    TARGET_DIR = target_dir

    # Start a thread to monitor the target directory
    threading.Thread(target=monitor_directory, args=(target_dir,), daemon=True).start()

    app.run(host=host, port=port, debug=False)

# Main function with command-line argument handling
def main():
    parser = argparse.ArgumentParser(description="Organize and/or host media files.")
    parser.add_argument('--import-files', action='store_true', help="Organize media files")
    parser.add_argument('--host', action='store_true', help="Host the media files over the web")
    parser.add_argument('--src', type=str, help="Source directory of unorganized media files")
    parser.add_argument('--dest', type=str, help="Target directory to organize files into")
    parser.add_argument('--dry-run', action='store_true', help="Simulate the organization process without moving files")
    parser.add_argument('--host-address', type=str, default='0.0.0.0', help="Host address for the Flask app (default: 0.0.0.0)")
    parser.add_argument('--port', type=int, default=6688, help="Port for the Flask app (default: 6688)")

    args = parser.parse_args()

    if args.import_files and args.src and args.dest:
        organize_files(args.src, args.dest, args.dry_run)

    if args.host and args.dest:
        with app.app_context():
            db.create_all()
        host_directory(args.dest, host=args.host_address, port=args.port)

    if not args.import_files and not args.host:
        parser.print_help()

if __name__ == '__main__':
    main()

