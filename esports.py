import irsdk
import time
import csv
from string import digits
import math

class State:
    ir_connected = False
    last_car_setup_tick = -1

def check_iracing():
    if state.ir_connected and not (ir.is_initialized and ir.is_connected):
        state.ir_connected = False
        state.last_car_setup_tick = -1
        ir.shutdown()
        print('irsdk disconnected')
    elif not state.ir_connected and ir.startup() and ir.is_initialized and ir.is_connected:
        state.ir_connected = True
        print('irsdk connected')

def getGrid(drivers):
    idxs = []
    startingGrid = ir['SessionInfo']['Sessions'][ir['SessionNum']]['QualifyPositions']

    for x in startingGrid:
        idxs.append(x['CarIdx'])

    return formatCSV(idxs, drivers)

def getPositions(drivers):
    idxs = []
    positions = ir['SessionInfo']['Sessions'][ir['SessionNum']]['ResultsPositions']
    for x in positions:
        idxs.append(x['CarIdx'])

    return formatCSV(idxs, drivers)

#iRacing SDK doesn't pull corresponding state with city, so this method matches the state based on city output
#Note: if we're running a track that isn't on this list, it will need to be updated
def getLocationState(city):
    trackName = ir['WeekendInfo']['TrackDisplayName']
    states = {
        #Weedsport
        'Weedsport': 'NY',
        #Cedar Lake
        'New Richmond': 'WI',
        #Fairbury
        'Fairbury': 'IL',
        #Lernerville
        'Sarver': 'PA',
        #Chili Bowl
        'Tulsa': 'OK',
        #Kokomo
        'Kokomo': 'IN',
        #Eldora
        'Rossburg': 'OH',
        #Williams Grove
        'Mechanicsburg': 'PA',
        #Volusia
        'Barberville': 'FL',
        #Knoxville
        'Knoxville': 'IA',
        #Bristol Dirt
        'Bristol': 'TN',
        #Limaland
        'Lima': 'OH',
        #Lanier
        'Braselton': 'GA',
        #Charlotte Dirt
        'Concord': 'NC',
        #USA Int'l
        'Lakeland': 'FL',
        #Indy
        'Indianapolis': 'IN',
        'Leeds': 'AL'}
    return city + ', ' + states[city] + " | " + trackName

#Format all of our info into something pretty that vMix can use
def formatCSV(idxs, drivers):

    driverInfo = []
    csvFormat = []
    repl = str.maketrans(
        "áéúíó",
        "aeuio"
    )
    remove_digits = str.maketrans(
        '',
        '',
        digits
    )
    lastNameNoNos = ['Jr', 'Jr.', 'II', 'III']
    driverNames = []

    for x in idxs:
        driverDict = {}
        driverDict['Position'] = idxs.index(x)+1
        driverDict['CarNumber'] = drivers[x]['CarNumber'].replace('0', 'O')
        name = drivers[x]['UserName'].translate(repl).translate(remove_digits).split()
        if len(name) > 2:
            if len(name[0]) > 2:
                name[0] = name[0].capitalize()
            driverDict['FirstName'] = name[0]
            if any(name[len(name) - 1] in x for x in lastNameNoNos):
                driverDict['LastName'] = name[len(name) - 2] + " " + name[len(name) - 1]
            else:
                driverDict['LastName'] = name[len(name) - 1]
        else:
            if len(name[0]) > 2:
                name[0] = name[0].capitalize()
            driverDict['FirstName'] = name[0]
            driverDict['LastName'] = name[1]
        driverDict['Laps'] = ir['CarIdxLapCompleted'][x]
        driverDict['LastLapTime'] = ir['CarIdxLastLapTime'][x]
        driverDict['BestLap'] = ir['CarIdxBestLapNum'][x]
        driverDict['BestLapTime'] = ir['CarIdxBestLapTime'][x]
        driverDict['Nationality'] = driverDict['FirstName'] + " " + driverDict['LastName']
        driverInfo.append(driverDict)

        driverNames.append(str(driverDict['FirstName'] + " " + driverDict['LastName']))

    sublist = [ir['SessionLapsRemain']]

    #VMix csv needs to be five cars per row, so 46 is the number of cells we need per line
    for x in range(0, len(driverInfo)):
        sublist.extend(list(driverInfo[x].values()))
        if len(sublist) == 46:
            csvFormat.append(sublist)
            sublist = [ir['SessionLapsRemain']]

    csvFormat.append(sublist)

    for x in range(0, len(driverNames)):
        if x < len(csvFormat):
            if len(csvFormat[x]) != 46:
                missing = [''] * (46-len(csvFormat[x]))
                csvFormat[x].extend(missing)
                csvFormat[x].append(driverNames[x])
            else:
                csvFormat[x].append(driverNames[x])

            if x == 0:
                location = []
                sessionName = ir['SessionInfo']['Sessions'][ir['SessionNum']]['SessionName']
                airTemp = '%.2f'%((ir['AirTemp'] * 9/5) + 32)
                trackTemp = '%.2f'%((ir['TrackTemp'] * 9/5) + 32)
                windVel = '%.2f'%(ir['WindVel']*2.2369)
                val = math.floor((ir['WindDir'] / 45) + 0.5);
                directions = ['N', 'NE', 'E', 'SE',  'S', 'SW', 'W', 'NW']
                windDir = (directions[(val % 8)])
                humidity = '%.2f'%(ir['RelativeHumidity'])

                location.append(str(getLocationState(ir['WeekendInfo']['TrackCity'])))
                csvFormat[x].extend(location)
                csvFormat[x].append(sessionName)
                csvFormat[x].append(airTemp)
                csvFormat[x].append(trackTemp)
                csvFormat[x].append(windVel)
                csvFormat[x].append(windDir)
                csvFormat[x].append(humidity)

        else:
            missing = [''] * 46
            missing.append(driverNames[x])
            csvFormat.append(missing)

    return csvFormat

def writeCSV(list):
    fields = ['LapsToGo', 'Position1', 'Number1', 'FirstName1', 'LastName1', 'Laps1', 'LastLapTime1',
              'BestLap1', 'BestLapTime1', 'FullName1', 'Position2', 'Number2', 'FirstName2', 'LastName2', 'Laps2',
              'LastLapTime2', 'BestLap2', 'BestLapTime2', 'FullName2', 'Position3', 'Number3', 'FirstName3',
              'LastName3',
              'Laps3', 'LastLapTime3', 'BestLap3', 'BestLapTime3', 'FullName3', 'Position4', 'Number4', 'FirstName4',
              'LastName4', 'Laps4', 'LastLapTime4', 'BestLap4', 'BestLapTime4', 'FullName4', 'Position5', 'Number5',
              'FirstName5', 'LastName5', 'Laps5', 'LastLapTime5', 'BestLap5', 'BestLapTime5', 'FullName5', 'FullName',
              'Track', 'CurrentSession', 'AirTemp', 'TrackTemp', 'WindSpeed', 'WindDirection', 'Humidity']
    filename = 'iracing_timing.csv'

    with open(filename, 'w', newline="") as csvFile:
        csvWriter = csv.writer(csvFile)
        csvWriter.writerow(fields)
        csvWriter.writerows(list)

if __name__ == '__main__':
    ir = irsdk.IRSDK()
    state = State()

    try:
        while True:
            check_iracing()

            if state.ir_connected:
                sessionType = ir['SessionInfo']['Sessions'][ir['SessionNum']]['SessionType']
                print(sessionType)

                drivers = ir['DriverInfo']['Drivers']
                raceFinished = ir['SessionInfo']['Sessions'][ir['SessionNum']]['ResultsOfficial']

                if sessionType == "Race" and ir['SessionState'] < 4 and raceFinished != 1:
                    if ir['SessionInfo']['Sessions'][ir['SessionNum']]['QualifyPositions'] is not None:
                        grid = getGrid(drivers)
                        writeCSV(grid)

                if sessionType == "Race" and ir['SessionState'] >= 4 and raceFinished != 1:
                    if ir['SessionInfo']['Sessions'][ir['SessionNum']]['ResultsPositions'] is not None:
                        positions = getPositions(drivers)
                        writeCSV(positions)

                if sessionType == "Practice" and ir['SessionState'] != 0 and ir['SessionState'] < 4 and raceFinished != 1:
                    if ir['SessionInfo']['Sessions'][ir['SessionNum']]['QualifyPositions'] is not None:
                        grid = getGrid(drivers)
                        writeCSV(grid)

                if sessionType == "Practice" and ir['SessionState'] >= 4 and raceFinished != 1:
                    if ir['SessionInfo']['Sessions'][ir['SessionNum']]['ResultsPositions'] is not None:
                        positions = getPositions(drivers)
                        writeCSV(positions)

                if sessionType == "Open Practice" and ir['SessionState'] != 0 and ir['SessionState'] < 4 and raceFinished != 1:
                    if ir['SessionInfo']['Sessions'][ir['SessionNum']]['QualifyPositions'] is not None:
                        grid = getGrid(drivers)
                        writeCSV(grid)

                if sessionType == "Open Practice" and ir['SessionState'] >= 4 and raceFinished != 1:
                    if ir['SessionInfo']['Sessions'][ir['SessionNum']]['ResultsPositions'] is not None:
                        positions = getPositions(drivers)
                        writeCSV(positions)

            time.sleep(1)

    except KeyboardInterrupt:
        pass
