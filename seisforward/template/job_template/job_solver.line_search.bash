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
#PBS -l walltime=NAN

# -----------------------------------------------------
# This is a simulataneous and serial job script
# for example, you have 250 events and 50 simultaneous run
# So it needs to loop 5 times in serial, inside which 50
# simultaneous runs
# User Parameter
# -----------------------------------------------------
model_perturbs=NAN

cd $PBS_O_WORKDIR
cat $PBS_NODEFILE > compute_nodes.$PBS_JOBID
echo "$PBS_JOBID" > jobid.$PBS_JOBID

pbsdir=`pwd`
echo "running simulation: `date`"
echo "Current directory: `pwd`"
echo

for mp in ${model_perturbs[@]}
do
  echo "+++++++++++++++++++++++++++++++++++++++++++++++++"
  echo "Launching perturbation in dir: $mp"
  subdir="perturb_$mp"
  if [ ! -d $subdir ]; then
    echo "No subdir: $subdir"
    exit
  fi
  # get into job dir
  cd $subdir
  echo "cd to dir: `pwd`"
  echo "bash job_solver.bash"
  bash job_solver.bash
  # return back
  cd $pbsdir
  echo "back to dir: `pwd`"
done

echo -e "\n*********************************"
echo "Summary: "
echo "Success!"
echo -e "*********************************\n"
