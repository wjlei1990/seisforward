#!/bin/bash
db_name="test.db"
if [ -f $db_name ]; then
  echo "remove: $db_name"
  rm $db_name
fi

# create database to store job information
seisforward-create_database -c config.yml

# fill in the database
seisforward-fill_database -c config.yml -v

# setup the run base directory
#seisforward-setup_runbase -c config.yml

# create jobs
seisforward-create_jobs -c config.yml
