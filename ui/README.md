# Perturbation Explorer

A dependency-free browser interface for exploring the frozen whole-brain Hopf
perturbation results. The committed JSON contains median regional response
profiles for 128 experimental conditions derived from 15,360 paired
confirmation runs. No JavaScript packages or build step are required.

Regenerate the data after reproducing the model and perturbation analysis:

```bash
python scripts/export_brain_dynamics_ui.py
```

Run the interface from the repository root:

```bash
python -m http.server 8000
```

Open `http://localhost:8000/ui/`.

The bilateral node layout is deterministic and schematic; it is not an
anatomical atlas projection. Playback stages regional response amplitudes to
make propagation patterns inspectable and is not presented as the literal Hopf
time series. Numerical values come from the frozen confirmation outputs.
