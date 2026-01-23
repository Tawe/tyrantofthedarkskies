"""Logging module for security and audit trails."""

import logging
import os
from datetime import datetime

class SecurityLogger:
    """Handles security-related logging and audit trails."""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.setup_logging()
    
    def setup_logging(self):
        """Set up logging configuration"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # Security/audit log
        security_log = os.path.join(self.log_dir, "security.log")
        self.security_logger = logging.getLogger('security')
        self.security_logger.setLevel(logging.INFO)
        security_handler = logging.FileHandler(security_log)
        security_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.security_logger.addHandler(security_handler)
        
        # General server log
        server_log = os.path.join(self.log_dir, "server.log")
        self.server_logger = logging.getLogger('server')
        self.server_logger.setLevel(logging.INFO)
        server_handler = logging.FileHandler(server_log)
        server_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.server_logger.addHandler(server_handler)
    
    def log_login_attempt(self, player_name, ip_address, success):
        """Log login attempts"""
        status = "SUCCESS" if success else "FAILED"
        self.security_logger.info(
            f"LOGIN {status} - Player: {player_name}, IP: {self.mask_ip(ip_address)}"
        )
    
    def log_admin_action(self, admin_name, action, details=""):
        """Log admin actions for audit trail"""
        self.security_logger.warning(
            f"ADMIN ACTION - Admin: {admin_name}, Action: {action}, Details: {details}"
        )
    
    def log_security_event(self, event_type, player_name, details):
        """Log security-related events"""
        self.security_logger.warning(
            f"SECURITY EVENT - Type: {event_type}, Player: {player_name}, Details: {details}"
        )
    
    def log_error(self, error_type, message, ip_address=None):
        """Log errors"""
        ip_str = f", IP: {self.mask_ip(ip_address)}" if ip_address else ""
        self.server_logger.error(f"{error_type}{ip_str} - {message}")
    
    def log_info(self, message):
        """Log general information"""
        self.server_logger.info(message)
    
    def mask_ip(self, ip_address):
        """Mask IP address for privacy (e.g., 192.168.1.xxx)"""
        if isinstance(ip_address, tuple):
            ip = ip_address[0]
        else:
            ip = str(ip_address)
        
        # Mask last octet for IPv4
        parts = ip.split('.')
        if len(parts) == 4:
            return '.'.join(parts[:3]) + '.xxx'
        return ip  # Return as-is if not IPv4
