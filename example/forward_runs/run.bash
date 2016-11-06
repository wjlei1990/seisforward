#!/bin/bash
db_name="test.db"
if [ -f $db_name ]; then
  echo "remove: $db_name"
  rm $db_name
fi

seisforward-create_database -c config.ebru_240.yml
seisforward-fill_database -c config.ebru_240.yml -v
seisforward-create_jobs -c config.ebru_240.yml
