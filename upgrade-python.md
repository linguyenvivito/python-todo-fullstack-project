# Update python on window

`winget --version`

`winget install --id Python.Python.3.14 -e --source winget --accept-package-agreements --accept-source-agreements`

`py -V`

# Rebuilding venv for 3.14.5


# Summary

1. Installed Python 3.14.5 via winget.
2. Verified launcher versions:
    - Default: 3.14.5
    - Also present: 3.11 and 3.8
3. Recreated your project virtual environment at .venv using 3.14.
4. Reinstalled dependencies from requirements.txt.
5. Verified project interpreter now reports:
    - Python 3.14.5
    - Executable: python.exe