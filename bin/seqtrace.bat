@echo off

setlocal enabledelayedexpansion

rem The location of the main SeqTrace program, relative to this launch script.
set SEQTRACEPATH=..\src\run_seqtrace.py

rem The location of Python 2.7.  If no location is set, we assume that "python"
rem is in the user's PATH somewhere.
set PYTHONPATH=python

rem Get the location of this launch script.  If the script was not run from a
rem symlink, the next two lines are all we need.
set SRCPATH=%~f0
set SRCDIR=%~dp0

rem If SRCPATH is a symlink, resolve the link (and any subsequent links) until
rem we arrive at the actual script location.
:while
dir "%SRCPATH%" | find "<SYMLINK>" >nul && (
 	for /f "tokens=2 delims=[]" %%i in ('dir "!SRCPATH!" ^| find "<SYMLINK>"') do set SRCPATH=%%i

	rem If the link target is a relative path, it is relative to the
	rem original symlink location, so we must construct a new path for the
	rem link target based on SRCDIR (the original symlink location).
 	if "!SRCPATH:~1,1!" neq ":" (
 		set SRCPATH=%SRCDIR%!SRCPATH!
 	)

 	for %%m in ("!SRCPATH!") do (
 		set SRCDIR=%%~dpm
 	)

 	goto :while
)

rem Check if python is installed.
where %PYTHONPATH% >nul 2>&1
if %ERRORLEVEL% neq 0 (
	echo ERROR: Python appears to be missing or is not in your path.
	echo Please install Python in order to run SeqTrace.
	exit 1
)

rem Run SeqTrace, passing on all command-line arguments.
%PYTHONPATH% "%SRCDIR%%SEQTRACEPATH%" %*

endlocal
