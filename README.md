Media Organizer & Gallery Tool
This project is a Media Organization and Gallery Tool that allows users to organize media files (images, videos, and audio) based on their metadata, such as the date of creation. It can also serve these files via a web interface using Flask. The application supports file uploads, directory uploads, and management features for administrators.

Features
Organize Media Files: Organize media files into directories based on the date of creation from either the filename or EXIF metadata.
File Serving: Host and serve the organized media files via a web interface.
File Upload: Allows users to upload media files from the web interface.
Directory Upload: Allows users to upload entire directories from the web interface.
Admin Capabilities: Admin users can delete files from the gallery.
Login System: Secure access to the gallery via user authentication.
Pagination and Filtering: Media files are displayed with pagination and filters for images, videos, and audio.
Requirements
Python 3.7+
Flask
SQLAlchemy
PIL (Python Imaging Library)
tqdm
bcrypt
Watchdog (for directory monitoring)
Hachoir (for extracting metadata from video files)
Install the dependencies using the following:

```
pip install -r requirements.txt
```
Getting Started

Clone the repository:

```
git clone https://github.com/yourusername/media-organizer.git
cd media-organizer
```

Set up the virtual environment (optional but recommended):

```
python3 -m venv venv
source venv/bin/activate
```
Install dependencies:

```
pip install -r requirements.txt
```

Set up the database:

The application uses SQLite to store user data. When you first run the application, a default admin user will be created with the username admin and password adminpassword. You will be prompted to change the password on first login.

Run the app to initialize the database:

```
python manage_and_serve.py --host --dest /path/to/organized/files

```
Command-Line Options
The tool provides several command-line options for organizing media files and hosting the web application.

1. Organize Media Files
To organize files from a source directory to a target destination based on metadata (EXIF data or filename), use the following:

```
python manage_and_serve.py --import-files --src /path/to/source --dest /path/to/organized/files
Options:
--import-files: Triggers the organization of files.
--src: The source directory containing unorganized media files.
--dest: The destination directory where files will be organized.
--dry-run: Simulates the organization process without moving files.
```

Example:
```
python script4.py --import-files --src /mnt/unorganized_media --dest /mnt/organized_media --dry-run
```
2. Host the Media Gallery
To host the media files as a web gallery where users can view, upload, and manage files, use the following:

```
python manage_and_serve.py --host --dest /path/to/organized/files --port 6688
Options:
--host: Starts the Flask web server to serve the organized files.
--dest: The destination directory that will be served over the web.
--host-address: The address to bind the web server (default: 0.0.0.0).
--port: The port on which the server will run (default: 6688).
```

Example:

```
python script4.py --host --dest /mnt/organized_media --port 6688
```

3. Organize Media by Uploading a Directory via Web Interface
In addition to file uploads, users can upload directories to be organized via the web interface.

Visit the /upload-directory page in the browser.
Select the source directory.
The tool will organize the contents of the directory based on the file’s metadata or filename.
4. Change Admin Settings
On first run, the tool automatically creates an admin user (admin) with the default password (adminpassword). You will be required to change the password after the first login.
Admins can delete files from the gallery via the web interface.
5. Login System
Secure login with user authentication.
Admin users have additional privileges (e.g., deleting files).
Non-admin users can view files and upload new files.


Web Interface Features
The web interface is a fully responsive media gallery built with Bootstrap. It provides the following features:

Login System: Only authenticated users can access the gallery.
File Upload: Allows users to upload media files from their local system.
Directory Upload: Allows users to upload a directory and organize its files.
Pagination: Large sets of media files are paginated for better navigation.
Filter: Filter media by type (images, videos, audio).
Admin Management: Admin users can delete files directly from the gallery.


Directory Structure
```
media-organizer/
├── static/                  # Static files (CSS, JS)
├── templates/               # HTML templates for Flask
│   ├── header.html          # Shared header template
│   ├── footer.html          # Shared footer template
│   ├── index.html           # Main gallery view
│   ├── login.html           # Login page
│   ├── upload.html          # File upload page
│   ├── slurp.html           # Directory upload page
├── manage_and_serve.py      # Main Python script for organizing and serving media
├── requirements.txt         # Python dependencies
└── README.md                # Documentation
```

License
This project is licensed under the MIT License - see the LICENSE file for details.

Contributing
Contributions are welcome! If you'd like to improve this project, feel free to fork the repository and submit a pull request.

FOLLOWING IS FOR SHELL VERSION(FOR OLD MACHINES WITHOUT PYTHON)


This tool is developed for organizing media files into proper directory
structures, using their creation time. Script is written using bash and
only(non-standard) requires ```exiftool```  installed. Multiple kind of  
hierarchy could be created using this tool which is configurable via 
arguments. 

However, format of media is non-configurable via arguments, but very
easy to change the code to add or remove formats. 





The output structures are:

Arrange media files in the year directory then create sub-directory for each month followed by sub-directories of each date. For this hierarchy use ```-f YYYYMMDD``` 

```
- YYYY
  |_MM
    |_DD
```
Arrange media files in the year directory then create sub-directory for each month. For this hierarchy use ```-f YYYYMM``` 
```
- YYYY
  |_MM
```

Arrange media files in the year directory. For this hierarchy use ```-f YYYY``` 
```
- YYYY
```
The media files supported are: 
```
The media files supported are:
- png
- 3gp
- MOV
- m4v
- avi
- gif
- jpeg
- jpg
- mkv
- mpg
- bmp
- flv
- wmv
- mp4
```
If you want to add/remove any format, its simple and could be manually modified
in the code, this is not configurable via arguments. 


Syntax:
```
bash mediaOrganizer.sh  -i <input directory> -o <output directory> -f <format one of YYYYMMDD or YYYYMM or YYYY>
```
Description:

input directory: This is the source directory, for which organization is targeted
output directory: Files will get moved under this directory with provided structure format.
format: Type of structure desired for organization
