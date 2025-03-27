import chess
import chess.engine
import rich
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from typing import Optional, Tuple
import sys
import argparse
import shutil
import platform
import os

class ChessPieces:
    """Unicode and Letter-based Chess Piece Representations"""
    UNICODE = {
        'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
        'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
    }
    
    LETTERS = {
        'P': 'P', 'N': 'N', 'B': 'B', 'R': 'R', 'Q': 'Q', 'K': 'K',
        'p': 'p', 'n': 'n', 'b': 'b', 'r': 'r', 'q': 'q', 'k': 'k'
    }
class ChessColors:
    """Define color scheme for the chessboard"""
    LIGHT_SQUARE = "on bright_white"
    DARK_SQUARE = "on bright_black"
    WHITE_PIECE = "bold white"
    BLACK_PIECE = "bold black"
    HIGHLIGHT = "on green"
    LAST_MOVE = "on yellow"

class ChessUI:
    """Handles terminal-based chess board rendering"""
    
    @staticmethod
    def clear_screen():
        """Clear terminal screen cross-platform"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def render_board(board: chess.Board, console: Console, 
                     last_move: Optional[chess.Move] = None, 
                     legal_moves: Optional[list] = None,
                     piece_mode: str = 'unicode') -> None:
        """Render the chessboard with rich formatting"""
        # Choose piece representation
        pieces = (ChessPieces.UNICODE if piece_mode == 'unicode' 
                  else ChessPieces.LETTERS)
        
        # Clear screen to create fixed board position
        ChessUI.clear_screen()
        
        board_display = []
        
        # Render column headers
        column_headers = "   " + " ".join([chr(97 + i) for i in range(8)])
        board_display.append(Text(column_headers, style="bold blue"))
        
        for rank in range(7, -1, -1):
            row_display = [Text(str(rank + 1), style="bold blue")]
            
            for file in range(8):
                square = chess.square(file, rank)
                piece = board.piece_at(square)
                
                # Determine square color
                square_color = (ChessColors.LIGHT_SQUARE if (file + rank) % 2 == 0 
                                else ChessColors.DARK_SQUARE)
                
                # Highlight logic
                is_last_move = (last_move and 
                                (square == last_move.from_square or 
                                 square == last_move.to_square))
                is_legal_move = (legal_moves and square in [move.to_square for move in legal_moves])
                
                if is_last_move:
                    square_color += f" {ChessColors.LAST_MOVE}"
                elif is_legal_move:
                    square_color += f" {ChessColors.HIGHLIGHT}"
                
                # Piece rendering
                if piece:
                    piece_style = (ChessColors.WHITE_PIECE if piece.color == chess.WHITE 
                                   else ChessColors.BLACK_PIECE)
                    piece_symbol = pieces[piece.symbol()]
                    piece_text = Text(piece_symbol, style=f"{piece_style} {square_color}")
                else:
                    piece_text = Text(".", style=square_color)
                
                row_display.append(piece_text)
            
            board_display.append(Text(" ").join(row_display))
        
        # Render board panel
        board_panel = Panel(
            Text("\n").join(board_display), 
            title="Chess Board", 
            border_style="blue"
        )
        console.print(board_panel)

class ChessGame:
    """Main game management class"""
    
    def __init__(self, game_mode: str = "pvp", difficulty: int = 2):
        self.board = chess.Board()
        self.game_mode = game_mode
        self.difficulty = difficulty
        self.console = Console()
        self.move_history = []
        self.engine = None
        self.piece_mode = 'unicode'
        
        # Stockfish setup if playing against computer
        if game_mode == "pvc":
            self.setup_stockfish()
    
    def setup_stockfish(self):
        """Set up Stockfish engine with flexible path detection"""
        # Detect Stockfish executable based on platform
        stockfish_paths = self.get_stockfish_paths()
        
        for path in stockfish_paths:
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(path)
                self.engine.configure({"Skill Level": self.difficulty})
                # self.console.print(f"[green]Stockfish found at: {path}[/green]")
                return
            except Exception:
                continue
        
        # If no Stockfish found
        self.console.print("[red]Stockfish engine not found. Install Stockfish or add to PATH.[/red]")
        self.console.print("[yellow]Defaulting to Player vs Player mode.[/yellow]")
        self.game_mode = "pvp"
    
    def get_stockfish_paths(self) -> list:
        """Detect possible Stockfish executable paths"""
        paths = []
        
        # Common names and paths
        common_names = ['stockfish', 'stockfish.exe']
        
        # Platform-specific paths
        if platform.system() == "Windows":
            paths.extend([
                "C:\\Program Files\\Stockfish\\stockfish.exe",
                "C:\\Program Files (x86)\\Stockfish\\stockfish.exe",
            ])
        elif platform.system() == "Darwin":  # macOS
            paths.extend([
                "/usr/local/bin/stockfish",
                "/opt/homebrew/bin/stockfish",
                "/Applications/Stockfish.app/Contents/MacOS/stockfish"
            ])
        elif platform.system() == "Linux":
            paths.extend([
                "/usr/bin/stockfish",
                "/usr/local/bin/stockfish"
            ])
        
        # Add paths from system PATH
        system_path = shutil.which('stockfish')
        if system_path:
            paths.append(system_path)
        
        # Add common names to all paths
        full_paths = []
        for path in paths:
            full_paths.extend([path] + [
                path.replace('stockfish', name) for name in common_names
            ])
        
        return full_paths
    
    def make_move(self, move_san: str) -> bool:
        """Attempt to make a move on the board"""
        try:
            move = self.board.parse_san(move_san)
            if move in self.board.legal_moves:
                self.move_history.append(move)
                self.board.push(move)
                return True
            else:
                self.console.print("[red]Illegal move! Try again.[/red]")
                return False
        except ValueError:
            self.console.print("[red]Invalid move notation! Use Standard Algebraic Notation.[/red]")
            return False
    
    def computer_move(self) -> Optional[chess.Move]:
        """Computer makes a move using Stockfish"""
        if self.game_mode != "pvc" or not self.engine:
            return None
        
        try:
            result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
            self.board.push(result.move)
            return result.move
        except Exception as e:
            self.console.print(f"[red]Computer move error: {e}[/red]")
            return None
    
    def play(self):
        """Main game loop"""
        last_move = None
        legal_moves = None
        
        while not self.board.is_game_over():
            # Render board, but only clear screen for normal gameplay
            if not (last_move is None and legal_moves is None):
                ChessUI.clear_screen()
            
            # Render board
            ChessUI.render_board(
                self.board, 
                self.console, 
                last_move=last_move, 
                legal_moves=legal_moves,
                piece_mode=self.piece_mode
            )
            
            # Determine current player
            current_player = "White" if self.board.turn == chess.WHITE else "Black"
            
            # Computer move if in Player vs Computer mode
            if self.game_mode == "pvc" and current_player == "Black":
                last_move = self.computer_move()
                continue
            
            # Player move input
            move_input = input(f"{current_player}'s turn. Enter move (or 'help'): ").strip()
            
            # Command handling
            if move_input.lower() == 'help':
                self.show_help()
                input("Press Enter to continue...")  # Wait for user to read help
                continue
            elif move_input.lower() in ['quit', 'exit']:
                break
            elif move_input.lower() == 'undo':
                self.undo_move()
                continue
            elif move_input.lower().startswith('pieces '):
                mode = move_input.lower().split()[1]
                if mode in ['unicode', 'letters']:
                    self.piece_mode = mode
                    self.console.print(f"[green]Switched to {mode} piece representation.[/green]")
                else:
                    self.console.print("[red]Invalid piece mode. Use 'unicode' or 'letters'.[/red]")
                continue
            
            # Process move
            move_result = self.make_move(move_input)
            if move_result:
                last_move = self.board.peek()
                legal_moves = list(self.board.legal_moves)
        
        # Game over handling
        self.console.print("\n[bold green]Game Over![/bold green]")
        self.show_result()

    def show_help(self):
        """Display game help"""
        help_text = """
        Chess CLI Help:
        • Enter moves in Standard Algebraic Notation (e.g., 'e4', 'Nf3')
        • Special commands:
          - 'help': Show this help
          - 'undo': Take back the last move
          - 'quit': Exit the game
          - 'pieces unicode': Switch to Unicode chess pieces
          - 'pieces letters': Switch to letter-based chess pieces
        """
        self.console.print(Panel(help_text, title="Help", border_style="blue"))
    
    def undo_move(self):
        """Undo the last move"""
        if self.move_history:
            self.board.pop()
            self.move_history.pop()
            self.console.print("[yellow]Last move undone.[/yellow]")
        else:
            self.console.print("[red]No moves to undo![/red]")
    
    def show_result(self):
        """Show game result and reason"""
        if self.board.is_checkmate():
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            self.console.print(f"[bold green]Checkmate! {winner} wins![/bold green]")
        elif self.board.is_stalemate():
            self.console.print("[yellow]Stalemate! The game is a draw.[/yellow]")
        elif self.board.is_insufficient_material():
            self.console.print("[yellow]Insufficient material. The game is a draw.[/yellow]")
        elif self.board.is_fifty_moves():
            self.console.print("[yellow]Fifty-move rule. The game is a draw.[/yellow]")
        elif self.board.is_repetition():
            self.console.print("[yellow]Threefold repetition. The game is a draw.[/yellow]")
    
    def __del__(self):
        """Cleanup Stockfish engine"""
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass

def main():
    parser = argparse.ArgumentParser(description="Chess CLI Game")
    parser.add_argument(
        '--mode', 
        choices=['pvp', 'pvc'], 
        default='pvp', 
        help='Game mode: Player vs Player or Player vs Computer'
    )
    parser.add_argument(
        '--difficulty', 
        type=int, 
        default=2, 
        choices=range(1, 21), 
        help='Stockfish AI difficulty (1-20)'
    )
    
    args = parser.parse_args()
    
    try:
        game = ChessGame(game_mode=args.mode, difficulty=args.difficulty)
        game.play()
    except KeyboardInterrupt:
        print("\n[Game terminated by user]")

if __name__ == "__main__":
    main()