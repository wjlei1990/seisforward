#!/bin/bash

#PBS -A GEO111
#PBS -N SPECFEM3D_solver
#PBS -j oe
#PBS -m a
#PBS -m b
#PBS -m e
#PBS -M NAP@princeton.edu
#PBS -o job_sb.$PBS_JOBID.o
#PBS -l nodes=NAN
#PBS -l feature=nogpureset
#PBS -l walltime=NAN

# -----------------------------------------------------
# This is a simulataneous and serial job script
# for example, you have 250 events and 50 simultaneous run
# So it needs to loop 5 times in serial, inside which 50
# simultaneous runs
# User Parameter
total_serial_runs=NAN
specfemdir=NAN
numproc=NAN
linkbase=NAN
timeout_aprun=NAN
# -----------------------------------------------------

cd $PBS_O_WORKDIR
cat $PBS_NODEFILE > compute_nodes.$PBS_JOBID
echo "$PBS_JOBID" > jobid.$PBS_JOBID

pbsdir=`pwd`
echo "running simulation: `date`"
echo "Current directory: `pwd`"
echo "specfem dir: $specfemdir"
echo

if [ ! -d $specfemdir ]; then
  echo "No specfem dir found: $specfemdir"
  exit
fi

for (( serial_id=1; serial_id<=$total_serial_runs; serial_id++ ))
do
  echo "|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||"
  echo "***********************************************************"
  echo "Serial run id: $serial_id"
  # begein serial
  eventfile="XEVENTID.$serial_id"
  eventlist_str=$(cat $eventfile |tr "\n" " ")
  eventlist=($eventlist_str)
  nevents=${#eventlist[@]}
  echo "Eventfile: $eventfile"
  echo "Number of events: $nevents"
  echo "^^^^^^^^^^^^^^^^^^^^^^^^"
  # ############################################
  # prepare files for each mpi run, which corresponds simultaneous run
  # of all events
  event_idx=1
  for event in ${eventlist[@]}
  do
    echo "-------"
    event_index_name=`printf "%04d" $event_idx`
    subrundir="$specfemdir/run$event_index_name"
    linkdir=$linkbase/$event
    echo "Idx: $event_index_name --- event $event"
    echo "subrun dir: $subrundir"
    echo "linkdir: $linkdir"
    ### remove $subrundir
    if [ -d $subrundir ]; then
      rm $subrundir
    fi
    ### LINK run000* to linkdir
    ln -s $linkdir $subrundir
    if [ $event_idx == 1 ]; then
      ### Clean model file in DATABASES_MPI
      rm $linkdir/DATABASES_MPI/attenuation.bp
      rm $linkdir/DATABASES_MPI/boundary.bp
      rm $linkdir/DATABASES_MPI/solver_data.bp
      rm $linkdir/DATABASES_MPI/solver_data_mpi.bp
      rm $linkdir/DATABASES_MPI/proc000000_reg1_topo.bin
      # LINK MODEL file for run0001 only
      model_base=$specfemdir"/DATABASES_MPI"
      echo "model base: "$mode_base
      ln -s $model_base"/attenuation.bp" $subrundir"/DATABASES_MPI/attenuation.bp"
      ln -s $model_base"/boundary.bp" $subrundir"/DATABASES_MPI/boundary.bp"
      ln -s $model_base"/solver_data.bp" $subrundir"/DATABASES_MPI/solver_data.bp"
      ln -s $model_base"/solver_data_mpi.bp" $subrundir"/DATABASES_MPI/solver_data_mpi.bp"
      ln -s $model_base"/proc000000_reg1_topo.bin" $subrundir"/DATABASES_MPI/proc000000_reg1_topo.bin"
      # echo "check model link"
      # ls -alh $subrundir/DATABASES_MPI
    fi
    # echo "check dir"
    # ls -alh $subrundir
    event_idx=$(( $event_idx + 1))
  done

  # ############################################
  # job running
  echo "^^^^^^^^^^^^^^^^^^^^^^^^"
  cd $specfemdir
  echo "cd to specfemdir: `pwd`"
  #ls -alh
  echo "solver start: `date`"
  echo "timeout -s INT $timeout_aprun aprun -n $numproc -N1 ./bin/xspecfem3D"
  ## CHECKING MODE
  #TMPLOG="./.tmp.${PBS_JOBID}.log"
  #timeout -s INT $timeout_aprun aprun -n $numproc -N1 ./bin/xspecfem3D | tee $TMPLOG
  #NODE_ERR="$(tail $TMPLOG | grep -m 1 --only-matching -E "\<ec_node_\S*\>")"
  #rm $TMPLOG
  #if [ ! -z "${NODE_ERR}" ]; then
  #  # Allow 3 min for failed node to be taken out of pool
  #  sleep 180
  #fi

  ## NON CHECKING MODE
  #timeout -s INT $timeout_aprun aprun -n $numproc -N1 ./bin/xspecfem3D

  ## Judy suggested checking mode
  EXCLUDE_NODES="$(aprun -n $PBS_NUM_NODES -N 1 /opt/bin/nvml.power_check.pl | grep ERROR: | awk '{print $2}' | xargs -r echo -n '--exclude-node-list' | sed -r 's/([^a-z]) /\1,/g')"
  timeout -s INT $timeout_aprun aprun -n $numproc -N1 ${EXCLUDE_NODES} ./bin/xspecfem3D
  sleep 10

  touch run0001/OUTPUT_FILES/proof.txt
  echo "solver end: `date`"

  # ############################################
  # Unlink
  echo "^^^^^^^^^^^^^^^^^^^^^^^^"
  echo "Remove symbolic links..."
  event_idx=1
  for event in ${eventlist[@]}
  do
    # REMOVE LINK(UNLINK)
    event_index_name=`printf "%04d" $event_idx`
    subrundir="$specfemdir/run$event_index_name"
    echo "unlink $subrundir"
    rm $subrundir
    event_idx=$(( $event_idx + 1 ))
  done
  cd $pbsdir
  # end of one eventlist file
done
# end of all eventlist files

echo -e "\n*********************************"
echo "Summary: "
echo "Success!"
echo -e "*********************************\n"
