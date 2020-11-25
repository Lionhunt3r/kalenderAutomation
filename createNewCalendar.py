#!/usr/bin/env python3
#coding=utf-8
import scrapeAutomation as scrapeFunctions
import caldav
import random, string
from requests_html import HTMLSession
from datetime import datetime
import re

client = caldav.DAVClient(url='https://ppp.woelkli.com/remote.php/dav', username='', password='')

principal = client.principal()
calendars = principal.calendars()
for calendar in calendars:
    calendar.delete()

calendar = principal.make_calendar('Uni')

for month in range(0, 3):
    masterURL = scrapeFunctions.getUrlOfMonth(datetime.now().month + month)

    htmlPageResult = scrapeFunctions.getHtml(masterURL)
    schoolEvents = scrapeFunctions.scrapeForSchoolEvents(htmlPageResult)


    if schoolEvents:
        for schoolEvent in schoolEvents:
            scrapeFunctions.addEventToCaldav(calendar, schoolEvent)

