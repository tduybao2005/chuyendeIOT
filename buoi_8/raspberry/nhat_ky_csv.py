"""Ghi cac ban ghi doc ve tu server thanh file CSV theo tung ngay."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


COT = [
    "id",
    "thoi_gian_gui",
    "ten_thiet_bi",
    "nhiet_do",
    "do_am",
    "led1",
    "led2",
    "led3",
]


class NhatKyCsv:
    def __init__(self, thu_muc="nhat_ky", dong_ho: Callable[[], datetime] = datetime.now):
        self._thu_muc = Path(thu_muc)
        self._dong_ho = dong_ho

    def ghi(self, ban_ghi: dict[str, Any]) -> Path:
        self._thu_muc.mkdir(parents=True, exist_ok=True)
        ngay = self._dong_ho().strftime("%Y-%m-%d")
        duong_dan = self._thu_muc / f"du_lieu_{ngay}.csv"
        can_tao_header = not duong_dan.exists() or duong_dan.stat().st_size == 0

        dong = [self._gia_tri(ban_ghi, cot) for cot in COT]
        with duong_dan.open("a", newline="", encoding="utf-8") as tep:
            writer = csv.writer(tep)
            if can_tao_header:
                writer.writerow(COT)
            writer.writerow(dong)
        return duong_dan

    @staticmethod
    def _gia_tri(ban_ghi: dict[str, Any], cot: str) -> str:
        gia_tri = ban_ghi.get(cot, "")
        if gia_tri is None:
            return ""
        if cot == "thoi_gian_gui":
            return str(gia_tri).replace("T", " ").split(".")[0].split("+")[0]
        return str(gia_tri)