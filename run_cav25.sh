#!/bin/bash

################################################################################################################################
# Which experiments should be performed?
explist=(
    'VN',
    'RT',
    'TA',
    'PW',
    'TS',
    'SD'
)
ok=1

if [ $# -eq 0 ]; then
  ok=0
elif [ $# -eq 1 ]; then
  value="\<${1}\>"
  if [[ " ${explist[*]} " == *" ${1}"* ]]; then
    explist=($1)
    ok=0
  else
    echo "Provided string does not match any of the benchmarks. Choose one of ${explist[@]} "
  fi
elif [ $# -gt 1 ]; then
  echo "More than a single argument was provided, this script can only handle a single one. Choose one of ${explist[@]} or do not provide any argument, then all will be executed"
fi


################################################################################################################################
# Output file
output_file=logs/results_cav25.txt

if [ -e "$output_file" ]
then
    echo "File $output_file found"
else
  ############### Declare files and check existence
  ###
  if [[ " ${explist[*]} " == *"VN"* ]]; then
    VNfiles=(
        ./benchmark/VN/vn-gen_1.nm
        ./benchmark/VN/vn-gen_10.nm
        ./benchmark/VN/vn-gen_100.nm
        ./benchmark/VN/vn-gen_200.nm
        ./benchmark/VN/vn-gen_250.nm
        ./benchmark/VN/vn-gen_300.nm
    )
    for i in "${VNfiles[@]}"; do
        if [ -e "$i" ]
        then
            echo "File $i found"
        else
            echo "File $i not found!"
            exit
        fi
    done
  fi

  ###
  if [[ " ${explist[*]} " == *"RT"* ]]; then
    RTfiles=(
        ./benchmark/RT/janitor_10.nm
        ./benchmark/RT/janitor_w_10.nm
        ./benchmark/RT/janitor_100.nm
        ./benchmark/RT/janitor_w_100.nm
        ./benchmark/RT/janitor_200.nm
        ./benchmark/RT/janitor_w_200.nm
        ./benchmark/RT/janitor_300.nm
        ./benchmark/RT/janitor_w_300.nm
    )
    for i in "${RTfiles[@]}"; do
        if [ -e "$i" ]
        then
            echo "File $i found"
        else
            echo "File $i not found!"
            exit
        fi
    done
  fi

  ####
  if [[ " ${explist[*]} " == *"TA"* ]]; then
    TAfiles=(
        ./benchmark/TA/tl_8.nm
        ./benchmark/TA/tl_16.nm
        ./benchmark/TA/tl_24.nm
        ./benchmark/TA/tl_28.nm
        ./benchmark/TA/tl_32.nm
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
  fi

  ####
  if [[ " ${explist[*]} " == *"PW"* ]]; then
    PWfiles=(
        ./benchmark/PW/password_leakage_1.nm
        ./benchmark/PW/password_leakage_2.nm
    )
    for i in "${PWfiles[@]}"; do
        if [ -e "$i" ]
        then
            echo "File $i found"
        else
            echo "File $i not found!"
            exit
        fi
    done
  fi

  ####
  if [[ " ${explist[*]} " == *"TS"* ]]; then
    TSfiles=(
        ./benchmark/TS/th10_20.nm
        ./benchmark/TS/th20_200.nm
        ./benchmark/TS/th20_5000.nm
        ./benchmark/TS/th50_10000.nm
        ./benchmark/TS/th50_20000.nm
    )
    for i in "${TSfiles[@]}"; do
        if [ -e "$i" ]
        then
            echo "File $i found"
        else
            echo "File $i not found!"
            exit
        fi
    done
  fi

  ####
  if [[ " ${explist[*]} " == *"SD"* ]]; then
    SDfiles=(
        ./benchmark/SD/simple/sketch.templ
        ./benchmark/SD/splash-1/sketch.templ
        ./benchmark/SD/splash-2/sketch.templ
        ./benchmark/SD/larger-1/sketch.templ
        ./benchmark/SD/larger-2/sketch.templ
        ./benchmark/SD/larger-3/sketch.templ
        ./benchmark/SD/train/sketch.templ
    )
    for i in "${SDfiles[@]}"; do
        if [ -e "$i" ]
        then
            echo "File $i found"
        else
            echo "File $i not found!"
            exit
        fi
    done
  fi

  # Set timeout duration (1 hour)
  timeout_duration=3600


  ################### Run
  ########
  echo "---------------------------------------------------" >> "$output_file"
  echo "Table 1" >>  "$output_file"
  echo "---------------------------------------------------" >> "$output_file"

  ####
  if [[ " ${explist[*]} " == *"VN"* ]]; then
    echo "VN" >> "$output_file"
    echo "-------------" >> "$output_file"
    files=("${VNfiles[@]}")
    call1="--numInit 2 --numScheds 1 --schedList 1 1 --targets res_is_0 res_is_1 --comparisonOperator = --coefficient 1 -1 0"
    call2="--numInit 2 --numScheds 1 --schedList 1 1 --targets res_is_0 res_is_1 --comparisonOperator = --coefficient 1 -1 0 --epsilon 0.1"
    for file in "${files[@]}"; do
      # Run command and append output to the file
      echo "$(date)" >>  "$output_file"
      echo "Running $file..."
      echo "Running $file..." >> "$output_file"
      echo "Checking $call1" >> "$output_file"
      timeout $timeout_duration python3 relreach.py --modelPath $file ${call1} >> "$output_file"

      # Check exit status
      exitcode=$?
      if [ $exitcode -eq 124 ]; then
          echo "Command timed out." >> "$output_file"
      elif [ $exitcode -eq 1 ]; then
          echo "Out of memory!" >> "$output_file"
      else
          echo "Exit status $exitcode" >> "$output_file"
      fi
      echo "---------------------------------------------------" >> "$output_file"

      # Run command and append output to the file
      echo "$(date)" >>  "$output_file"
      echo "Running $file..." >> "$output_file"
      echo "Checking $call2" >> "$output_file"
      timeout $timeout_duration python3 relreach.py --modelPath $file ${call2} >> "$output_file"

      # Check exit status
      exitcode=$?
      if [ $exitcode -eq 124 ]; then
          echo "Command timed out." >> "$output_file"
      elif [ $exitcode -eq 1 ]; then
          echo "Out of memory!" >> "$output_file"
      else
          echo "Exit status $exitcode" >> "$output_file"
      fi
      echo "---------------------------------------------------" >> "$output_file"
    done
  fi


  ####
  if [[ " ${explist[*]} " == *"RT"* ]]; then
    echo "RT" >> "$output_file"
    echo "-------------" >> "$output_file"
    files=("${RTfiles[@]}")
    call="--numInit 2 --numScheds 2 --schedList 1 2 --targets target target --epsilon 0.00001 --coefficient 1 -1 0"
    for file in "${files[@]}"; do
      # Run command and append output to the file
      echo "$(date)" >>  "$output_file"
      echo "Running $file..."
      echo "Running $file..." >> "$output_file"
      echo "Checking $call" >> "$output_file"
      timeout $timeout_duration python3 relreach.py --modelPath $file ${call} >> "$output_file"

      # Check exit status
      exitcode=$?
      if [ $exitcode -eq 124 ]; then
          echo "Command timed out." >> "$output_file"
      elif [ $exitcode -eq 1 ]; then
          echo "Out of memory!" >> "$output_file"
      else
          echo "Exit status $exitcode" >> "$output_file"
      fi
      echo "---------------------------------------------------" >> "$output_file"
    done
  fi

  ########
  echo "---------------------------------------------------" >> "$output_file"
  echo "Table 2" >>  "$output_file"
  echo "---------------------------------------------------" >> "$output_file"

  ###
  if [[ " ${explist[*]} " == *"TA"* ]]; then
    echo "TA(1)" >> "$output_file"
    echo "-------------" >> "$output_file"
    files=("${TAfiles[@]}")
    call1="--numInit 2 --numScheds 1 --schedList 1 1 --targets j0 j0 --coefficient 1 -1 0"
    call2="--numInit 2 --numScheds 2 --schedList 1 2 --targets j0 j0 --coefficient 1 -1 0"
    for file in "${files[@]}"; do
      # Run command and append output to the file
      echo "$(date)" >>  "$output_file"
      echo "Running $file..."
      echo "Running $file..." >> "$output_file"
      echo "Checking $call1" >> "$output_file"
      timeout $timeout_duration python3 relreach.py --modelPath $file ${call1} >> "$output_file"

      # Check exit status
      exitcode=$?
      if [ $exitcode -eq 124 ]; then
          echo "Command timed out." >> "$output_file"
      elif [ $exitcode -eq 1 ]; then
          echo "Out of memory!" >> "$output_file"
      else
          echo "Exit status $exitcode" >> "$output_file"
      fi
      echo "---------------------------------------------------" >> "$output_file"
    done

    echo "TA(2)" >> "$output_file"
    echo "-------------" >> "$output_file"
    for file in "${files[@]}"; do
      # Run command and append output to the file
      echo "$(date)" >>  "$output_file"
      echo "Running $file..."
      echo "Running $file..." >> "$output_file"
      echo "Checking $call2" >> "$output_file"
      timeout $timeout_duration python3 relreach.py --modelPath $file ${call2} >> "$output_file"

      # Check exit status
      exitcode=$?
      if [ $exitcode -eq 124 ]; then
          echo "Command timed out." >> "$output_file"
      elif [ $exitcode -eq 1 ]; then
          echo "Out of memory!" >> "$output_file"
      else
          echo "Exit status $exitcode" >> "$output_file"
      fi
      echo "---------------------------------------------------" >> "$output_file"
    done
  fi


  ####
  if [[ " ${explist[*]} " == *"PW"* ]]; then
    echo "PW(1)" >> "$output_file"
    echo "-------------" >> "$output_file"
    files=("${PWfiles[@]}")
    call1="--numInit 2 --numScheds 1 --schedList 1 1 --targets counter0 counter0 --coefficient 1 -1 0"
    call2="--numInit 2 --numScheds 2 --schedList 1 2 --targets counter0 counter0 --coefficient 1 -1 0"
    for file in "${files[@]}"; do
      # Run command and append output to the file
      echo "$(date)" >>  "$output_file"
      echo "Running $file..."
      echo "Running $file..." >> "$output_file"
      echo "Checking $call1" >> "$output_file"
      timeout $timeout_duration python3 relreach.py --modelPath $file ${call1} >> "$output_file"

      # Check exit status
      exitcode=$?
      if [ $exitcode -eq 124 ]; then
          echo "Command timed out." >> "$output_file"
      elif [ $exitcode -eq 1 ]; then
          echo "Out of memory!" >> "$output_file"
      else
          echo "Exit status $exitcode" >> "$output_file"
      fi
      echo "---------------------------------------------------" >> "$output_file"
    done

    echo "PW(2)" >> "$output_file"
    echo "-------------" >> "$output_file"
    for file in "${files[@]}"; do
      # Run command and append output to the file
      echo "$(date)" >>  "$output_file"
      echo "Running $file..."
      echo "Running $file..." >> "$output_file"
      echo "Checking $call2" >> "$output_file"
      timeout $timeout_duration python3 relreach.py --modelPath $file ${call2} >> "$output_file"

      # Check exit status
      exitcode=$?
      if [ $exitcode -eq 124 ]; then
          echo "Command timed out." >> "$output_file"
      elif [ $exitcode -eq 1 ]; then
          echo "Out of memory!" >> "$output_file"
      else
          echo "Exit status $exitcode" >> "$output_file"
      fi
      echo "---------------------------------------------------" >> "$output_file"
    done
  fi


  ####
  if [[ " ${explist[*]} " == *"TS"* ]]; then
    echo "TS" >> "$output_file"
    echo "-------------" >> "$output_file"
    files=("${TSfiles[@]}")
    call="--numInit 2 --numScheds 1 --schedList 1 1 --targets terml1 terml1 --coefficient 1 -1 0"
    for file in "${files[@]}"; do
      # Run command and append output to the file
      echo "$(date)" >>  "$output_file"
      echo "Running $file..."
      echo "Running $file..." >> "$output_file"
      echo "Checking $call" >> "$output_file"
      timeout $timeout_duration python3 relreach.py --modelPath $file ${call} >> "$output_file"

      # Check exit status
      exitcode=$?
      if [ $exitcode -eq 124 ]; then
          echo "Command timed out." >> "$output_file"
      elif [ $exitcode -eq 1 ]; then
          echo "Out of memory!" >> "$output_file"
      else
          echo "Exit status $exitcode" >> "$output_file"
      fi
      echo "---------------------------------------------------" >> "$output_file"
    done
  fi


  ####
  if [[ " ${explist[*]} " == *"SD"* ]]; then
    echo "SD" >> "$output_file"
    echo "-------------" >> "$output_file"
    files=("${SDfiles[@]}")
    call="--numInit 2 --numScheds 1 --schedList 1 1 --targets target target -cop > --coefficient 1 -1 0"
    for file in "${files[@]}"; do
      # Run command and append output to the file
      echo "$(date)" >>  "$output_file"
      echo "Running $file..."
      echo "Running $file..." >> "$output_file"
      echo "Checking $call" >> "$output_file"
      timeout $timeout_duration python3 relreach.py --modelPath $file ${call} >> "$output_file"

      # Check exit status
      exitcode=$?
      if [ $exitcode -eq 124 ]; then
          echo "Command timed out." >> "$output_file"
      elif [ $exitcode -eq 1 ]; then
          echo "Out of memory!" >> "$output_file"
      else
          echo "Exit status $exitcode" >> "$output_file"
      fi
      echo "---------------------------------------------------" >> "$output_file"
    done
  fi

  echo "Finished running all experiments"
fi
