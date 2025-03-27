# CLI-Based Chess

just felt like making a cli app x)

## Installation

### Install Dependencies
Install dependencies stated in `requirements.txt`.

### Install Stockfish

#### Windows
- Download from the official Stockfish website.
- Add to PATH or place in the standard Program Files directory.

#### macOS
```bash
brew install stockfish
```

#### Linux
```bash
sudo apt-get install stockfish  # Ubuntu/Debian
sudo dnf install stockfish      # Fedora
```

## Running the Game

### Player vs Player (default)
```bash
python chess_cli.py
```

### Player vs Computer
```bash
python chess_cli.py --mode pvc
```

### Set AI Difficulty (1-20)
```bash
python chess_cli.py --mode pvc --difficulty 10
```