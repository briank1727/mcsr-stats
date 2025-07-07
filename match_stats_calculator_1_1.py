import os
import json
from datetime import datetime
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox

now = datetime.now()
month = now.month
day = now.day
year = now.year

path = f"matches/{month}_{day}_{year}"
files = os.listdir(path)
UUID = "34c876e4a23a4fe5a1fbf76a41db0e78"
json_matches = []
for item in files:
    newPath = os.path.join(path, item)
    with open(newPath, "r") as f:
        dict = json.load(f)
        json_matches.append(dict)


def format_time(milliseconds):
    try:
        total_seconds = int(abs(milliseconds) // 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        sign = "-" if milliseconds < 0 else ""
        return f"{sign}{minutes}:{seconds:02d}"
    except Exception:
        return "0:00"


class Timestamp:
    def __init__(self, time, type):
        self.type = type
        self.time = time


class Match:
    def __init__(self, json_match):
        timestamps = json_match["timelines"][::-1]
        self.id = json_match["id"]
        self.overworld_type = json_match["seedType"]
        self.bastion_type = json_match["bastionType"]
        self.result = ""
        if json_match["result"]["uuid"] == None:
            self.result = "draw"
        elif json_match["forfeited"]:
            self.result = "forfeit"
        else:
            self.result = "completion"

        self.final_time = json_match["result"]["time"]
        self.winner = json_match["result"]["uuid"]
        self.user_timeline = [Timestamp(0, "start")]
        self.opponent_timeline = [Timestamp(0, "start")]
        for timestamp in timestamps:
            if timestamp["uuid"] == UUID:
                self.user_timeline.append(
                    Timestamp(timestamp["time"], timestamp["type"])
                )
            else:
                self.opponent_timeline.append(
                    Timestamp(timestamp["time"], timestamp["type"])
                )
        if self.result == "completion":
            if self.winner == UUID:
                self.user_timeline.append(
                    Timestamp(json_match["result"]["time"], "end")
                )
            else:
                self.opponent_timeline.append(
                    Timestamp(json_match["result"]["time"], "end")
                )

    def user_started_split(self, split):
        return any(timestamp.type == split for timestamp in self.user_timeline)

    def opponent_started_split(self, split):
        return any(timestamp.type == split for timestamp in self.opponent_timeline)

    def user_split_time(self, start_split, end_split):
        return self.split_time(start_split, end_split, self.user_timeline)

    def opponent_split_time(self, start_split, end_split):
        return self.split_time(start_split, end_split, self.opponent_timeline)

    def split_time(self, start_split, end_split, timeline):
        start_time = -1
        end_time = -1
        for timestamp in timeline:
            if timestamp.type == start_split and start_time == -1:
                start_time = timestamp.time
            elif timestamp.type == end_split:
                end_time = timestamp.time
                break
        if start_time == -1 or end_time == -1:
            return -1
        return end_time - start_time

    def died_or_reset(self, start_split, end_split, timeline):
        start_time = -1
        death_time = -1
        for timestamp in timeline:
            if timestamp.type == start_split and start_time == -1:
                start_time = timestamp.time
            elif (
                timestamp.type == "projectelo.timeline.death"
                or timestamp.type == "projectelo.timeline.reset"
            ) and start_time != -1:
                death_time = timestamp.time
            elif timestamp.type == end_split:
                return start_time != -1 and death_time != -1 and start_time < death_time
        if start_time != -1 and death_time != -1 and start_time < death_time:
            return True
        return False

    def __str__(self):
        result = "Match Timelines:\n"
        result += f"Result: {self.result}"
        if self.winner:
            result += f" (Winner: {self.winner})\n"
        else:
            result += "\n"
        result += f"Overworld: {self.overworld_type}, Bastion: {self.bastion_type}\n\n"

        result += "User Timeline:\n"
        for timestamp in self.user_timeline:
            result += f"  {format_time(timestamp.time)} - {timestamp.type}\n"

        result += "\nOpponent Timeline:\n"
        for timestamp in self.opponent_timeline:
            result += f"  {format_time(timestamp.time)} - {timestamp.type}\n"

        return result


matches: list[Match] = []
for json_match in json_matches:
    matches.append(Match(json_match))

MAJOR_SPLITS = [
    {
        "name": "MCSR Ranked",
        "start_split": "start",
        "end_split": "end",
    },
    {
        "name": "Overworld",
        "start_split": "start",
        "end_split": "story.enter_the_nether",
    },
    {
        "name": "Shipwreck",
        "start_split": "start",
        "end_split": "story.enter_the_nether",
        "overworld_filter": "SHIPWRECK",
    },
    {
        "name": "Buried Treasure",
        "start_split": "start",
        "end_split": "story.enter_the_nether",
        "overworld_filter": "BURIED_TREASURE",
    },
    {
        "name": "Village",
        "start_split": "start",
        "end_split": "story.enter_the_nether",
        "overworld_filter": "VILLAGE",
    },
    {
        "name": "Ruined Portal",
        "start_split": "start",
        "end_split": "story.enter_the_nether",
        "overworld_filter": "RUINED_PORTAL",
    },
    {
        "name": "Desert Temple",
        "start_split": "start",
        "end_split": "story.enter_the_nether",
        "overworld_filter": "DESERT_TEMPLE",
    },
    {
        "name": "Nether",
        "start_split": "story.enter_the_nether",
        "end_split": "nether.find_bastion",
    },
    {
        "name": "Bastion",
        "start_split": "nether.find_bastion",
        "end_split": "nether.find_fortress",
    },
    {
        "name": "Housing",
        "start_split": "nether.find_bastion",
        "end_split": "nether.find_fortress",
        "bastion_filter": "HOUSING",
    },
    {
        "name": "Bridge",
        "start_split": "nether.find_bastion",
        "end_split": "nether.find_fortress",
        "bastion_filter": "BRIDGE",
    },
    {
        "name": "Stables",
        "start_split": "nether.find_bastion",
        "end_split": "nether.find_fortress",
        "bastion_filter": "STABLES",
    },
    {
        "name": "Treasure",
        "start_split": "nether.find_bastion",
        "end_split": "nether.find_fortress",
        "bastion_filter": "TREASURE",
    },
    {
        "name": "Fortress",
        "start_split": "nether.find_fortress",
        "end_split": "projectelo.timeline.blind_travel",
    },
    {
        "name": "Blind",
        "start_split": "projectelo.timeline.blind_travel",
        "end_split": "story.follow_ender_eye",
    },
    {
        "name": "Fortress + Blind",
        "start_split": "nether.find_fortress",
        "end_split": "story.follow_ender_eye",
    },
    {
        "name": "Stronghold",
        "start_split": "story.follow_ender_eye",
        "end_split": "story.enter_the_end",
    },
    {
        "name": "End",
        "start_split": "story.enter_the_end",
        "end_split": "end",
    },
]


class StatsUI(tk.Tk):
    def __init__(self, matches, major_splits):
        super().__init__()
        self.title("MCSR Match Stats")
        self.geometry("1000x800")
        self.matches = matches
        self.major_splits = major_splits

        self.split_names = [split["name"] for split in self.major_splits]
        self.selected_split = tk.StringVar(value=self.split_names[0])

        self.create_widgets()
        self.update_stats()

    def create_widgets(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        ttk.Label(top_frame, text="Select Split:").pack(side=tk.LEFT)
        self.split_combo = ttk.Combobox(
            top_frame,
            values=self.split_names,
            textvariable=self.selected_split,
            state="readonly",
        )
        self.split_combo.pack(side=tk.LEFT, padx=5)
        self.split_combo.bind("<<ComboboxSelected>>", lambda e: self.update_stats())

        self.stats_text = tk.Text(self, wrap=tk.WORD, font=("Consolas", 14))
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.stats_text.config(state=tk.DISABLED)

    def update_stats(self):
        split_name = self.selected_split.get()
        split = next(s for s in self.major_splits if s["name"] == split_name)
        start_split = split["start_split"]
        end_split = split["end_split"]

        filtered_matches = self.matches
        if "overworld_filter" in split:
            filtered_matches = [
                match
                for match in filtered_matches
                if match.overworld_type == split["overworld_filter"]
            ]
        if "bastion_filter" in split:
            filtered_matches = [
                match
                for match in filtered_matches
                if match.bastion_type == split["bastion_filter"]
            ]

        stats_lines = []
        stats_lines.append(f"{split_name} Stats:\n")

        num_starts = len(
            [m for m in filtered_matches if m.user_started_split(start_split)]
        )
        stats_lines.append(f"Number of {split_name} Starts: {num_starts}")

        num_user_forfeits = len(
            [
                m
                for m in filtered_matches
                if m.user_started_split(start_split)
                and m.user_split_time(start_split, end_split) == -1
                and m.result == "forfeit"
                and m.winner != UUID
            ]
        )
        stats_lines.append(
            f"Number of User Forfeits: {num_user_forfeits} ({(num_user_forfeits / num_starts * 100) if num_starts else 0:.1f}% Forfeit Rate)"
        )

        num_deaths = len(
            [
                m
                for m in filtered_matches
                if m.user_started_split(start_split)
                and m.died_or_reset(start_split, end_split, m.user_timeline)
            ]
        )
        stats_lines.append(
            f"Number of Deaths/Resets: {num_deaths} ({(num_deaths / num_starts * 100) if num_starts else 0:.1f}% Death Rate)"
        )
        stats_lines.append("\n")

        num_opponent_wins = len(
            [
                m
                for m in filtered_matches
                if m.user_started_split(start_split)
                and m.user_split_time(start_split, end_split) == -1
                and m.result == "completion"
                and m.winner != UUID
            ]
        )
        stats_lines.append(f"Number of Opponent Wins: {num_opponent_wins}")

        num_opponent_forfeits = len(
            [
                m
                for m in filtered_matches
                if m.user_started_split(start_split)
                and m.user_split_time(start_split, end_split) == -1
                and m.result == "forfeit"
                and m.winner == UUID
            ]
        )
        stats_lines.append(f"Number of Opponent Forfeits: {num_opponent_forfeits}")

        num_draws = len(
            [
                m
                for m in filtered_matches
                if m.user_started_split(start_split)
                and m.user_split_time(start_split, end_split) == -1
                and m.result == "draw"
            ]
        )
        stats_lines.append(f"Number of Draws: {num_draws}")
        stats_lines.append("\n")

        fastest_time = min(
            [
                m.user_split_time(start_split, end_split)
                for m in filtered_matches
                if m.user_split_time(start_split, end_split) != -1
            ],
            default=None,
        )
        if fastest_time is not None:
            stats_lines.append(
                f"Fastest {split_name} Completion Time: {format_time(fastest_time)}"
            )
        stats_lines.append("\n")

        completed = len(
            [
                m
                for m in filtered_matches
                if m.user_split_time(start_split, end_split) != -1
            ]
        )
        if completed > 0:
            average_completion_time = np.mean(
                [
                    m.user_split_time(start_split, end_split)
                    for m in filtered_matches
                    if m.user_split_time(start_split, end_split) != -1
                ]
            )
            stats_lines.append(
                f"Average {split_name} Completion Time: ({format_time(average_completion_time)})"
            )
            stats_lines.append(f"Completed: {completed}")
            stats_lines.append("\n")

        completed_no_deaths = len(
            [
                m
                for m in filtered_matches
                if m.user_split_time(start_split, end_split) != -1
                and not m.died_or_reset(start_split, end_split, m.user_timeline)
            ]
        )
        if completed_no_deaths > 0 and completed_no_deaths != completed:
            average_completion_time_no_deaths = np.mean(
                [
                    m.user_split_time(start_split, end_split)
                    for m in filtered_matches
                    if m.user_split_time(start_split, end_split) != -1
                    and not m.died_or_reset(start_split, end_split, m.user_timeline)
                ]
            )
            stats_lines.append(
                f"Average Completion Time (No Deaths): ({format_time(average_completion_time_no_deaths)})"
            )
            stats_lines.append(f"Completed (No Deaths): {completed_no_deaths}")
            stats_lines.append("\n")

        completed_deaths = len(
            [
                m
                for m in filtered_matches
                if m.user_split_time(start_split, end_split) != -1
                and m.died_or_reset(start_split, end_split, m.user_timeline)
            ]
        )
        if completed_deaths > 0 and completed_deaths != completed:
            average_completion_time_deaths = np.mean(
                [
                    m.user_split_time(start_split, end_split)
                    for m in filtered_matches
                    if m.user_split_time(start_split, end_split) != -1
                    and m.died_or_reset(start_split, end_split, m.user_timeline)
                ]
            )
            stats_lines.append(
                f"Average {split_name} Completion Time (With Deaths): ({format_time(average_completion_time_deaths)})"
            )
            stats_lines.append(
                f"Completed {split_name} (With Deaths): {completed_deaths}"
            )
            stats_lines.append("\n")

        completed_both = len(
            [
                m
                for m in filtered_matches
                if m.user_split_time(start_split, end_split) != -1
                and m.opponent_split_time(start_split, end_split) != -1
            ]
        )
        stats_lines.append(
            f"Number of Completed Splits (User & Opponent): {completed_both}"
        )

        if completed_both > 0:
            user_wins = len(
                [
                    m
                    for m in filtered_matches
                    if m.user_split_time(start_split, end_split) != -1
                    and m.opponent_split_time(start_split, end_split) != -1
                    and m.user_split_time(start_split, end_split)
                    < m.opponent_split_time(start_split, end_split)
                ]
            )
            winrate = user_wins / completed_both * 100
            stats_lines.append(
                f"User Winrate: {user_wins}/{completed_both} ({winrate:.1f}%)"
            )
            avg_diff = np.mean(
                [
                    m.user_split_time(start_split, end_split)
                    - m.opponent_split_time(start_split, end_split)
                    for m in filtered_matches
                    if m.user_split_time(start_split, end_split) != -1
                    and m.opponent_split_time(start_split, end_split) != -1
                ]
            )
            status = "Ahead" if avg_diff < 0 else "Behind"
            stats_lines.append(
                f"Average Difference: {format_time(abs(avg_diff))} {status}"
            )

        stats_lines.append("\n")

        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert(tk.END, "\n".join(stats_lines))
        self.stats_text.config(state=tk.DISABLED)


# Launch the UI
if __name__ == "__main__":
    app = StatsUI(matches, MAJOR_SPLITS)
    app.mainloop()
