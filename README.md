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
- jpeg
- jpg
- png
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
