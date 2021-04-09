This tool is developed for organizing media files into proper directory
structures, using their creation time.

The output structures are:

Arrange media files in the year directory then create sub-directory for each month followed by sub-directories of each date. 

```
- YYYY
  |_MM
    |_DD
```
Arrange media files in the year directory then create sub-directory for each month.
```
- YYYY
  |_MM
```

Arrange media files in the year directory.
```
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
bash mediaOrganizer.sh  -i <input directory> -o <output directory> -f <format one of YYYYMMDD or YYYYMM or YYYY>
```
Description:

input directory: This is the source directory, for which organization is targeted
output directory: Files will get moved under this directory with provided structure format.
format: Type of structure desired for organization
