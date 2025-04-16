# Space Weather Timeline App Shortcut Instructions

This document explains how to create a desktop shortcut for the Space Weather Timeline app.

## Prerequisites

Before creating the shortcut, make sure you have:

1. Installed all required dependencies using `pip install -r requirements.txt`
2. Set up your `.streamlit/secrets.toml` file with your API keys and configuration
3. Verified that the app runs correctly by executing `streamlit run app.py` in your terminal

## Creating a Desktop Shortcut

### Automatic Method

1. Double-click the `create_shortcut.vbs` file in the project directory
2. A shortcut named "Space Weather Timeline" will be created on your desktop
3. You can now launch the app by double-clicking this shortcut

### Manual Method

If the automatic method doesn't work, you can create a shortcut manually:

1. Right-click on your desktop and select "New > Shortcut"
2. In the location field, enter the full path to the batch file:
   ```
   C:\Path\To\Your\Project\launch_spaceweather_app.bat
   ```
   (Replace with the actual path to your project)
3. Click "Next"
4. Name the shortcut "Space Weather Timeline" and click "Finish"
5. Right-click the new shortcut and select "Properties"
6. In the "Start in" field, enter the full path to your project directory:
   ```
   C:\Path\To\Your\Project
   ```
7. Click "OK" to save the changes

## Customizing the Shortcut

To change the icon of your shortcut:

1. Right-click the shortcut and select "Properties"
2. Click the "Change Icon" button
3. Browse to a suitable icon file or select one from the Windows system icons
4. Click "OK" to save the changes

## Troubleshooting

If the shortcut doesn't work:

1. Make sure you have Python and Streamlit installed and accessible from the command line
2. Check that all dependencies are installed
3. Verify that the app runs correctly when launched manually with `streamlit run app.py`
4. Check that the paths in the shortcut properties are correct
5. Try running the batch file directly to see if there are any error messages

## Moving the Shortcut

You can move the shortcut to other locations such as:

- The Start menu
- The taskbar (by right-clicking the shortcut and selecting "Pin to taskbar")
- A different folder

The app will still work as long as you don't move the actual project files.
