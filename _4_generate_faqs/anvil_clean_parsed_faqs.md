**Q: How can I resolve job submission errors on Anvil due to an invalid account or partition combination?**

**A:** Ensure you specify the correct account and partition in your `sbatch` command using:


```bash
sbatch [options] -A <account> -p <partition> script.sh
```

Replace `<account>` with your actual account name and `<partition>` with the intended partition. If unsure, consult system documentation or a local administrator for guidance. For more details, refer to the [SLURM documentation](https://slurm.schedmd.com/documentation.html).

**Q: Why am I experiencing login issues with Purdue Anvil, and how can they be resolved?**

**A:** Login difficulties to Purdue Anvil often stem from account setup, propagation delays, or incorrect configurations. If encountering "failed to map user" errors, ensure your account is correctly added in [Anvil User Management](https://allocations.access-ci.org/user_management) and verify that you are included in necessary allocations by contacting your PI. Ensure SSH keys are properly configured if using remote login commands, following the [Open OnDemand User Guide](https://www.rcac.purdue.edu/knowledge/anvil/access/login/ood) and [Anvil SSH Keys Guide](https://www.rcac.purdue.edu/knowledge/anvil/access/login/sshkeys). Allow a few days for account propagation if recently added. To resolve session issues, clear your web browser's cache and cookies. If encountering syntax errors or module loading issues, adjust `.bashrc` by commenting out problematic lines (e.g., bind commands causing line editing issues) and reload necessary modules with `module load <module_name>`. Ensure your home directory isn't full; check usage with `$ myquota x-ddickson`, locate large files using `find ~ -type f -size +100M`, and delete or archive them as needed.

**Q: How can I resolve configuration and installation errors related to FFTW when setting up PETSc on Anvil?**

**A:** To address FFTW-related issues during the configuration and installation of PETSc on Anvil, modify your `install_ANVIL.sh` script. Replace any commands that download FFTW with a line that loads the existing module using `module load fftw`. After updating the script, retry installing PETSc. If errors persist, consult the output file (e.g., `slurm-<job-id>.out`) for additional clues and adjust as necessary.

**Q: How can I access and use Gaussian software on Anvil when it is not pre-installed?**

**A:** To use Gaussian on Anvil, obtain an allocation through Expanse by transferring credits since Anvil lacks a native license for Gaussian. Contact Joan Shea (PI for MCA05S027) to request a supplement via ACCESS at <https://allocations.access-ci.org>. Follow these steps:


1. Log in and go to "Manage Allocations."
2. Select the relevant allocation.
3. Choose "Supplement" for your action.

After review, you will receive a notification about the decision. Once approved, access Gaussian through Expanse using the allocated time.

**Q: Why am I encountering Out of Memory errors with VASP calculations on Anvil, and how can I resolve them?**

**A:** Out of Memory errors in VASP on Anvil often stem from memory leaks or improper setup for large-scale jobs. To address these issues:


1. Check your INCAR file by running smaller test jobs to ensure configurations are suitable.
2. Modify parameters like `NSW`, `NELM`, or `EDIFF` that affect memory usage if small jobs succeed but larger ones fail.
3. Ensure the job script specifies correct resource allocation using `#SBATCH -A myallocation`.
4. Load necessary modules, such as VASP and its dependencies, before submitting your job.
5. Verify paths for libraries in environment variables are set correctly.
6. Consider compiling VASP with OpenMPI version 4.1.6 or later to avoid memory leaks associated with earlier versions.

**Q: How can I gain access to the Anvil HPC system at Purdue University?**

**A:** Access to the Anvil HPC system requires being part of an active allocation. If you are not yet included, contact the PI managing your project on Anvil for addition or apply for a new allocation via the ACCESS website. Refer to these resources for detailed steps: [Prepare Requests Overview](https://allocations.access-ci.org/prepare-requests-overview) and [Submit a Proposal Guide](https://allocations.access-ci.org/prepare-requests-overview). These actions ensure compliance with system access policies and facilitate your project contributions.

**Q: What should I do if I encounter a "stale file handle" error when accessing directories on Anvil?**

**A:** A "stale file handle" error typically arises from issues with directory caching or synchronization in the GPFS filesystem. To resolve this:


1. **Reconnect to Different Nodes**: Try logging into alternative nodes like `\_g005.anvil.rcac.purdue.edu` and `\_g008.anvil.rcac.purdue.edu`, then access your directories again.

2. **Clear Lock Files**: If related to specific job locks, remove them using:
   ```
   rm -rf .Slurm_XXX
   ```
   Replace "XXX" with the job ID of a failed Slurm job found by running `ls -ltrh | grep slock`.

3. **Regular Backups**: Regularly back up your work using tools like `rsync`, `scp`, or Globus to prevent data loss.

These steps should help you regain access to your files on Anvil while minimizing disruption.

**Q: How can I effectively manage and request increases for my file number limits on the Anvil HPC cluster?**

**A:** To manage your file quotas efficiently on Anvil HPC, utilize the personal scratch directory with its large 100TB quota and consider using archive formats like `.zip` or `.tar` to optimize storage. Regularly monitor your usage with `myquota`. For long-term storage, use project directories that offer a 5TB limit. If you need an increase in file number limits (e.g., from 1M to 2M) for research purposes such as image classification models, contact Anvil HPC support with details about your current usage and justification for the request. The support team will review your application and provide guidance on how to proceed. Remember that inactive files in the personal scratch directory are purged after 30 days if not accessed.

**Q: How do I resolve BerkeleyGW software job submission issues on Anvil due to MPI configuration errors?**

**A:** To address BerkeleyGW job execution problems on Anvil caused by incorrect MPI settings, ensure you use the `--mpi=your-username` option with your `mpirun` command. Update your job script as follows:


```bash
mpirun --mpi=your-username -np $SLURM_NTASKS $BGW/epsilon.cplx.x
```

Load necessary modules before running your script:

```bash
module load intel impi intel-mkl your-username libszip
```

Verify that the `$QE` and `$BGW` variables in your script point to the correct directories containing the Quantum Espresso and BerkeleyGW executables. For example:

```bash
QE=/home/your-username/qe-7.2/bin
BGW=/home/your-username/BerkeleyGW-3.0.1-your-username/bin
```

This should help resolve job submission issues related to MPI configuration on Anvil.

**Q: How can I access and use VASP software on the Anvil HPC system?**

**A:** To access VASP software on Anvil, ensure your account is added to the appropriate Unix group (e.g., your-username or your-username) by your supervisor. Membership may take a few hours to be ready. Verify your group membership using `$ groups <username>`. Start a new login session for changes to take effect. To load a VASP module, use `module load vaspX.YY` in the terminal, where X.YY corresponds to the version number. For VASP6, include 'module load your-username' in your submit script. Refer to [VASP calculations on Anvil](https://www.rcac.purdue.edu/knowledge/anvil/software/installing_applications/vasp) for detailed instructions.

**Q: How can I handle file number limits when running extensive jobs on the SCRATCH directory or other HPC project spaces?**

**A:** To address file number limits in your HPC environment's SCRATCH directory or project space, consider bundling files using TAR or ZIP to reduce the total count of individual files. Use `tar -cvf archive_name.tar directory/` for creating a tarball and `zip -0 -r archive_name.zip directory/` for a zip file without compression. These commands consolidate multiple small files into fewer large files, minimizing inode usage. Additionally, regularly delete unnecessary files using `rm [filename]` or `rm -r [directoryname]`, ensuring you back up important data before doing so. If your work requires continuous terminal sessions, consider using utilities like TMUX or SCREEN to maintain active connections during long operations. For accessing archive contents as directories, use tools such as ratarmount: `ratarmount training_data.tar other_dirname/`. By managing file organization and storage efficiently, you can avoid exceeding file number limits and continue running your jobs effectively.

**Q: How can I obtain my correct AnvilGPT access allocation number?**

**A:** To obtain your AnvilGPT access allocation number, start by reviewing any emails or documentation from when you first requested access. If necessary, contact support for help locating this information. You can also verify your access through the AnvilGPT platform's notifications or dashboard messages. Additionally, submit a short proposal via the ACCESS website; upon approval, you'll receive credits that can be converted into Anvil Service Units (SUs). Ensure that your request includes any relevant project numbers if linked with NAIRR allocations. For further guidance on managing and understanding different allocation types, visit the [ACCESS Project Types page](https://allocations.access-ci.org/project-types|smart-link) or consult the [AnvilGPT Knowledge Base](https://www.rcac.purdue.edu/knowledge/anvil/anvilgpt).

