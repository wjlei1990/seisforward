#!/bin/bash

#PBS -A GEO111
#PBS -N SPECFEM3D_solver
#PBS -j oe
#PBS -m a
#PBS -m b
#PBS -m e
#PBS -M lei@princeton.edu
#PBS -o job_sb.$PBS_JOBID.o
#PBS -l nodes=480
#PBS -l walltime=1:00:00

# -----------------------------------------------------
# This is a simulataneous and serial job script
# for example, you have 250 events and 50 simultaneous run
# So it needs to loop 5 times in serial, inside which 50
# simultaneous runs
# User Parameter
total_serial_runs=5
specfemdir="/lustre/atlas/proj-shared/geo111/Wenjie/test/seisforward/runbase/specfem3d_globe"
numproc=480
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
  eventlist=`cat $eventfile`
  nevents=`cat $eventfile | wc -l`
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
    linkbase=$pbsdir"/outputbase/"$event
    rm -rf $linkbase/DATABASES_MPI/*
    echo "Idx: $event_index_name --- event $event"
    echo "subrun dir: $subrundir"
    echo "linkbase: $linkbase"
    ### LINK HERE
    ln -s $linkbase $subrundir
    if [ $event_idx == 1 ]; then
      model_base=$specfemdir"/DATABASES_MPI"
      echo "model base: "$mode_base
      # LINK MODEL file for run0001 only
      ln -s $model_base"/attenuation.bp" $subrundir"/DATABASES_MPI/attenuation.bp"
      ln -s $model_base"/boundary.bp" $subrundir"/DATABASES_MPI/boundary.bp"
      ln -s $model_base"/solver_data.bp" $subrundir"/DATABASES_MPI/solver_data.bp"
      ln -s $model_base"/solver_data_mpi.bp" $subrundir"/DATABASES_MPI/solver_data_mpi.bp"
      ln -s $model_base"/proc000000_reg1_topo.bin" $subrundir"/DATABASES_MPI/proc000000_reg1_topo.bin"
      echo "check model link"
      ls -alh $subrundir/DATABASES_MPI
    fi
    echo "check dir"
    ls -alh $subrundir
    event_idx=$(( $event_idx + 1))
  done

  # ############################################
  # job running
  echo "^^^^^^^^^^^^^^^^^^^^^^^^"
  cd $specfemdir
  echo "cd to specfemdir: `pwd`"
  #ls -alh
  echo "solver start: `date`"
  aprun -n $numproc -N1 ./bin/xspecfem3D
  touch run0001/OUTPUT_FILES/proof.txt
  echo "solver end: `date`"

  # ############################################
  # Unlink
  echo "^^^^^^^^^^^^^^^^^^^^^^^^"
  echo "Remove symbolic links..."
  event_idx=1
  for event in ${eventlist[@]}
  do
    # UNLINK HERE
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
