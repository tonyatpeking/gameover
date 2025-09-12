# Show the path of all Explorer Windows
# from win32com.client.gencache import EnsureDispatch

# for w in EnsureDispatch("Shell.Application").Windows():
#     print(w.LocationName + "=" + w.LocationURL)


# Copying text into Windows Clipboard
# import win32clipboard

# win32clipboard.OpenClipboard()
# win32clipboard.EmptyClipboard()
# win32clipboard.SetClipboardText("text")
# win32clipboard.CloseClipboard()


# A file open dialog with win32ui
# import win32ui

# o = win32ui.CreateFileDialog(
#     1, ".txt", "default.txt", 0, "Text Files (*.txt)|*.txt|All Files (*.*)|*.*|"
# )
# o.DoModal()
# print(o.GetPathName())


# Two instances of Windows Explorer side by side
# from win32gui import (
#     EnumWindows,
#     SetWindowPos,
#     GetDesktopWindow,
#     GetWindowRect,
#     FindWindow,
#     GetClassName,
#     ShowWindow,
# )
# import os, time
# import pywintypes


# def enumWinProc(h, lparams):

#     if GetClassName(h) == "ExploreWClass":
#         lparams.append(h)


# winList = []
# EnumWindows(enumWinProc, winList)
# winCnt = len(winList)
# if winCnt == 0:  # No Explorer running
#     os.system("explorer.exe")
#     while 1:
#         try:
#             FindWindow("ExploreWClass", None)  # Wait for first instance to run
#         except pywintypes.error:
#             pass
#         else:
#             break
#         time.sleep(0.1)  # Sleep for a while before continuing
#     os.system("explorer.exe")  # Start second instance
# elif winCnt == 1:
#     os.system("explorer.exe")  # Start second instance
# time.sleep(2)  # Wait for Explorer to run
# winList = []
# EnumWindows(enumWinProc, winList)  # Get handles of running Explorer
# hDesk = GetDesktopWindow()
# (dLeft, dTop, dRight, dBottom) = GetWindowRect(hDesk)  # Get desktop size
# SetWindowPos(
#     winList[0], 0, dRight / 2, 0, dRight / 2, dBottom, 0
# )  # Set the windows sizes
# SetWindowPos(winList[1], 0, 0, 0, dRight / 2, dBottom, 0)
# ShowWindow(winList[0], 1)  # Show the windows
# ShowWindow(winList[1], 1)


# Calculator automation via sendkeys
# import win32com.client
# import win32api

# shell = win32com.client.Dispatch("WScript.Shell")
# shell.Run("calc")
# win32api.Sleep(100)
# shell.AppActivate("Calculator")
# win32api.Sleep(100)
# shell.SendKeys("1{+}")
# win32api.Sleep(500)
# shell.SendKeys("2")
# win32api.Sleep(500)
# shell.SendKeys("~")  # ~ is the same as {ENTER}
# win32api.Sleep(500)
# shell.SendKeys("*3")
# win32api.Sleep(500)
# shell.SendKeys("~")
# win32api.Sleep(2500)

# Controlling applications via sendkeys
# https://win32com.goermezer.de/microsoft/windows/controlling-applications-via-sendkeys.html


# Show usable ProgIDs for win32com
# This example shows you the available ProgIDs of the Windows applications which are installed and ahould be usable  with win32com. My problem is, that most of the ProgIDs are shown, but not all ?!
# import win32com.client

# strComputer = "."
# objWMIService = win32com.client.Dispatch("WbemScripting.SWbemLocator")
# objSWbemServices = objWMIService.ConnectServer(strComputer, r"root\cimv2")
# colItems = objSWbemServices.ExecQuery("Select * from Win32_ProgIDSpecification")
# for objItem in colItems:
#     print("Caption: ", objItem.Caption)
#     print("Check ID: ", objItem.CheckID)
#     print("Check Mode: ", objItem.CheckMode)
#     print("Description: ", objItem.Description)
#     print("Name: ", objItem.Name)
#     print("Parent: ", objItem.Parent)
#     print("ProgID: ", objItem.ProgID)
#     print("Software Element ID: ", objItem.SoftwareElementID)
#     print("Software Element State: ", objItem.SoftwareElementState)
#     print("Target Operating System: ", objItem.TargetOperatingSystem)
#     print("Version: ", objItem.Version)
#     print("-------------------------------------------------------------------\n")


# Shellwindows
# This example prints the name and and pathes of the open windows (Tip: You can get the CLSID with makepy in Pythonwin):

# import win32com.client

# # look in the makepy output for IE for the 'CLSIDToClassMap'
# # dictionary, and find the entry for 'ShellWindows'
# clsid = "{9BA05972-F6A8-11CF-A442-00A0C90A8F39}"
# ShellWindows = win32com.client.Dispatch(clsid)
# for i in range(ShellWindows.Count):
#     print(i)
#     # this is the titlebar value
#     print(ShellWindows[i].LocationName)
#     # this is the current URL
#     print(ShellWindows[i].LocationURL)
# print()


# Print all events from Windows Event Log
# import win32com.client

# strComputer = "."
# objWMIService = win32com.client.Dispatch("WbemScripting.SWbemLocator")
# objSWbemServices = objWMIService.ConnectServer(strComputer, "root\cimv2")
# colItems = objSWbemServices.ExecQuery("Select * from Win32_NTLogEvent")
# for objItem in colItems:
#     print("Category: ", objItem.Category)
#     print("Category String: ", objItem.CategoryString)
#     print("Computer Name: ", objItem.ComputerName)
#     z = objItem.Data
#     if z is None:
#         a = 1
#     else:
#         for x in z:
#             print("Data: ", x)
#     print("Event Code: ", objItem.EventCode)
#     print("Event Identifier: ", objItem.EventIdentifier)
#     print("Event Type: ", objItem.EventType)
#     z = objItem.InsertionStrings
#     if z is None:
#         a = 1
#     else:
#         for x in z:
#             print("Insertion Strings: ", x)
#     print("Logfile: ", objItem.Logfile)
#     print("Message: ", objItem.Message)
#     print("Record Number: ", objItem.RecordNumber)
#     print("Source Name: ", objItem.SourceName)
#     print("Time Generated: ", objItem.TimeGenerated)
#     print("Time Written: ", objItem.TimeWritten)
#     print("Type: ", objItem.Type)
#     print("User: ", objItem.User)
