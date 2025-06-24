import os
import json
from datetime import datetime

now = datetime.now()
month = now.month
day = now.day
year = now.year

path = f"matches/{month}_{day}_{year}"
files = os.listdir(path)
UUID = "34c876e4a23a4fe5a1fbf76a41db0e78"
matches = []
for item in files:
    newPath = os.path.join(path, item)
    with open(newPath, "r") as f:
        dict = json.load(f)
        matches.append(dict)


originalNumber = len(matches)
numReset = 0
numFortFirst = 0
for i in range(len(matches) - 1, -1, -1):
    hasReset = False
    bastionTime = -1
    fortressTime = -1
    bastionTimeOpponent = -1
    fortressTimeOpponent = -1
    for timestamp in matches[i]["timelines"]:
        if timestamp["type"] == "projectelo.timeline.reset":
            hasReset = True
        if timestamp["uuid"] == UUID:
            if timestamp["type"] == "nether.find_bastion":
                bastionTime = timestamp["time"]
            if timestamp["type"] == "nether.find_fortress":
                fortressTime = timestamp["time"]
        else:
            if timestamp["type"] == "nether.find_bastion":
                bastionTimeOpponent = timestamp["time"]
            if timestamp["type"] == "nether.find_fortress":
                fortressTimeOpponent = timestamp["time"]
    if hasReset:
        matches.pop(i)
        numReset += 1
    elif (fortressTime != -1 and bastionTime != -1 and fortressTime < bastionTime) or (
        fortressTimeOpponent != -1
        and bastionTimeOpponent != -1
        and fortressTimeOpponent < bastionTimeOpponent
    ):
        matches.pop(i)
        numFortFirst += 1

print(
    f"{numReset} matches have a reset and {numFortFirst} matches are fortress first. Only {len(matches)} will be considered for analysis."
)


def formatTime(milliseconds):
    return f"{"-" if milliseconds < 0 else ""}{int(abs(milliseconds) / 1000 // 60)}:{round(abs(milliseconds) / 1000 % 60):02d}"


def splitTime(split, match, opponent=False):
    if split == "":
        return 0
    for timestamp in match["timelines"]:
        if (timestamp["uuid"] == UUID) != opponent and timestamp["type"] == split:
            return timestamp["time"]
    return -1


def splitCompletionTime(
    prevSplit, nextSplit, match, opponent=False, excludeDeaths=True
):
    prevTime = -1
    nextTime = -1
    deaths = []
    if prevSplit == "":
        prevTime = 0
    if (
        nextSplit == ""
        and not match["forfeited"]
        and match["result"]["uuid"] != None
        and (match["result"]["uuid"] == UUID) != opponent
    ):
        nextTime = match["result"]["time"]
    for timestamp in match["timelines"]:
        if (timestamp["uuid"] == UUID) != opponent:
            if timestamp["type"] == prevSplit:
                prevTime = timestamp["time"]
            elif timestamp["type"] == nextSplit:
                nextTime = timestamp["time"]
            elif timestamp["type"] == "projectelo.timeline.death":
                deaths.append(timestamp["time"])
    if prevTime == -1 or nextTime == -1:
        return -1
    if excludeDeaths:
        for death in deaths:
            if death >= prevTime and death <= nextTime:
                return -1
    return nextTime - prevTime


def died(prevSplit, nextSplit, match):
    prevTime = -1
    nextTime = -1
    deaths = []
    if prevSplit == "":
        prevTime = 0
    if (
        nextSplit == ""
        and not match["forfeited"]
        and match["result"]["uuid"] != None
        and match["result"]["uuid"] == UUID
    ):
        nextTime = match["result"]["time"]
    for timestamp in match["timelines"]:
        if timestamp["uuid"] == UUID:
            if timestamp["type"] == prevSplit:
                prevTime = timestamp["time"]
            elif timestamp["type"] == nextSplit:
                nextTime = timestamp["time"]
            elif timestamp["type"] == "projectelo.timeline.death":
                deaths.append(timestamp["time"])
    if prevTime == -1:
        return False
    for death in deaths:
        if death > prevTime and (death < nextTime or nextTime == -1):
            return True
    return False


def opponentWonDuringSplit(prevSplit, nextSplit, match):
    nextTime = -1
    prevTime = -1
    for timestamp in match["timelines"]:
        if timestamp["uuid"] == UUID:
            if timestamp["type"] == prevSplit:
                prevTime = timestamp["time"]
            if timestamp["type"] == nextSplit:
                nextTime = timestamp["time"]
    return (
        nextTime == -1
        and prevTime != -1
        and match["result"]["uuid"] != None
        and match["result"]["uuid"] != UUID
        and not match["forfeited"]
    )


def forfeitedDuringSplit(prevSplit, nextSplit, match, opponent):
    nextTime = -1
    prevTime = -1
    if prevSplit == "":
        prevTime = 0
    for timestamp in match["timelines"]:
        if timestamp["uuid"] == UUID:
            if timestamp["type"] == prevSplit:
                prevTime = timestamp["time"]
            if timestamp["type"] == nextSplit:
                nextTime = timestamp["time"]
    return (
        nextTime == -1
        and prevTime != -1
        and match["forfeited"]
        and match["result"]["uuid"] != None
        and (match["result"]["uuid"] == UUID) != opponent
    )


def drewDuringSplit(prevSplit, nextSplit, match):
    nextTime = -1
    prevTime = -1
    if prevSplit == "":
        prevTime = 0
    for timestamp in match["timelines"]:
        if timestamp["uuid"] == UUID:
            if timestamp["type"] == prevSplit:
                prevTime = timestamp["time"]
            if timestamp["type"] == nextSplit:
                nextTime = timestamp["time"]
    return nextTime == -1 and prevTime != -1 and match["result"]["uuid"] == None


def numSplits(split, opponent=False):
    num = 0
    for match in matches:
        if splitTime(split, match, opponent) >= 0:
            num += 1
    return num


def numCompletedSplits(prevSplit, nextSplit, opponent=False, excludeDeaths=True):
    num = 0
    for match in matches:
        newTime = splitCompletionTime(
            prevSplit, nextSplit, match, opponent=opponent, excludeDeaths=excludeDeaths
        )
        if newTime >= 0:
            num += 1
    return num


def averageSplitTime(prevSplit, nextSplit, opponent=False, excludeDeaths=True):
    time = 0

    for match in matches:
        newTime = splitCompletionTime(
            prevSplit, nextSplit, match, opponent=opponent, excludeDeaths=excludeDeaths
        )
        if newTime >= 0:
            time += newTime
    num = numCompletedSplits(
        prevSplit, nextSplit, opponent=opponent, excludeDeaths=excludeDeaths
    )
    if num == 0:
        return 0
    else:
        return time / num


def numSplitsBoth(prevSplit, nextSplit):
    num = 0
    for match in matches:
        yourTime = splitCompletionTime(prevSplit, nextSplit, match, opponent=False)
        opponentTime = splitCompletionTime(prevSplit, nextSplit, match, opponent=True)
        if yourTime >= 0 and opponentTime >= 0:
            num += 1
    return num


def numBeaten(prevSplit, nextSplit):
    num = 0
    for match in matches:
        yourTime = splitCompletionTime(prevSplit, nextSplit, match, opponent=False)
        opponentTime = splitCompletionTime(prevSplit, nextSplit, match, opponent=True)
        if yourTime >= 0 and opponentTime >= 0 and yourTime < opponentTime:
            num += 1
    return num


def averageDifference(prevSplit, nextSplit):
    time = 0
    for match in matches:
        yourTime = splitCompletionTime(prevSplit, nextSplit, match, opponent=False)
        opponentTime = splitCompletionTime(prevSplit, nextSplit, match, opponent=True)
        if yourTime >= 0 and opponentTime >= 0:
            time += yourTime - opponentTime
    num = numSplitsBoth(prevSplit, nextSplit)

    return 0 if num == 0 else time / numSplitsBoth(prevSplit, nextSplit)


def numDeaths(prevSplit, nextSplit):
    num = 0
    for match in matches:
        newDied = died(prevSplit, nextSplit, match)
        if newDied:
            num += 1
    return num


def numOpponentWonDuringSplit(prevSplit, nextSplit):
    num = 0
    for match in matches:
        if opponentWonDuringSplit(prevSplit, nextSplit, match):
            num += 1
    return num


def numForfeitedDuringSplit(prevSplit, nextSplit, opponent):
    num = 0
    for match in matches:
        if forfeitedDuringSplit(prevSplit, nextSplit, match, opponent):
            num += 1
    return num


def numDraws(prevSplit, nextSplit):
    num = 0
    for match in matches:
        if drewDuringSplit(prevSplit, nextSplit, match):
            num += 1
    return num


def numDeathRecoveries(prevSplit, nextSplit):
    num = 0
    for match in matches:
        if splitCompletionTime(
            prevSplit, nextSplit, match, opponent=False, excludeDeaths=False
        ) >= 0 and died(prevSplit, nextSplit, match):
            num += 1
    return num


majorSplits = [
    {
        "name": "Overworld",
        "prevSplit": "",
        "nextSplit": "story.enter_the_nether",
    },
    {
        "name": "Shipwreck",
        "prevSplit": "",
        "nextSplit": "story.enter_the_nether",
        "overworldFilter": "SHIPWRECK",
    },
    {
        "name": "Buried Treasure",
        "prevSplit": "",
        "nextSplit": "story.enter_the_nether",
        "overworldFilter": "BURIED_TREASURE",
    },
    {
        "name": "Village",
        "prevSplit": "",
        "nextSplit": "story.enter_the_nether",
        "overworldFilter": "VILLAGE",
    },
    {
        "name": "Ruined Portal",
        "prevSplit": "",
        "nextSplit": "story.enter_the_nether",
        "overworldFilter": "RUINED_PORTAL",
    },
    {
        "name": "Desert Temple",
        "prevSplit": "",
        "nextSplit": "story.enter_the_nether",
        "overworldFilter": "DESERT_TEMPLE",
    },
    {
        "name": "Nether",
        "prevSplit": "story.enter_the_nether",
        "nextSplit": "nether.find_bastion",
    },
    {
        "name": "Bastion",
        "prevSplit": "nether.find_bastion",
        "nextSplit": "nether.find_fortress",
    },
    {
        "name": "Housing",
        "prevSplit": "nether.find_bastion",
        "nextSplit": "nether.find_fortress",
        "bastionFilter": "HOUSING",
    },
    {
        "name": "Bridge",
        "prevSplit": "nether.find_bastion",
        "nextSplit": "nether.find_fortress",
        "bastionFilter": "BRIDGE",
    },
    {
        "name": "Stables",
        "prevSplit": "nether.find_bastion",
        "nextSplit": "nether.find_fortress",
        "bastionFilter": "STABLES",
    },
    {
        "name": "Treasure",
        "prevSplit": "nether.find_bastion",
        "nextSplit": "nether.find_fortress",
        "bastionFilter": "TREASURE",
    },
    {
        "name": "Fortress",
        "prevSplit": "nether.find_fortress",
        "nextSplit": "projectelo.timeline.blind_travel",
    },
    {
        "name": "Blind",
        "prevSplit": "projectelo.timeline.blind_travel",
        "nextSplit": "story.follow_ender_eye",
    },
    {
        "name": "Fortress + Blind",
        "prevSplit": "nether.find_fortress",
        "nextSplit": "story.follow_ender_eye",
    },
    {
        "name": "Stronghold",
        "prevSplit": "story.follow_ender_eye",
        "nextSplit": "story.enter_the_end",
    },
    {
        "name": "End",
        "prevSplit": "story.enter_the_end",
        "nextSplit": "",
    },
]


print(f"{numCompletedSplits("", "", opponent=False, excludeDeaths=False)} Completions")
print(
    f"Average Completion Time: {formatTime(averageSplitTime("", "", opponent=False,excludeDeaths=False))}"
)
print(f"{numCompletedSplits("", "")} Completions Without Deaths")
print(f"Average Completion Time Without Deaths: {formatTime(averageSplitTime("", ""))}")
print()

originalMatches = matches


for majorSplit in majorSplits:
    name = majorSplit["name"]
    prevSplit = majorSplit["prevSplit"]
    nextSplit = majorSplit["nextSplit"]
    matches = originalMatches[:]
    for i in range(len(matches) - 1, -1, -1):
        if (
            "overworldFilter" in majorSplit
            and majorSplit["overworldFilter"] != matches[i]["seedType"]
        ):
            matches.pop(i)
        if (
            "bastionFilter" in majorSplit
            and majorSplit["bastionFilter"] != matches[i]["bastionType"]
        ):
            matches.pop(i)
    print(f"{name} Stats:")
    print()
    print(
        f"Average {name} Completion Time (Excluding Deaths): {formatTime(averageSplitTime(prevSplit, nextSplit))}"
    )
    print()
    print(f"Number of {name} Starts: {numSplits(prevSplit)}")
    print(
        f"Number of {name} Completions: {numCompletedSplits(prevSplit, nextSplit, opponent=False, excludeDeaths=False)}"
    )

    print(
        f"You forfeited {numForfeitedDuringSplit(prevSplit, nextSplit, False)} times during this split."
    )
    print(
        f"Your opponent won {numOpponentWonDuringSplit(prevSplit, nextSplit)} times during this split."
    )
    print(
        f"Your opponent forfeited {numForfeitedDuringSplit(prevSplit, nextSplit, True)} times during this split."
    )
    print(f"You drew {numDraws(prevSplit, nextSplit)} times during this split.")
    print()
    if numSplits(prevSplit) == 0:
        print(f"Deaths: {numDeaths(prevSplit, nextSplit)} (0% Death Rate)")
    else:
        print(
            f"Deaths: {numDeaths(prevSplit, nextSplit)} ({(numDeaths(prevSplit, nextSplit) / numSplits(prevSplit) * 100):.1f}% Death Rate)"
        )
    print(
        f"You completed the split despite a death {numDeathRecoveries(prevSplit, nextSplit)} times."
    )
    print()
    if nextSplit != "":
        print(f"{numSplitsBoth(prevSplit, nextSplit)} Splits of Both Players")
        if numSplitsBoth(prevSplit, nextSplit) == 0:
            print(
                f"{numBeaten(prevSplit, nextSplit)} Wins on {name} Split (0% Win Rate)"
            )
        else:
            print(
                f"{numBeaten(prevSplit, nextSplit)} Wins on {name} Split ({(numBeaten(prevSplit, nextSplit) / numSplitsBoth(prevSplit, nextSplit) * 100):.1f}% Win Rate)"
            )
        diff = averageDifference(prevSplit, nextSplit)
        if diff < 0:
            print(f"Average Difference: {formatTime(abs(diff))} Ahead")
        else:
            print(f"Average Difference: {formatTime(diff)} Behind")
        print()
    print()
