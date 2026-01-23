"""Text formatting and display utilities for the MUD server."""

class Formatter:
    """Handles all text formatting and ANSI color codes."""
    
    def __init__(self):
        # ANSI color codes for terminal highlighting
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'dim': '\033[2m',
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'orange': '\033[38;5;208m',
            'gray': '\033[90m',
            'purple': '\033[38;5;141m',
            'brown': '\033[38;5;130m'
        }
    
    def format_brackets(self, text, color='cyan'):
        """Format text with colored brackets"""
        color_code = self.colors.get(color, self.colors['cyan'])
        return f"{color_code}[{self.colors['reset']}{text}{color_code}]{self.colors['reset']}"
    
    def format_item(self, text):
        """Format item names with highlighting"""
        return f"{self.colors['yellow']}{text}{self.colors['reset']}"
    
    def format_npc(self, text):
        """Format NPC names with highlighting"""
        return f"{self.colors['magenta']}{text}{self.colors['reset']}"
    
    def format_exit(self, direction):
        """Format exit directions with brackets"""
        return self.format_brackets(direction.capitalize(), 'green')
    
    def format_command(self, text):
        """Format commands in help text"""
        return self.format_brackets(text, 'blue')
    
    def format_header(self, text):
        """Format headers with bold"""
        return f"{self.colors['bold']}{text}{self.colors['reset']}"
    
    def format_success(self, text):
        """Format success messages"""
        return f"{self.colors['green']}{text}{self.colors['reset']}"
    
    def format_error(self, text):
        """Format error messages"""
        return f"{self.colors['red']}{text}{self.colors['reset']}"
    
    def send_to_player(self, player, message):
        """Send formatted message to player"""
        try:
            message_str = str(message) + "\n"
            player.connection.sendall(message_str.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message to {player.name}: {e}")
