# v5.28 Spatial layer compositor and mask editor

v5.28 turns saved detections and segmentations into persistent, editable layers rather than one-off model results.

## Persistent layer model

Every saved box, polygon, mask, or composite keeps its own layer record with:

- stable annotation ID and stack order;
- name, visibility, lock state, color, opacity, and blend mode;
- source and model provenance;
- confidence where the producing model supplied one;
- parent layer IDs for derived/composite layers;
- revision history for saved edits.

Model output, user-created annotations, imported Krita masks, and composite results can coexist on the same image. Running another model appends layers without replacing earlier work.

## Detection and box composition

The **Detection & Boxes** stack supports selecting any number of saved box layers and creating a new editable box by:

- union/enclosing bounds;
- intersection/common area;
- coordinate average;
- confidence-weighted average.

The sources are preserved by default. The user can load any box, including a model-generated or composite box, into the canvas editor and move or resize it before updating that layer or saving a new one.

## Segmentation and mask composition

The **Segmentation & Masks** stack supports selecting any number of compatible saved mask layers and creating a new editable mask by:

- union;
- intersection;
- subtracting all following masks from a chosen base layer;
- XOR/symmetric difference.

Optional threshold, feather, and grow/shrink processing is applied to the new composite. Grayscale/alpha strengths are preserved so feathered model masks and semi-transparent brush strokes are not forced to hard binary pixels during composition. Source masks are preserved unless the user explicitly requests deletion.

Selected saved layers and selected unsaved model previews can also be loaded directly into the pixel editor using replace, add, subtract, intersection, or XOR. This allows model output, a prior composite, a Krita-edited mask, and a hand-painted layer to be combined and refined before saving. If selected preview layers are used by a compositor operation, the app promotes them to persistent source layers automatically before creating the composite.

## Manual mask tools

The embedded mask editor includes:

- variable-size brush and eraser;
- brush opacity and hardness;
- freehand lasso selection;
- ellipse and rectangular selection;
- add, subtract, and replace shape modes;
- magic selection using contiguous flood fill, non-contiguous similar color, or GrabCut-style estimation where available;
- tolerance, feather, grow/shrink, and inversion controls;
- overlay color and transparency;
- local undo/redo, invert, and clear;
- multiple independent object layers per image.

Magic selection uses OpenCV when available and a NumPy/Pillow fallback otherwise.

## Layer management

Both spatial editors provide:

- select all / clear selection;
- drag-and-drop stack reordering plus Move Up/Move Down controls;
- show/hide and lock/unlock;
- rename, recolor, adjust opacity, and change overlay blend mode;
- duplicate and delete;
- restore the state before the latest saved edit;
- clear unsaved model previews separately from deleting saved model layers;
- persist selected model preview results as individual layers.

When a model/API layer is manually edited, its original provenance is retained in metadata and the edited layer is protected from model-only cleanup.

## Storage and interoperability

Mask files are stored as unique PNGs under the annotation output directory. Layer records remain in SQLite and are available to later model runs, orchestration steps, Krita handoffs, exports, and future training-set builders.
