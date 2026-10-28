"""Candidate-only window icon, preserving the upstream application's icon."""
from pathlib import Path
import tkinter
from src import constants


def apply_candidate_icon(root):
    path = Path(constants.RESOURCE_DIR) / 'resources/icons/draft.png'
    if path.is_file():
        root._candidate_icon = tkinter.PhotoImage(master=root, file=str(path))
        root.iconphoto(True, root._candidate_icon)
