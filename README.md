# ORC-MANAGER
🏎️ WRC League Manager - Quick Start Guide
Welcome to the WRC League Manager! This app runs locally on your computer. We've set it up so you don't need to be a programmer to use it. Just follow these simple steps!

🛠️ Prerequisites
You only need one thing installed on your computer: Python 3.

Windows users: Download it from python.org. CRITICAL STEP: During installation, you must check the box at the very bottom that says "Add Python to PATH" before clicking Install.

Mac/Linux users: You likely already have Python installed. If not, download it or use your package manager.

🚀 How to Launch the App
For Windows:

Double-click the Run_WRC.bat file.

A black terminal window will pop up. Don't panic! This is our server working in the background.

If it's your first time running it, the script will automatically download the necessary files (it takes about a minute).

Your web browser will automatically open the app (http://127.0.0.1:8000).

For Mac / Linux:

Open your terminal in the project folder.

Run this command to grant permissions (you only do this once): chmod +x run_wrc.sh

Start the app by typing: ./run_wrc.sh

⚠️ THE GOLDEN RULE
Do not close the black terminal window while you are using the app!

The app runs inside your web browser, but the actual "brain" (server) lives in that black window. If you close the terminal, the website will stop working and display a "Site can't be reached" error.

When you are completely done managing your league, you can safely close the browser and then close the terminal window. All your data is safely saved in the wrc_liga.db file!
