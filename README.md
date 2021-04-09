This tool is developed for organizing media files into proper directory
structures, using their creation time.

The output structures are:
```
- YYYY
  |_MM
    |_DD

- YYYY
  |_MM

- YYYY
```
The media files supported are:
```
- jpeg
- jpg
- png
- mp4
```
If you want to add/remove any format, its simple and could be manually modified
in the following lines of code


Syntax:
```
bash mediaOrganizer.sh  -i <input directory> -o <output directory> -f <format>
```
Description:

input directory: This is the source directory, for which organization is targeted
output directory: Files will get moved under this directory with provided structure format.
format: Type of structure desired for organization
