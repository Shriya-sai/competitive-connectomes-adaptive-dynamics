# Perturbation Explorer

[Open the deployed explorer](https://shriya-sai.github.io/competitive-connectomes-adaptive-dynamics/).

A dependency-free browser interface for exploring the frozen whole-brain Hopf
perturbation results. The committed JSON contains median regional response
profiles for 128 experimental conditions derived from 15,360 paired
confirmation runs. Playback uses the actual intervention-minus-control BOLD
trajectory from frozen confirmation seed 300 for each condition. No JavaScript
packages or build step are required.

Regenerate the data after reproducing the model and perturbation analysis:

```bash
python scripts/export_brain_dynamics_ui.py
```

Run the interface from the repository root:

```bash
python -m http.server 8000 --bind 127.0.0.1 --directory ui
```

Open `http://127.0.0.1:8000/`.

The bilateral node layout is deterministic and schematic; it is not an
anatomical atlas projection. Playback is literal model time: every pulse sample
is retained and recovery is sampled every four TRs. Values are int16-quantized
with a per-trajectory scale recorded in the export; reconstruction error is at
most `scale / 32767`. Summary metrics remain medians across all 30 confirmation
seeds, while the animated trajectory is explicitly one untouched seed rather
than a synthetic average.
