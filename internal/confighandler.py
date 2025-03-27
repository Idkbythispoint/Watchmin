import os
import json
import logging

class ConfigHandler:
    # Class-level defaults dictionary
    _default_config = {}
    
    @classmethod
    def set_defaults(cls, defaults_dict):
        """
        Set default configuration values at the class level.
        
        Args:
            defaults_dict (dict): Dictionary mapping setting names to their default values.
        """
        cls._default_config.update(defaults_dict)
    
    @classmethod
    def get_defaults(cls):
        """
        Get the current default configuration values.
        
        Returns:
            dict: The default configuration values.
        """
        return cls._default_config.copy()
    
    def __init__(self, config_path=None):
        """
        Initialize the ConfigHandler with a path to the config file.
        
        Args:
            config_path (str): Path to the configuration file. If None, uses config.cfg in the parent
                             of the parent directory of this file.
        """
        if config_path is None:
            # Get the directory of the current file (confighandler.py)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Get the parent of the parent directory
            parent_of_parent = os.path.dirname(os.path.dirname(current_dir))
            # Set config_path to config.cfg in that directory
            config_path = os.path.join(parent_of_parent, "config.cfg")
        
        self.config_path = config_path
        self.config_data = {}
        
        # Apply default configuration values automatically
        if self._default_config:
            self.ensure_defaults(self._default_config)

        self.load_config()
    def load_config(self):
        """
        Load configuration from the config file into a dictionary.
        If the file doesn't exist, create an empty config.
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as config_file:
                    self.config_data = json.load(config_file)
                logging.info(f"Configuration loaded from {self.config_path}")
            else:
                logging.warning(f"Config file {self.config_path} not found. Creating empty config.")
                self.config_data = {}
                self.save_config()
        except Exception as e:
            logging.error(f"Error loading configuration: {str(e)}")
            self.config_data = {}
    
    def save_config(self):
        """
        Save the current configuration to the config file.
        """
        try:
            with open(self.config_path, 'w') as config_file:
                json.dump(self.config_data, config_file, indent=4)
            logging.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logging.error(f"Error saving configuration: {str(e)}")
    
    def get_config(self):
        """
        Get the entire configuration table.
        
        Returns:
            dict: The configuration data.
        """
        return self.config_data
    
    def get_value(self, key, default=None):
        """
        Get a specific value from the configuration.
        
        Args:
            key (str): The configuration key to retrieve.
            default: The default value to return if the key is not found.
            
        Returns:
            The value associated with the key, or the default if not found.
        """
        return self.config_data.get(key, default)
    
    def set_value(self, key, value):
        """
        Set a specific value in the configuration.
        
        Args:
            key (str): The configuration key to set.
            value: The value to associate with the key.
        """
        self.config_data[key] = value
        self.save_config()
    
    def delete_value(self, key):
        """
        Delete a specific key from the configuration.
        
        Args:
            key (str): The configuration key to delete.
            
        Returns:
            bool: True if the key was deleted, False if it didn't exist.
        """
        if key in self.config_data:
            del self.config_data[key]
            self.save_config()
            return True
        return False
        
    def ensure_defaults(self, defaults_dict):
        """
        Ensures that required settings exist in the configuration.
        If any required setting is missing, it will be added with its default value.
        
        Args:
            defaults_dict (dict): Dictionary mapping setting names to their default values.
            
        Returns:
            bool: True if any defaults were added, False otherwise.
        """
        added_defaults = False
        for key, default_value in defaults_dict.items():
            if key not in self.config_data:
                self.config_data[key] = default_value
                added_defaults = True
                logging.info(f"Added default configuration for '{key}': {default_value}")
        
        if added_defaults:
            self.save_config()
        
        return added_defaults


# Set default configuration values - add your required settings here
# These will be automatically applied when ConfigHandler is instantiated
ConfigHandler.set_defaults({
    "lines_of_logs_to_give_llm": 10,
    "max_tokens_for_llm": 2048,
    "model_for_relevance_finder": "gpt-4o-mini",
    "model_for_fixer": "o3-mini",

})

# Example usage:
# 1. Import the ConfigHandler in your code:
#    from internal.confighandler import ConfigHandler
#
# 2. Create an instance of ConfigHandler (default settings are applied automatically):
#    config = ConfigHandler()
#
# 3. Access configuration values:
#    app_name = config.get_value("app_name")  # Returns "Watchmin" if not set in config file
