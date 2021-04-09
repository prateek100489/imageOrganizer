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

- jpeg
- jpg
- png
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
media_list=$(find "${input_dir}" -path "./$(basename "$output_dir")"  -prune -o -type f   \( -name "*.png" -o -name "*.jpeg" -o -name "*.jpg" -o -name "*.mp4" \))
total_files=$(echo "$media_list" |wc -l)
count=1
echo "$media_list"|while read -r file;
do
        if [ -d "$file" ];then
                echo "$(date): [Warn]: Skipping directory $file"
                continue;
        fi
        echo "$(date): [Info]: Processing $count/$total_files file. Current file is $(basename "$file")"
        count=$((count+1))
        out_path=$(exiftool  "$file" |awk -v format="${format}" -v OFS='/' '/^Create Date/{split($4,a,":");if(format == "YYYYMMDD") {print a[1],a[2],a[3]}; if(format == "YYYYMM") {print a[1],a[2]} if(format == "YYYY") {print a[1]} ;exit}')
        if [ -z "${out_path}" ];then
                out_path=$(exiftool  "$file" | awk -v format="${format}" -v OFS='/' '/^File Modification Date/{split($5,a,":");if(format == "YYYYMMDD") {print a[1],a[2],a[3]}; if(format == "YYYYMM") {print a[1],a[2]} if(format == "YYYY") {print a[1]};exit}')
        fi

        if [ -z "${out_path}" ];then
                echo "$(date): [Warn]: Unable to fetch the create time of $(basename "$file"), moving to ${output_dir}/unknown_origin"
                if [ ! -d "${output_dir}/unknown_origin" ];then
                        if ! mkdir -p "${output_dir}"/unknown_origin 2>/dev/null;then
                                echo "$(date): [Error]: Unable to create ${output_dir}/unknown_origin"
                                exit 1
                        fi
                fi
                mv "${file}" "${output_dir}/unknown_origin/"
                continue;
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
