import os
from .helper_functions import parse_single_all_tags, write_tags_to_text_file


def load_image_tags(image_path):
    """Return list of tags for given image path.

    Looks for a sibling ``.txt`` file with the same basename.
    Returns an empty list if the tag file does not exist.
    """
    tag_path = os.path.splitext(image_path)[0] + '.txt'
    tags = parse_single_all_tags(tag_path)
    return [t.strip() for t in tags if t.strip()]


def transfer_tags(src_image, dest_image, tags, remove=False):
    """Transfer ``tags`` from ``src_image`` to ``dest_image``.

    Tags already present in ``dest_image`` are not duplicated. If
    ``remove`` is True, transferred tags are removed from ``src_image``.
    """
    src_tags = load_image_tags(src_image)
    dest_tags = load_image_tags(dest_image)

    for t in tags:
        if t not in dest_tags:
            dest_tags.append(t)
        if remove and t in src_tags:
            src_tags.remove(t)

    write_tags_to_text_file('\n'.join(dest_tags), os.path.splitext(dest_image)[0] + '.txt')
    if remove:
        write_tags_to_text_file('\n'.join(src_tags), os.path.splitext(src_image)[0] + '.txt')


def invert_selection(selected, all_items):
    """Return items from ``all_items`` that are not in ``selected``."""
    selected_set = set(selected)
    return [item for item in all_items if item not in selected_set]


def compare_tags(image_a, image_b):
    """Compare tags of two images.

    Parameters
    ----------
    image_a : str
        Path to the first image file.
    image_b : str
        Path to the second image file.

    Returns
    -------
    dict
        Mapping with keys ``"a_only"``, ``"b_only"`` and ``"common"`` denoting
        tags only present in ``image_a``, only in ``image_b`` and in both
        respectively. All tag lists are sorted alphabetically.
    """
    tags_a = set(load_image_tags(image_a))
    tags_b = set(load_image_tags(image_b))

    return {
        "a_only": sorted(tags_a - tags_b),
        "b_only": sorted(tags_b - tags_a),
        "common": sorted(tags_a & tags_b),
    }


def apply_tag_modifications(image_paths, add_tags=None, remove_tags=None):
    """Apply tag additions/removals to multiple images.

    Parameters
    ----------
    image_paths : Iterable[str]
        Collection of image file paths to modify.
    add_tags : Iterable[str], optional
        Tags to add to each image. Existing tags are not duplicated.
    remove_tags : Iterable[str], optional
        Tags to remove from each image if present.
    """
    add_tags = set(add_tags or [])
    remove_tags = set(remove_tags or [])

    for img in image_paths:
        tags = load_image_tags(img)
        tag_set = set(tags)
        tag_set.update(add_tags)
        tag_set.difference_update(remove_tags)
        write_tags_to_text_file("\n".join(sorted(tag_set)), os.path.splitext(img)[0] + ".txt")
