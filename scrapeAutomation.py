#!/usr/bin/env python3
#coding=utf-8
from datetime import datetime
import caldav
import random, string
from requests_html import HTMLSession
import re
import telegram_bot

masterURL = ''

class caldavEvent:
    def __init__(self, startDate, endDate, summary,uId):
        self.startDate = startDate
        self.endDate = endDate
        self.summary = summary
        self.uId = uId if uId else ''.join(random.choices(string.ascii_letters + string.digits, k=16))

def addEventToCaldav(calendar,schoolEvent):

    startDate = schoolEvent.startDate.strftime("%Y%m%dT%H%M%S")
    endDate = schoolEvent.endDate.strftime("%Y%m%dT%H%M%S")

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")

    summary = schoolEvent.summary
    uId = schoolEvent.uId

    vcal = """BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Example Corp.//CalDAV Client//EN\nBEGIN:VEVENT\nUID:"""+uId+"""\nDTSTAMP:"""+timestamp+"""\nDTSTART;TZID=Europe/Berlin:"""+startDate+"""\nDTEND;TZID=Europe/Berlin:"""+endDate+"""\nSUMMARY:"""+summary+"""\nEND:VEVENT\nEND:VCALENDAR"""

    event = calendar.add_event(vcal)
    
    print (event.instance.vevent.summary.value, "(" + str(event.instance.vevent.dtstart.value.day) + "." + str(event.instance.vevent.dtstart.value.month) + ")", "created!")

def connectCaldavClient():
    client = caldav.DAVClient(url='https://ppp.woelkli.com/remote.php/dav', username='leonjaeger000@gmail.com', password='Leonjaeger00')
    
    principal = client.principal()
    calendars = principal.calendars()
    calendar = None
    for ccalendar in calendars:
        calendar = ccalendar if ccalendar.name == 'Uni' else None
    return [client, calendar]
   
def getHtml(url):
    session = HTMLSession()
    r = session.get(url)
    r.html.render()
    r.close()
    return r.html

def scrapeForSchoolEvents(htmlPageResult):
    aTags = htmlPageResult.find("a.ui-link") 
    global allSchoolEvents
    allSchoolEvents = []

    #für jeden Schultag in einem <a>-Tag wird hier iteriert
   
    for tag in aTags:
        schoolDay = tag.text.splitlines()

        # schoolDay ist ein Schultag
        if len(schoolDay) > 0:
            splittedDate = list(filter(lambda x: x.isdigit(), schoolDay[0]))
            schoolDay.pop(0)

            dateDay = splittedDate[0] + splittedDate[1]
            dateMonth = splittedDate[2] + splittedDate[3]
            startDateTimeHH = ''
            startDateTimeMM = ''
            endDateTimeHH = ''
            endDateTimeMM = ''
            isResultUhrzeit = None
            summary= ''
            for i in range(len(schoolDay)):
        
                result = re.match('(\d\d:\d\d-\d\d:\d\d)',schoolDay[i],re.M|re.I)

                if result:
                    if summary:
                        #Kalenderevent zur Liste allSchoolEvents hinzufügen
                        dateTimeList = re.split(":|-",isResultUhrzeit)
                        startDateTimeHH = dateTimeList[0]
                        startDateTimeMM = dateTimeList[1]
                        endDateTimeHH = dateTimeList[2]
                        endDateTimeMM = dateTimeList[3]

                        startDate = datetime(int(datetime.now().year),int(dateMonth),int(dateDay),int(startDateTimeHH),int(startDateTimeMM))
                        endDate = datetime(int(datetime.now().year),int(dateMonth),int(dateDay),int(endDateTimeHH),int(endDateTimeMM))
                        uId = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

                        allSchoolEvents.append((caldavEvent(startDate,endDate,(summary[:-2]), uId)))
                    summary = ''
                    isResultUhrzeit = result.group()
                    continue

                if schoolDay[i] and schoolDay[i] != '' :
                    summary += schoolDay[i] + ", "
                
                if len(schoolDay) == i + 1:
                    dateTimeList = re.split(":|-",isResultUhrzeit)
                    startDateTimeHH = dateTimeList[0]
                    startDateTimeMM = dateTimeList[1]
                    endDateTimeHH = dateTimeList[2]
                    endDateTimeMM = dateTimeList[3]

                    startDate = datetime(int(datetime.now().year),int(dateMonth),int(dateDay),int(startDateTimeHH),int(startDateTimeMM))
                    endDate = datetime(int(datetime.now().year),int(dateMonth),int(dateDay),int(endDateTimeHH),int(endDateTimeMM))
                    uId = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

                    allSchoolEvents.append((caldavEvent(startDate,endDate,(summary[:-2]),uId)))

    return allSchoolEvents
   
def getConvertedEventsFromCaldav(calendar):
    convertedFetchedEvents = []

    fetchedEvents = calendar.events()
 
    for fetchedEvent in fetchedEvents:
        summary = re.search('SUMMARY:+.*',fetchedEvent.data).group().replace("SUMMARY:","")
        summary = summary.replace('\\', '')
        dtStart = datetime(fetchedEvent.instance.vevent.dtstart.value.year, fetchedEvent.instance.vevent.dtstart.value.month, fetchedEvent.instance.vevent.dtstart.value.day, fetchedEvent.instance.vevent.dtstart.value.hour, fetchedEvent.instance.vevent.dtstart.value.minute)
        dtEnd = datetime(fetchedEvent.instance.vevent.dtend.value.year, fetchedEvent.instance.vevent.dtend.value.month, fetchedEvent.instance.vevent.dtend.value.day, fetchedEvent.instance.vevent.dtend.value.hour, fetchedEvent.instance.vevent.dtend.value.minute)
        uId = fetchedEvent.instance.vevent.uid.value
        convertedFetchedEvents.append((caldavEvent(dtStart, dtEnd, summary, uId)))
    
    return convertedFetchedEvents

def addModifiedEvents(calendar, schoolEvents):
    counterAddedEvents = 0
    counterModifiedEvents = 0
    changedEvents = []

    calendarEvents = getConvertedEventsFromCaldav(calendar)

    for schoolEvent in schoolEvents:
        found = False
        for calendarEvent in calendarEvents:
            if schoolEvent.startDate == calendarEvent.startDate and \
                schoolEvent.endDate == calendarEvent.endDate and \
                schoolEvent.summary == calendarEvent.summary:
                    found = True
            elif schoolEvent.startDate.day == calendarEvent.startDate.day and \
                schoolEvent.endDate.day == calendarEvent.startDate.day and \
                ((schoolEvent.startDate == calendarEvent.startDate and \
                schoolEvent.endDate == calendarEvent.endDate and \
                schoolEvent.summary != calendarEvent.summary) or \
                (schoolEvent.startDate == calendarEvent.startDate and \
                schoolEvent.endDate != calendarEvent.endDate and \
                schoolEvent.summary == calendarEvent.summary) or \
                (schoolEvent.startDate != calendarEvent.startDate and \
                schoolEvent.endDate == calendarEvent.endDate and \
                schoolEvent.summary == calendarEvent.summary) or \
                (schoolEvent.startDate != calendarEvent.startDate and \
                schoolEvent.endDate != calendarEvent.endDate and \
                schoolEvent.summary == calendarEvent.summary)):
                    oldEventSearch = calendar.date_search(calendarEvent.startDate, calendarEvent.endDate)
                    for oldEvent in oldEventSearch:
                        changedEvents.append(schoolEvent)
                        oldEvent.delete()
                        print("Deleted", oldEvent.instance.vevent.summary.value, oldEvent.instance.vevent.dtstart.value)
                    addEventToCaldav(calendar,schoolEvent)
                    counterModifiedEvents += 1
                    found = True
                
        
        if not found:
            addEventToCaldav(calendar,schoolEvent)
            counterAddedEvents += 1

    return [counterAddedEvents, counterModifiedEvents, changedEvents]
    
def getUrlOfMonth(intMonth):
    addingYear = 0
    realMonth = intMonth
    if intMonth > 12:
        intMonth = intMonth - 12
        addingYear = 1
    thisMonthTimestamp = datetime(datetime.now().year + addingYear,intMonth,1).timestamp()
    masterURL = 'https://vorlesungsplan.dhbw-mannheim.de/index.php?action=view&gid=3069001&uid=7752001&date=' + str(thisMonthTimestamp) + '&view=month'

    return masterURL

def main():
    global masterURL 
    result = connectCaldavClient()
    client = result[0]
    calendar = result[1]

    for month in range(0, 3):
        masterURL = getUrlOfMonth(datetime.now().month + month)

        htmlPageResult = getHtml(masterURL)
        schoolEvents = scrapeForSchoolEvents(htmlPageResult)


        if schoolEvents:
            returnValuesAddNewEventsToCaldav = addModifiedEvents(calendar,schoolEvents)
            counterNewEvents = returnValuesAddNewEventsToCaldav[0]
            counterChangedEvents = returnValuesAddNewEventsToCaldav[1]
            listChangedEvents = returnValuesAddNewEventsToCaldav[2]

        if counterChangedEvents > 0 or counterNewEvents > 0:
            print("\n----------------------------")
            print("new Events:",counterNewEvents)
            print("Modified Events:", counterChangedEvents, listChangedEvents)
            print("----------------------------")
            
            if listChangedEvents:
                with open('chat_Ids.txt') as f:
                   for changedEvent in listChangedEvents:
                        print(type(changedEvent))
                        date = str(changedEvent.startDate.day) + '.' + str(changedEvent.startDate.month) + '.' + str(changedEvent.startDate.year)
                        startTime = changedEvent.startDate.strftime('%H:%M') #str(changedEvent.instance.vevent.dtstart.value.hour) + ':' + str(changedEvent.instance.vevent.dtstart.value.minute)
                        endTime = changedEvent.endDate.strftime('%H:%M')#str(changedEvent.instance.vevent.dtend.value.hour) + ':' + str(changedEvent.instance.vevent.dtend.value.minute)
                        text = str(changedEvent.summary)

                        textValue = 'Neuigkeiten:\nAm ' + str(date) + ' von ' + str(startTime) + ' bis ' + str(endTime) + '\n' + text 
                        input = f.readlines()
                        for line in input:
                            if line:
                                id = line.replace('\n','')
                                telegram_bot.CalUpdaterBot.send_message(id, textValue)

if __name__ == "__main__":
    main()

       
