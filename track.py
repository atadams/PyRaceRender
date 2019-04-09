import json

trackName = 'cota'


def camel_case(st):
    output = ''.join(x if x.isalnum() else "_" for x in st.title())
    return output[0].lower() + output[1:]


def is_turn(this_section):
    return this_section['type'] == 'turn'


with open(f'{trackName}.json', 'r') as f:
    trackDict = json.load(f)


trackTurns = list(filter(is_turn, trackDict['sections']))

backgroundScript = f'SlowColor = ColorA;\nFastColor = ColorB;\nTextColor = ColorC;\nLineSize = 1;\nLapSize = 24;\nLapBottomOffset = LapSize;\nLineTopY = SizeY - (2 * LapSize) - 10;\n\nCurrentTurn = 0;\nCurrentTurnString = "";\nDisplayString = "";\nDisplayTurnString = "";\nDisplayPrevBest = 0;\nDisplayBest = 0;\nCreateDisplayString = 0;\nDiffString = "";\n\n'\

foregroundScript = 'CurrentSpeed = Round(GetDataValue(DFT_Speed), 1);\n\n'

for i, section in enumerate(trackDict['sections'], start=1):
    camelName = camel_case(section['name'])
    section.update({"i": i, "camelName": camelName})

    if section['type'] == 'turn':
        section.update({"sectionMinMax": "min", "sectionMinMaxValue": 999})
    else:
        section.update({"sectionMinMax": "max", "sectionMinMaxValue": 0})

    backgroundScript += f'{camelName}Best = 0;\n'

    foregroundScript += 'if(DataValue > {start} && DataValue <= {end}) {{\n\tif(CurrentTurnString != "{name}") {{\n\t\tCurrentMinMaxSpeed = {sectionMinMaxValue};\n\t}}\n\tCurrentTurnString = "{name}";\n\tCurrentMinMaxSpeed = {sectionMinMax}(CurrentSpeed, CurrentMinMaxSpeed);\n}} else if(CreateDisplayString == 0 && CurrentTurnString == "{name}") {{\n\tCreateDisplayString = 1;\n\tDisplayPrevBest = {camelName}Best;\n\n\tif(CurrentMinMaxSpeed >= {camelName}Best) {{\n\t\t{camelName}Best = CurrentMinMaxSpeed;\n\t}}\n\tDisplayTurnString = CurrentTurnString;\n\tDisplayCurrent = CurrentMinMaxSpeed;\n}}\n\n'.format(
        **section)



foregroundScript += f'\n\nif(CreateDisplayString == 1) {{\n\tDiffString = "";\n\tBackgroundColor = SlowColor;\n\n\tif(DisplayPrevBest > 0) {{\n\t\tDiff = DisplayCurrent - DisplayPrevBest;\n\t\tif(abs(Diff) >= 0.1) {{\n\t\t\tDiffString = FormatNumber(Diff, 1) + " MPH";\n\t\t}}\n\t}}\n\n\tif(DiffString != "" && Diff >= 0) {{\n\t\tDiffString = "+" + DiffString;\n\t\tBackgroundColor = FastColor;\n\t}}\n\n\tDisplayString = DisplayTurnString + ": " + FormatNumber(DisplayCurrent, 1) + " MPH  ";\n\tCreateDisplayString = 0;\n}}\n\n\nif(DisplayString != "") {{\n\tDrawRect(0, 0, SizeX, SizeY, BackgroundColor, Filled);\n\tDrawText(DisplayString, 30, 0, TextColor, 48, AlignH_Left);\n\tif(DiffString != "") {{\n\t\tDrawText(DiffString, SizeX - 10, 48, TextColor, 30, AlignH_Right);\n\t}}\n}}'


f = open(f'{trackName}_min-turn-speeds_background.txt', 'wt', encoding='utf-8')
f.write(backgroundScript)

f = open(f'{trackName}_min-turn-speeds_foreground.txt', 'wt', encoding='utf-8')
f.write(foregroundScript)


# Turn markers

numTurnsDisplayed = 10

backgroundScript = f'Pad = 1;\nSpaceX = SizeX - (Pad * 2);\n\n\nLapColor = ColorA;\nLineColor = ColorB;\nLineSize = 2;\nLapSize = 32;\nLapBottomOffset = LapSize;\nLapY = SizeY - Pad - LapBottomOffset;\nTimeSpan = 45;\nLineTopY = SizeY - (2 * LapSize) - 10;\n\nDisplayWidth = SpaceX;\nTimeScale = DisplayWidth / TimeSpan;\n\nCurrentTurn = 0;\n\n\n'

for i in range(1, numTurnsDisplayed + 1):
    backgroundScript += f'DisplayTurn{i} = 0;\nDisplayTurnTime{i} = 0;\n\n'


foregroundScript = f'MinTime = SampleTime - TimeSpan;\n\nAlign = AlignH_Center;\nSetTextOutline(Transparent);\n\n'

for i, turn in enumerate(trackTurns, 1):
    foregroundScript += f"if(DataValue >= {turn['start']} && DataValue <= {turn['end']} && CurrentTurn != {i}) {{ CurrentTurn = {i}; }}\n"

foregroundScript += f'\n\nif(CurrentTurn > 0 && CurrentTurn != DisplayTurn1 && SampleTime - DisplayTurnTime1 > 1) {{\n'

for i in reversed(range(2, numTurnsDisplayed + 1)):
    prevTurn = i - 1
    foregroundScript += f'\tDisplayTurn{i} = DisplayTurn{prevTurn};\n\tDisplayTurnTime{i} = DisplayTurnTime{prevTurn};\n\n'

foregroundScript += f'\tDisplayTurn1 = CurrentTurn;\n\tDisplayTurnTime1 = SampleTime;\n}}\n\n\n'

for i in range(1, numTurnsDisplayed + 1):
    foregroundScript += f'if(DisplayTurnTime{i} > MinTime) {{\n\tX = DisplayWidth - ((SampleTime - DisplayTurnTime{i}) * TimeScale);\n\tDrawText(FormatNumber(DisplayTurn{i}, 0), X, LapY, LapColor, LapSize, Align);\n\tDrawLineFlat(X, LineTopY, X, 0, LineColor, 1);\n}}\n\n'


f = open(f'{trackName}_turn-num-graph_background.txt', 'wt', encoding='utf-8')
f.write(backgroundScript)

f = open(f'{trackName}_turn-num-graph_foreground.txt', 'wt', encoding='utf-8')
f.write(foregroundScript)


# Sector times

numOfSectors = len(trackDict['sectors'])

backgroundScript = f'LapNumColor = ColorA;\nCurLapTimeColor = ColorB;\nLapTimeColor = ColorC;\nBestLapTimeColor = ColorD;\nBackColor = ColorE;\nTrimColor = ColorF;\n\nDigits = 2;\nCompact = 1;\n\nFontSize = 48;\n\nOffsetX = 6;\nOffsetY = 6;\n\nTopY = SizeY - OffsetY;\nGapX = 85;\nGapY = 5;\n\nCurrentSector = 0;\n\n\n'

foregroundScript = f'X = OffsetX + 16;\nY = SizeY;\n\nLapTime = GetCurLapTime();\n\nY -= FontSize + GapY;\n\n\n'

for i in range(1, numOfSectors + 1):
    backgroundScript += f'Sector{i}Current = 0;\nSector{i}Best = 9999999;\n\n'

    foregroundScript += f'DrawText("S{i}", 20, Y, LapNumColor, FontSize, AlignH_Left);\nY -= FontSize + GapY;\n\n'

for i in range(2, numOfSectors + 1):
    backgroundScript += f'Sector{i}Current = 0;\nSector{i}Diff = 0;\n\n'

sector1End = trackDict['sectors'][0]['end']

foregroundScript += f'Y = SizeY;\n\nif(CurrentSector == 0 && DataValue < {sector1End}) {{\n\tCurrentSector = 1;\n}}\n\n\nif(CurrentSector != 0) {{\n'

for i, sector in enumerate(trackDict['sectors']):
    sectorNumber = i + 1

    if i + 1 < numOfSectors:
        nextSector = i + 2
        sectorEnd = '> {}'.format(sector['end'])
        laptimeStr = 'LapTime'
    else:
        nextSector = 1
        sectorEnd = '< {}'.format(trackDict['sectors'][0]['end'])
        laptimeStr = 'GetLapTime(GetCurLapNum() - 1)'

    foregroundScript += f'\tif(DataValue {sectorEnd} && CurrentSector == {sectorNumber}) {{\n\t\tSector{sectorNumber}Current = {laptimeStr}'

    if sectorNumber != 1:
        for h in range(1, sectorNumber):
            foregroundScript += f' - Sector{h}Current'

    foregroundScript += f';\n\t\tif(Sector{sectorNumber}Best < 999) {{\n\t\t\tSector{sectorNumber}Diff = Sector{sectorNumber}Current - Sector{sectorNumber}Best;\n\t\t}}\n\t\tSector{sectorNumber}Best = min(Sector{sectorNumber}Current, Sector{sectorNumber}Best);\n\t\tCurrentSector = {nextSector};\n'

    if sectorNumber == 1:
        for j in range(2, numOfSectors + 1):
            foregroundScript += f'\t\tSector{j}Current = 0;\n\t\tSector{j}Diff = 0;\n'

    foregroundScript += f'\n\t}}\n\n'


for i in range(1, numOfSectors + 1):
    foregroundScript += f'\tY -= FontSize + GapY;\n\tif(Sector{i}Current > 0) {{\n\t\tif(Sector{i}Current == Sector{i}Best) {{ LapColor = BestLapTimeColor; }} else {{ LapColor = CurLapTimeColor; }}\n\t\tDrawTime(Sector{i}Current, Digits, X + GapX, Y, LapColor, FontSize, 0, Compact);\n\n\t\tDiffText = "-";\n\t\tif(Sector{i}Diff > 0) {{ \n\t\t\tDiffText = "+" + FormatNumber(Sector{i}Diff, 2); \n\t\t}} \n\t\tif(Sector{i}Diff < 0) {{\n\t\t\tDiffText = "- " + FormatNumber(abs(Sector{i}Diff), 2); \n\t\t}} \n\n\t\tDrawText(DiffText, SizeX - GapX, Y, LapTimeColor, FontSize, AlignH_Right);\n\n\t}}\n\n'

foregroundScript += '}\n'

f = open(f'{trackName}_sector-times_background.txt', 'wt', encoding='utf-8')
f.write(backgroundScript)

f = open(f'{trackName}_sector-times_foreground.txt', 'wt', encoding='utf-8')
f.write(foregroundScript)
