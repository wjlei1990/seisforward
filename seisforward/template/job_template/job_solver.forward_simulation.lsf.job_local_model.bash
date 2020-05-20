#!/bin/bash

#BSUB -P GEO111
#BSUB -J solver
#BSUB -N
#BSUB -o log.solver.%J
#BSUB -alloc_flags gpumps
#BSUB -nnodes 960
#BSUB -W 2:00

# -----------------------------------------------------
# This is a simulataneous and serial job script
# for example, you have 250 events and 50 simultaneous run
# So it needs to loop 5 times in serial, inside which 50
# simultaneous runs
# User Parameter
specfemdir=NAN
linkbase=NAN
# ---
total_serial_runs=NAN
timeout_aprun=NAN
# ---
nres=NAN
nmpi_per_res=NAN
ncpu_per_res=NAN
# -----------------------------------------------------

jobdir=`pwd`
echo "job submit directory: $LS_SUBCWD"
echo "Current directory: $jobdir"
echo "running simulation: `date`"
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
    echo "----------"
    event_index_name=`printf "%04d" $event_idx`
    subrundir="$specfemdir/run$event_index_name"
    linkdir=$linkbase/$event
    echo "Idx: $event_index_name --- event $event"
    echo "subrun dir: $subrundir"
    echo "linkdir: $linkdir"
    ### remove $subrundir
    if [ -e $subrundir ]; then
      rm $subrundir
    fi
    ### LINK run000* to linkdir
    ln -s $linkdir $subrundir
    # echo "check dir"
    # ls -alh $subrundir
    event_idx=$(( $event_idx + 1))
  done

  # ############################################
  # job running
  echo "^^^^^^^^^^^^^^^^^^^^^^^^"
  cd $specfemdir
  echo "cd to specfemdir: `pwd`"
  echo "solver start: `date`"
  echo "jsrun -n $nres -a $nmpi_per_res -c $ncpu_per_res -g 1 ./bin/xspecfem3D"
  jsrun -n $nres -a $nmpi_per_res -c $ncpu_per_res -g 1 ./bin/xspecfem3D
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
  cd $jobdir
  # end of one eventlist file
done
# end of all eventlist files

echo -e "\n*********************************"
echo "Summary: "
echo "Success!"
echo -e "*********************************\n"
