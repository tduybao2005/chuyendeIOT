"""Cho pytest thay cac module cua server (nam o thu muc cha cua tests/)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
