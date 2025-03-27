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
    "max_relevance_searches": 3,
    "max_turns": 20,  # Maximum number of turns for LLM interactions in fixing
    "fixer_prompt": "You are a specialized code repair assistant focused on fixing runtime errors. Your task is to:\n\n1. Analyze the error message, logs, and code to precisely identify the root cause\n2. Develop a targeted solution that addresses the specific issue, not just symptoms\n3. Use available tools strategically:\n   - run_shell_command: For system-level operations\n   - run_python_code: To test hypotheses or verify solutions\n   - read_file: To examine related code that might impact the error\n   - edit_file: To implement your fixes\n   - mark_as_fixed: ONLY when you've verified the solution works\n\nFollow these principles:\n- Make minimal changes necessary to fix the error\n- Preserve existing code style and patterns\n- Test your changes before marking as fixed\n- Explain your reasoning clearly when making changes\n- Do not output user-facing messages - communicate through tool usage only\n\nOnce fixed, use the mark_as_fixed tool with {\\\"fixed\\\": true} to indicate success.",
    "VERY_EXPERIMENTAL_automatic_diff_application": False
})
