#!/bin/bash

################################################################################################################################
# Output file

############### Declare files and check existence
####
TAfiles=(
    ./benchmark/TA/tl_8.nm
)
for i in "${TAfiles[@]}"; do
    if [ -e "$i" ]
    then
        echo "File $i found"
    else
        echo "File $i not found!"
        exit
    fi
done

# Set timeout duration (1 hour)
timeout_duration=3600

################### Run
###
files=("${TAfiles[@]}")
call1="--numInit 2 --numScheds 1 --schedList 1 1 --targets j0 j0 --coefficient 1 -1 0"
for file in "${files[@]}"; do
  # Run command and append output to the file
  echo "Running $file..."
  echo "Checking $call1"
  timeout $timeout_duration python3 relreach.py --modelPath $file ${call1}

  # Check exit status
  exitcode=$?
  if [ $exitcode -eq 0 ]; then
      echo "Sample command ran successfully!"
  fi
done
