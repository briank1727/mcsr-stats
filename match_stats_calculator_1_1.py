import os
import json
from datetime import datetime
import numpy as np

now = datetime.now()
month = now.month
day = now.day
year = now.year

path = f"Matches_{month}_{day}_{year}"
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
        return f"{"-" if milliseconds < 0 else ""}{int(abs(milliseconds) / 1000 // 60)}:{round(abs(milliseconds) / 1000 % 60):02d}"
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
        start_time = 0
        end_time = -1
        for timestamp in timeline:
            if timestamp.type == start_split:
                start_time = timestamp.time
            elif timestamp.type == end_split:
                end_time = timestamp.time
                break
        if start_time == -1 or end_time == -1:
            return -1
        return end_time - start_time

    def died_or_reset(self, start_split, end_split, timeline):
        start_time = -1
        end_time = -1
        death_time = -1
        for timestamp in timeline:
            if timestamp.type == start_split:
                start_time = timestamp.time
            elif (
                timestamp.type == "projectelo.timeline.death"
                or timestamp.type == "projectelo.timeline.reset"
            ):
                death_time = timestamp.time
            elif timestamp.type == end_split:
                end_time = timestamp.time
                break
        if start_time == -1 or end_time == -1:
            return False
        if death_time != -1 and start_time < death_time < end_time:
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
        "overworldFilter": "SHIPWRECK",
    },
    {
        "name": "Buried Treasure",
        "start_split": "start",
        "end_split": "story.enter_the_nether",
        "overworldFilter": "BURIED_TREASURE",
    },
    {
        "name": "Village",
        "start_split": "start",
        "end_split": "story.enter_the_nether",
        "overworldFilter": "VILLAGE",
    },
    {
        "name": "Ruined Portal",
        "start_split": "start",
        "end_split": "story.enter_the_nether",
        "overworldFilter": "RUINED_PORTAL",
    },
    {
        "name": "Desert Temple",
        "start_split": "start",
        "end_split": "story.enter_the_nether",
        "overworldFilter": "DESERT_TEMPLE",
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
        "bastionFilter": "HOUSING",
    },
    {
        "name": "Bridge",
        "start_split": "nether.find_bastion",
        "end_split": "nether.find_fortress",
        "bastionFilter": "BRIDGE",
    },
    {
        "name": "Stables",
        "start_split": "nether.find_bastion",
        "end_split": "nether.find_fortress",
        "bastionFilter": "STABLES",
    },
    {
        "name": "Treasure",
        "start_split": "nether.find_bastion",
        "end_split": "nether.find_fortress",
        "bastionFilter": "TREASURE",
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
print()
for SPLIT in MAJOR_SPLITS[-1:]:
    name = SPLIT["name"]
    start_split = SPLIT["start_split"]
    end_split = SPLIT["end_split"]

    print(f"{name} Stats:")
    print()

    num_starts = len(
        [match for match in matches if match.user_started_split(start_split)]
    )

    print(f"Number of {name} Starts: {num_starts}")

    num_user_forfeits = len(
        [
            match
            for match in matches
            if match.user_started_split(start_split)
            and match.user_split_time(start_split, end_split) == -1
            and match.result == "forfeit"
            and match.winner != UUID
        ]
    )

    print(
        f"Number of User Forfeits: {num_user_forfeits} ({(num_user_forfeits / num_starts * 100):.1f}% Forfeit Rate)"
    )

    num_opponent_wins = len(
        [
            match
            for match in matches
            if match.user_started_split(start_split)
            and match.user_split_time(start_split, end_split) == -1
            and match.result == "completion"
            and match.winner != UUID
        ]
    )

    print(f"Number of Opponent Wins: {num_opponent_wins}")

    num_opponent_forfeits = len(
        [
            match
            for match in matches
            if match.user_started_split(start_split)
            and match.user_split_time(start_split, end_split) == -1
            and match.result == "forfeit"
            and match.winner == UUID
        ]
    )

    print(f"Number of Opponent Forfeits: {num_opponent_forfeits}")

    num_draws = len(
        [
            match
            for match in matches
            if match.user_started_split(start_split)
            and match.user_split_time(start_split, end_split) == -1
            and match.result == "draw"
        ]
    )
    print(f"Number of Draws: {num_draws}")

    print()

    completed_matches = len(
        [
            match
            for match in matches
            if match.user_split_time(start_split, end_split) != -1
        ]
    )
    if completed_matches > 0:
        average_completion_time = np.mean(
            [
                match.user_split_time(start_split, end_split)
                for match in matches
                if match.user_split_time(start_split, end_split) != -1
            ]
        )

        print(
            f"Average {name} Completion Time: ({format_time(average_completion_time)})"
        )

        print(f"Completed: {completed_matches}")

        print()

    completed_matches_no_deaths = len(
        [
            match
            for match in matches
            if match.user_split_time(start_split, end_split) != -1
            and not match.died_or_reset(start_split, end_split, match.user_timeline)
        ]
    )

    if completed_matches_no_deaths > 0:
        average_completion_time_no_deaths = np.mean(
            [
                match.user_split_time(start_split, end_split)
                for match in matches
                if match.user_split_time(start_split, end_split) != -1
                and not match.died_or_reset(start_split, end_split, match.user_timeline)
            ]
        )
        print(
            f"Average {name} Completion Time (No Deaths): ({format_time(average_completion_time_no_deaths)})"
        )
        print(f"Completed {name} (No Deaths): {completed_matches_no_deaths}")
        print()

    completed_matches_deaths = len(
        [
            match
            for match in matches
            if match.user_split_time(start_split, end_split) != -1
            and match.died_or_reset(start_split, end_split, match.user_timeline)
        ]
    )

    if completed_matches_deaths > 0:
        average_completion_time_deaths = np.mean(
            [
                match.user_split_time(start_split, end_split)
                for match in matches
                if match.user_split_time(start_split, end_split) != -1
                and match.died_or_reset(start_split, end_split, match.user_timeline)
            ]
        )
        print(
            f"Average {name} Completion Time (With Deaths): ({format_time(average_completion_time_deaths)})"
        )
        print(f"Completed {name} (With Deaths): {completed_matches_deaths}")
        print()
