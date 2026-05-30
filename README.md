# Sudoku

A Pygame Sudoku game with a browser-ready localhost build. The game starts with
an animated Sudoku loading screen, asks the player to pick a difficulty, then
opens the playable Sudoku board.

## Features

- Randomized Sudoku puzzles for Easy, Medium, and Hard.
- Real Sudoku validation for rows, columns, and 3x3 boxes.
- Timer that starts when a difficulty is selected.
- Hint button on Easy and Medium.
- Each hint reveals one correct solution cell and adds a 15-second penalty.
- Hints are disabled on Hard.
- Left-side rules box and right-side leaderboard.
- Win screen with player name entry.
- Leaderboard sorted by fastest adjusted completion time.
- Browser leaderboard persistence through `localStorage` when running with pygbag.

## Difficulties

- Easy: 51 starting clues.
- Medium: 41 starting clues.
- Hard: 31 starting clues and no hints.

## Run the Desktop Game

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run the Pygame version:

```bash
python3 sudoku.py
```

## Run the Browser/Localhost Version

Install dependencies if needed:

```bash
python3 -m pip install -r requirements.txt
```

Start the pygbag local server:

```bash
./web.sh
```

Open the URL printed by pygbag:

```text
http://localhost:8000/
```

Equivalent direct command:

```bash
python -m pygbag --ume_block 0 --template static/sudoku.tmpl .
```

## Web Deployment

The Vercel build uses pygbag to create a static web build in `build/web`.
The repository includes `vercel.json` so Vercel can run the build command and
serve the generated static output.
