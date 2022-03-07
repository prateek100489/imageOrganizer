#!/bin/bash
set -e
show_help()
{
echo "This tool is developed for organizing media files into proper directory
structures, using their creation time.
The output structures are:
- YYYY
  |_MM
    |_DD
- YYYY
  |_MM
- YYYY
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

If you want to add/remove any format, its simple and could be manually modified
in the following lines of code"

echo "Syntax:
bash $0 -i <input directory> -o <output directory> -f <format>
"
echo "Description:
input directory: This is the source directory, for which organization is targeted
output directory: Files will get moved under this directory with provided structure format.
format: Type of structure desired for organization"

exit 0;
}
while getopts ":i:o:f:h" opt; do
  case ${opt} in
     i)
       input_dir="${OPTARG}"
       ;;
     o)
      output_dir="${OPTARG}"
       ;;
     f)
      format="${OPTARG^^}"
       ;;
    h)
      show_help
      ;;
    \? )
      echo "Invalid option: $OPTARG" 1>&2
      exit 0
      ;;
    : )
      echo "Invalid option: $OPTARG requires an argument" 1>&2
      exit
      ;;
  esac
done
shift $((OPTIND -1))
: "${input_dir:?Missing -i <input directory name>}" "${output_dir:?Missing -o <output directory name>}" "${format:?Missing -f <YYYYMMDD|YYYYMM|YYYY>}"

if ! which exiftool &>/dev/null ;then
        echo "$(date): [Error]: This tool requires exiftool installed on the sytem."
        exit 0
fi

if [ "$input_dir" == "$output_dir" ];then
        echo "$(date): [Error]: Input and output directories cannot be same."
        exit 0
else
        if [ ! -d "$input_dir" ];then
                echo "$(date): [Error]:  There is no input directory called ${input_dir}."
                exit 2
        fi
fi

if ! echo "$format" |grep -qEiw "^YYYYMMDD$|^YYYYMM$|^YYYY$" ;then
        echo "$(date): [Error]: Invalid Directory levels. Supported values: <YYYYMMDD|YYYYMM|YYYY>"
        exit 99
fi

find_command="find '${input_dir}' -path "./$(basename "$output_dir")"  -prune -o -type f   \( -iname '*.png' -o -iname '*.3gp' -o -iname '*.MOV' -o -iname '*.m4v' -o -iname '*.avi' -o -iname '*.gif' -o -iname '*.jpeg' -o -iname '*.jpg' -o -iname '*.mkv' -o -iname '*.mpg' -o -iname '*.bmp' -o -iname '*.flv' -o -iname '*.wmv' -o -iname '*.mp4' \)"


media_list=$(echo "$find_command" |bash)




#media_list=$(find "${input_dir}" -path "./$(basename "$output_dir")"  -prune -o -type f   \( -iname "*.png" -o -iname "*.3gp" -o -iname "*.MOV" -o -iname "*.m4v" -o -iname "*.avi" -o -iname "*.gif" -o -iname "*.jpeg" -o -iname "*.jpg" -o -iname "*.mkv" -o -iname "*.mpg" -o -iname "*.bmp" -o -iname "*.flv" -o -iname "*.wmv" -o -iname "*.mp4" \))

total_files=$(echo "$media_list" |grep -E . |wc -l)
if [ "${total_files:-0}" -eq 0 ];then
        echo "$(date): [Info]: No media file found ${media_list}. Supported format by this tool are:  $(echo "$find_command"  |grep -oP 'name\K\s+[^ ]+'|tr '\n' ', ') "
        exit 69
else
        initial_size_input_dir=$(du -sh "${input_dir}" |awk '{print $1}')
        echo "$(date): [Info]: The initial size of input directory(${input_dir}) is ${initial_size_input_dir}"
fi

count=1
echo "$media_list"|while read -r file;
do
        if [ -d "$file" ];then
                echo "$(date): [Warning]: Skipping directory $file"
                continue;
        fi
        echo "$(date): [Info]: Processing $count/$total_files file. Current file is $(basename "$file")"
        count=$((count+1))
        out_path=$(exiftool  "$file" |awk -v format="${format}" -v OFS='/' '/^Create Date/{split($4,a,":");if(format == "YYYYMMDD") {print a[1],a[2],a[3]}; if(format == "YYYYMM") {print a[1],a[2]} if(format == "YYYY") {print a[1]} ;exit}')
        if [[ $format == "YYYY" && $out_path == "0000"  ||  $format == "YYYYMM" && $out_path == "0000/00" ||  $format == "YYYYMMDD" &&  $out_path == "0000/00/00" || -z $out_path ]];then
                echo "$(date): [Warning]: Unable to get the creation time of $file using exiftool, falling back to probe file name to get a valid date"
                date_from_filename=$(echo "$file"|grep -oP '20\d{2}-*([0][1-9]|[1][012])-*([0][1-9]|[1][0-9]|[2][0-9]|[3][0-1])'||true)
                if ! date -d "$date_from_filename" &>/dev/null;then
                        echo "$(date): [Warning]: Unable to obtain a valid date from the filename probe, moving file to ${output_dir}/unknown_origin"

                        if [ ! -d "${output_dir}/unknown_origin" ];then
                              if ! mkdir -p "${output_dir}"/unknown_origin 2>/dev/null;then
                                        echo "$(date): [Error]: Unable to create ${output_dir}/unknown_origin"
                                        exit 1
                              fi
                        fi

                        mv "${file}" "${output_dir}/unknown_origin/"
                        continue;
                else

                        out_path=$(date -d "$date_from_filename" +%F |awk -v format="${format}" -v OFS='/' '{split($1,a,"-");if(format == "YYYYMMDD") {print a[1],a[2],a[3]}; if(format == "YYYYMM") {print a[1],a[2]} if(format == "YYYY") {print a[1]} ;exit}')
                fi
        fi

        if [ ! -d "${output_dir}/${out_path}" ];then
                if ! mkdir -p "${output_dir}/${out_path}" ;then
                        echo "$(date): [Error]: Unable to create ${output_dir}/${out_path} directory."
                        exit 2
                fi
        fi
        if ! rc_out=$(mv "$file" "${output_dir}/${out_path}" 2>&1) ;then
                echo "$(date): [Error]: Unable to move $(basename "${file}") to ${output_dir}"
                echo "${rc_out}"
                exit 3;
        fi

done
