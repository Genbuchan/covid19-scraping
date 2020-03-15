# -*- coding: utf-8 -*-
import re

from datetime import datetime, timedelta

from typing import Dict

from util import excel_date, get_file, get_weekday, dumps_json, jst
from summary import MainSummary


class Patients:
    def __init__(self):
        self.sheets = get_file("/kk03/corona_kanjyajyokyo.html", "xlsx")["公表"]
        self.patients_count = 5
        self._patients_json = {}
        self._patients_summary_json = {}
        self.get_patients()

    def patients_json(self) -> Dict:
        if not self._patients_json:
            self.make_patients()
        return self._patients_json

    def patients_summary_json(self) -> Dict:
        if not self._patients_summary_json:
            self.patients_json()
            self.make_patients_summary()
        return self._patients_summary_json

    def make_patients(self) -> None:
        self._patients_json = {
            "data": [],
            "last_update": self.get_last_update()
        }
        for i in range(5, self.patients_count):
            data = {}
            release_date = excel_date(self.sheets.cell(row=i, column=3).value)
            data["No"] = self.sheets.cell(row=i, column=2).value
            data["リリース日"] = release_date.isoformat()
            data["曜日"] = get_weekday(release_date.weekday())
            data["居住地"] = self.sheets.cell(row=i, column=7).value
            data["年代"] = str(self.sheets.cell(row=i, column=4).value) + "代"
            data["性別"] = self.sheets.cell(row=i, column=5).value
            data["退院"] = None
            data["備考"] = re.sub('NO.|N0.|NO,|N0,|No,', 'No.', str(self.sheets.cell(row=i, column=11).value)).replace("・", "、")
            data["date"] = release_date.strftime("%Y-%m-%d")
            self._patients_json["data"].append(data)
        self._patients_json["data"].reverse()

    def make_patients_summary(self) -> None:
        def make_data(date):
            data = {}
            data["日付"] = date
            data["小計"] = 1
            return data

        self._patients_summary_json = {
            "data": [],
            "last_update": self.get_last_update()
        }

        prev_data = {}
        for patients_data in self.patients_json()["data"]:
            date = patients_data["リリース日"]
            if prev_data:
                prev_date = datetime.strptime(prev_data["日付"], "%Y-%m-%dT%H:%M:%S+09:00")
                patients_zero_days = (datetime.strptime(date, "%Y-%m-%dT%H:%M:%S+09:00") - prev_date).days
                if prev_data["日付"] == date:
                    prev_data["小計"] += 1
                    continue
                else:
                    self._patients_summary_json["data"].append(prev_data)
                    if patients_zero_days >= 2:
                        for i in range(1, patients_zero_days):
                            self._patients_summary_json["data"].append(
                                {
                                    "日付": (prev_date + timedelta(days=i)).astimezone(jst).isoformat(),
                                    "小計": 0
                                }
                            )
            prev_data = make_data(date)
        self._patients_summary_json["data"].append(prev_data)

    def get_last_update(self) -> str:
        data_time_str = str(self.sheets.cell(row=3, column=16).value).replace("\u3000", " ")
        if data_time_str[-5:] == "24時現在":
            day_str, hour_str = data_time_str[-8:].split()
            day_int = int(day_str)
            data_time_str = data_time_str[:-8] + str(day_int + 1) + " 0時現在"
        return datetime.strptime(
            "2020/" + data_time_str, "%Y/%m/%d %H時現在"
        ).strftime("%Y/%m/%d %H:%M")

    def get_patients(self) -> None:
        while self.sheets:
            self.patients_count += 1
            value = self.sheets.cell(row=self.patients_count, column=2).value
            if not value:
                break


class Inspections:
    def __init__(self):
        self.sheets = get_file("/kf16/singatakoronakensa.html", "xlsx")["Sheet1"]
        self.inspections_count = 2
        self._inspections_json = {}
        self._inspections_summary_json = {}
        self.get_inspections()

    def inspections_json(self) -> Dict:
        if not self._inspections_json:
            self.make_inspections()
        return self._inspections_json

    def inspection_summary_json(self) -> Dict:
        if not self._inspections_summary_json:
            self.make_inspections()
            self.make_inspections_summary()
        return self._inspections_summary_json

    def make_inspections(self) -> None:
        self._inspections_json = {
            "data": [],
            "last_update": self.get_last_update()
        }
        for i in range(2, self.inspections_count):
            date = self.sheets.cell(row=i, column=1).value
            data = {}
            data["判明日"] = date.strftime("%d/%m/%Y")
            pcr = self.sheets.cell(row=i, column=2).value
            data["検査検体数"] = pcr if pcr else 0
            data["陽性確認"] = self.sheets.cell(row=i, column=3).value
            self._inspections_json["data"].append(data)

    def make_inspections_summary(self) -> None:
        self._inspections_summary_json = {
            "data": {
                "検査検体数": [],
                "陽性確認": []
            },
            "labels": [],
            "last_update": self.get_last_update()
        }
        for inspections_data in self.inspections_json()["data"]:
            date = datetime.strptime(inspections_data["判明日"], "%d/%m/%Y")
            self._inspections_summary_json["data"]["検査検体数"].append(inspections_data["検査検体数"])
            self._inspections_summary_json["data"]["陽性確認"].append(inspections_data["陽性確認"])
            self._inspections_summary_json["labels"].append(date.strftime("%m/%d"))

    def get_last_update(self) -> str:
        data_time = self.sheets.cell(row=self.inspections_count-1, column=1).value + timedelta(days=1)
        return data_time.strftime("%Y/%m/%d %H:%M")

    def get_inspections(self) -> None:
        while self.sheets:
            self.inspections_count += 1
            value = self.sheets.cell(row=self.inspections_count, column=1).value
            if not value:
                break


if __name__ == '__main__':
    patients = Patients()
    inspections = Inspections()
    main_summary = MainSummary()
    dumps_json("patients.json", patients.patients_json())
    dumps_json("patients_summary.json", patients.patients_summary_json())
    dumps_json("inspections.json", inspections.inspections_json())
    dumps_json("inspections_summary.json", inspections.inspection_summary_json())
    dumps_json("main_summary.json", main_summary.get_summary_json())
