# Forward simulations

1. Prepare the `config.yml` file and cmtlist file.
  In the config file, you will need to specify
    * simulation type
    * database name
    * job information, such as the directory of running base, cmts, stations.
      The cmtlist file should contains the names of all events.
    * job configuration, such as the number of simulataneous runs and serial runs.

  In the cmtlist file, all eventnames are stored in this file.


2. Create an empty database using:
  ```
    seisforward-create_database -c config.yml
  ```

  Job entries will be filled in next step


3. Fill the database with jobs using:
  ```
    seisforward-fill_database -c config.yml -v
  ```

  For forward simulation, it will fill each entry with the path of cmtfile, station file and event running directory, which are input information for forward runs.


4. setup the running directory using:
  ```
    seisforward-setup_runbase -c config.yml
  ```

  It will first setup necessary(empty) folders, including:
    * `archive`: event running and output direcotry
    * `jobs`: job submission script folder
    * `specfem3d\_globe`: specfem code related file, like mesh, binary and etc.

  Then, it copies the specfem related files into the folder `specfem3d\_globe`.


5. create jobs using:
  ```
    seisforward-create_jobs -c config.yml
  ```

  It works as following:
    * fetch a certain number(n\_serial * nevents\_per\_simul\_run) new job(event) entries from the database.
    * setup directory for each job(event), specifically copy the cmtsolution, station file, values\_from\_mesher.h and addressing.h in `archive` directory.
    * prepare the job submission script dir.
      * First, it will split the eventlist based on the number of simulataneous runs.
      * Second, it will make a local copy of specfem(model files won't be copied because of the size so make sure all the jobs in this running base use the same model file).
      * Third, it generate the pbs job script based on current settings.
      * Fouth, it modify the specfem parfile, such as simulation type, save forward flag and so on.
