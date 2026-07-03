# v5.44 Stoppable Downloads and Conda Script Activation

The Jobs tab has stop controls for downloads:

- **Stop Queued/Running Downloads** cancels queued or running jobs whose type contains `download`.
- **Stop Checked Jobs** cancels checked job rows.
- Backend endpoint: `POST /api/jobs/cancel`.

Queued jobs are cancelled before their worker starts. Running jobs are cooperative; a very large in-progress file transfer may finish its current file before the worker exits.

Model downloads use a dedicated `model_download` lane, serial by default, so large model downloads do not consume the general app job pool.

Windows scripts now use `scripts/find_conda.bat` and `scripts/activate_data_curation_env.bat` to find user-folder Conda installs such as `%USERPROFILE%\miniconda3\condabin\conda.bat`. Override with `DCT_CONDA_BAT`. Shell scripts source `scripts/activate_data_curation_env.sh`; override with `DCT_CONDA_BASE`.
