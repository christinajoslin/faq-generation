**Q: How can I resolve login issues with Purdue's GitHub instance due to incorrect LDAP ID or password errors?**

**A:** Login issues with github.itap.purdue.edu often stem from using the full email address instead of your Purdue career account username (e.g., your-username). Ensure there are no accidental additions, like "push," at the end of your password. Verify that you can log into other Purdue services, such as myPurdue, to confirm your LDAP credentials are correct. If issues persist, try logging in with a private or alternate browser and ensure authentication on platforms requiring LDAP integration, like BoilerAD. Contact IT support for unresolved cases.

**Q: How do I resolve a "permission denied" error when attempting to log into an RCAC cluster?**

**A:** To address a "permission denied" login issue on the RCAC cluster, follow these steps:


1. **Cluster Identification**: Confirm which specific RCAC cluster you're trying to access.
2. **Queue Activity**: Ensure your account is active and not blocked on any of its queues.
3. **Access Purchase**: Verify that your group has purchased necessary access from your supervisor.

Providing these details can help identify the root cause of the issue, allowing for appropriate resolution steps.

**Q: Why might my jobs be delayed or fail to start on the Gilbreth cluster?**

**A:** Jobs may experience delays or failures on the Gilbreth cluster due to several common issues:


1. **Maintenance Reservations**: Scheduled maintenance can reserve nodes, preventing job execution. To mitigate this, resubmit your jobs with shorter walltimes before the maintenance window begins.

2. **PartitionDown Errors**: These occur when hardware is unavailable due to cooling or facility problems, causing job submission failures. Monitor cluster announcements for updates on service restoration.

3. **Resource Limits**: Ensure that your job requests do not exceed available resources in any partition. Adjust according to `sacctmgr show QOS` output.

4. **Outages and Facility Issues**: Power outages or water issues can temporarily shut down the cluster, leading to delays. 

5. **Cooling Problems**: Similar to facility issues, cooling problems can lead to unavailable partitions.

To troubleshoot, regularly check job statuses using commands like `jobinfo <job_id>` or `squeue -lj <job_id>`, and align your submissions with current cluster policies and queue statuses. Adjust walltimes if needed to avoid maintenance reservations.

**Q: Why do processes like "slurm_gpustat" frequently die on Gilbreth's front-end node after a few hours, especially when intended to run for extended periods?**

**A:** Processes often terminate unexpectedly on Gilbreth's front-end nodes due to periodic reboots and their unsuitability for long-term tasks. To ensure stability over extended durations, submit jobs directly to compute nodes using SLURM rather than relying on `nohup`. This approach allows setting a runtime limit, which helps manage resources effectively and minimizes unexpected terminations. For guidance on submitting your job, refer to the [Gilbreth Job Submission Guide](https://www.rcac.purdue.edu/knowledge/gilbreth/run/slurm/submit). Additionally, consider implementing monitoring scripts to automatically restart processes if they stop unexpectedly.

**Q: Why am I unable to log into the Negishi cluster and how can I resolve LDAP authentication issues?**

**A:** If you're experiencing difficulty logging into the Negishi cluster due to LDAP authorization check failures or incorrect credentials, it might be related to ongoing maintenance or recent system changes. To resolve this:


1. **Check for Maintenance Updates**: Visit https://www.rcac.purdue.edu/news/6189 or https://www.rcac.purdue.edu/news/7106 to see if any scheduled maintenance is affecting LDAP services.

2. **Verify Credentials**: Ensure your username and password are correct, including any necessary passcode details unless specifically using other clusters like Bell.

3. **Clear Existing Sessions**: When logging in via ThinLinc or the Gateway, check 'End existing sessions' before entering your credentials to avoid session conflicts.

4. **Retry After Some Time**: If issues persist due to maintenance, attempt to log in again after the scheduled maintenance window ends.

These steps should help resolve common LDAP authentication errors on the Negishi cluster.

**Q: What should I do if my Gilbreth cluster session fails to start or shows resource allocation issues?**

**A:** Ensure you have successfully submitted a job request using SLURM (`sbatch`). Verify your session by checking the `myquota` output to confirm available space in your HOME directory. Specify the correct account with the `--account` option in the `srun` command and use the following example for guidance:


```
srun --account=your-account-name -n 1 --gres=gpu:1 --cpus-per-task=4 --mem=8000M --partition=debug --pty bash
```

To list available accounts and partitions, run `slist your-account-name`. If the issue persists, try accessing the Jupyter Notebook with:

```
module load singularity
singularity exec --pwd /scratch/your-username /cluster/apps/software/jupyter-notebook jupyter-notebook
```

Replace 'your-username' with your actual username. For slow speed and freezing issues on the cluster, switch to a different login node for relief.

**Q: How can I request access to faster computing resources like HPC clusters at RCAC for tasks such as ANSYS simulations?**

**A:** To access HPC clusters including Gilbreth, Negishi, Bell, Anvil, or Data Workbench for tasks like ANSYS simulations, you need your advisor to have purchased access. You can then request access via the [RCAC Account Request](https://www.rcac.purdue.edu/account/request) page or through your advisor's account portal. If needed, your professor can contact RCAC directly to set up a group account if they haven't already done so. Note that the Scholar cluster is only available for instructional purposes and not for research after courses conclude. For more details on available resources, consult with ECN.

**Q: How can I resolve permission issues when installing Python packages on HPC clusters using Conda?**

**A:** To avoid permission problems when installing Python packages on HPC clusters like Bell or Gilbreth, use Conda within a dedicated environment:


1. **Create a Conda Environment**: Start by creating an isolated environment with your desired Python version:
   ```bash
   conda create -n myenv python=3.XX
   ```
   Replace `myenv` with your chosen name and `3.XX` with the specific Python version.

2. **Activate Your Environment**:
   ```bash
   conda activate myenv
   ```

3. **Install Packages**: Use Conda to install packages, specifying any necessary channels like `conda-forge` if needed:
   ```bash
   conda install -c conda-forge package_name
   ```
   Substitute `package_name` with the desired library.

4. **Load Necessary Modules**: Ensure that all required modules are loaded before installations or running scripts to address dependencies or configuration issues.

Using Conda environments helps mitigate permission-related problems and simplifies package management across various RCAC clusters.

**Q: How can I resolve "license not found" errors when using COMSOL on HPC clusters like Negishi and Bell?**

**A:** To resolve "license not found" errors with COMSOL, ensure you are affiliated with the College of Engineering at Purdue University or collaborating with its faculty. If affiliated, contact support to verify your permissions and add you to the necessary groups. Use `module load comsol` followed by `comsol` in a terminal session on ThinLinc or Gateway for Negishi. Verify the installed COMSOL version's compatibility with your OS. For module loading issues, try `module --ignore-cache load "comsol"`. Check user license counts and collaborate with your department if additional licenses are needed.

**Q: What can I do if I experience slow module loading or SSH connection hangs when accessing the Bell HPC system?**

**A:** Slow response times or hanging SSH connections on the Bell cluster may be due to recent Depot performance issues. To address this, try the following steps:


1. **Log into Different Front-End Nodes:** Determine if the issue is isolated to a specific node by logging in from different nodes.
2. **Verify Network Connection:** Ensure your internet connection is stable, especially when using Wi-Fi.
3. **Retry Connections:** If the login node seems overloaded, wait briefly and try reconnecting.
4. **Monitor Updates:** Check RCAC news for updates on system performance at [RCAC News](https://www.rcac.purdue.edu/news/5934) to stay informed about any ongoing issues or resolutions.

These steps may help identify and resolve common problems related to module loading and SSH connectivity without further assistance.

**Q: How can I efficiently synchronize files between the Negishi cluster and another cluster, like NSF?**

**A:** Use the `rsync` command to synchronize files between clusters without needing additional software installations. This method provides efficient file transfer with progress display. The basic command format is:


```
rsync -ah --info=your-username SOURCE DESTINATION
```

For example, to sync files from an NSF cluster to Negishi, use:

```
rsync -ah --info=your-username nsfcluster.edu:/path/to/files ${CLUSTER_SCRATCH}/nsf_files
```

This approach keeps your file versions updated across different systems. For handling large .zip files, utilize the Globus transfer service instead of downloading directly via the Negishi Gateway. Additional details can be found at [Negishi Storage Transfer](https://www.rcac.purdue.edu/knowledge/negishi/storage/transfer/globus).

**Q: Why might my Abaqus jobs be experiencing delays while waiting for tokens in a queue when using Hypershell on an HPC cluster?**

**A:** Delays with Abaqus jobs in the queue often occur due to inefficient token distribution among parallel workers in Hypershell. To address this, ensure backend licenses are available and optimize token allocation by adjusting tasks per node. Verify that there are no out-of-memory (OOM) issues affecting your jobs. Consider modifying configuration settings such as the number of resources allocated per node for better performance. Check relevant documentation related to job processing if necessary.

**Q: How can I resolve issues related to incorrect interpreter settings and environment module usage in job submissions on HPC clusters?**

**A:** If you encounter problems with job submission due to incorrect interpreter settings or environment module usage, modify your script by changing the shebang line from `#!/bin/bash` to `#!/bin/sh -l`. Also, ensure proper initialization of modules by adding `source /etc/profile.d/modules.sh` at the beginning of your script before using any module commands like `module purge`. For issues specifically related to 'mpirun' on certain HPC clusters, replace instances of `mpirun -np [number]` with `srun -n [number]`, and submit jobs using `srun sbatch -n [number] your_job_script.sh`. These adjustments help ensure correct interpreter settings and module loading across different scenarios.

**Q: How can I verify access and check the availability of Nvidia A100 GPUs on the Gilbreth cluster?**

**A:** To verify your access to Nvidia A100 GPUs on the Gilbreth cluster, use the `slist` command followed by your username. This will display details about available resources under your account, including how many GPUs are accessible:


```
$ slist <your-username>
Current Number of GPUs Node Account Total Queue Run Free Max Walltime Type ============== ================================= ============== ====== canli-k 1 0 0 1 14-00:00:00 K debug 182 0 0 182 00:30:00 B,D,E,F,G,H,I standby 272 1125 64 151 04:00:00 B,D,E,F,G,H,I,K
```

The "Free" column indicates the number of A100 GPUs currently available to your account. If further details about license requirements are needed, contact the Engineering Computer Network (ECN).

**Q: Why might I not see or have access to certain queues on Gilbreth?**

**A:** If you're unable to see or access specific queues on the Gilbreth cluster, consider these potential causes:


1. **Expired Queue Access**: Ensure your group's allocation has been renewed. Coordinate with your PI to submit a purchase request if necessary.

2. **Group Membership and LDAP Synchronization**: Verify that you are part of the correct research group using `groups your-username`. If recently added, allow up to four hours for LDAP synchronization to update your access.

3. **Command Syntax Errors**: Use the correct syntax when accessing queues (e.g., `sinteractive -A name-g`).

4. **System Outages or Propagation Delays**: Check if there are ongoing system issues that could affect queue visibility, such as power outages or delays in configuration propagation from Halcyon to SLURM.

5. **Pending Account Additions**: If not part of a group, ensure your PI has submitted an order for you to access Gilbreth. For Rowdy clusters, verify if manual addition is needed through RCAC's account request portal.

By addressing these issues, you can resolve most visibility or access problems related to queues on the Gilbreth cluster.

