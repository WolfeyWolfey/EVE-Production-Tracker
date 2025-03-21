"""
Blueprint management GUI components for EVE Production Calculator
This file contains the UI components and logic for blueprint management
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import platform
import re

from core.config.blueprint_config import save_blueprint_ownership, update_blueprint_ownership
from core.config.blueprint_config import get_blueprint_ownership, get_blueprint_me, get_blueprint_te
from core.config.blueprint_config import update_blueprint_me, update_blueprint_te
from core.utils.debug import debug_print

class BlueprintManager:
    """
    Blueprint management class for handling blueprint ownership and invention status
    for EVE Online ships, capital ships, components, and capital components.
    """
    
    def __init__(self, parent, discovered_modules, blueprint_config, module_registry):
        """
        Initialize the blueprint manager
        
        Args:
            parent: The parent tkinter application
            discovered_modules: Dictionary of discovered modules
            blueprint_config: Blueprint configuration
            module_registry: Module registry
        """
        self.parent = parent
        self.discovered_modules = discovered_modules
        self.blueprint_config = blueprint_config
        self.module_registry = module_registry
        
        # Initialize status variable
        if hasattr(parent, 'status_var'):
            self.status_var = parent.status_var
        else:
            self.status_var = tk.StringVar()
            self.status_var.set("Ready")
        
    def create_blueprint_management_tab(self, parent_tab):
        """Create the main blueprint management tab"""
        # Create notebook for different blueprint types
        notebook = ttk.Notebook(parent_tab)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create main tabs
        ships_tab = ttk.Frame(notebook)
        components_tab = ttk.Frame(notebook)
        
        # Add tabs to notebook
        notebook.add(ships_tab, text="Ships")
        notebook.add(components_tab, text="Components")
        
        # Create combined ships blueprint management tab (regular + capital ships)
        self.create_combined_ships_blueprint_tab(ships_tab)
        
        # Create combined components blueprint tab (regular + capital components)
        self.create_combined_components_blueprint_tab(components_tab)
        
        # Create save frame at the bottom
        save_frame = ttk.Frame(parent_tab)
        save_frame.pack(fill="x", padx=10, pady=10)
        
        # Add reset button
        reset_button = ttk.Button(save_frame, text="Reset All Ship Ownership", 
                               command=self.reset_all_ship_ownership)
        reset_button.pack(side="left", padx=5)
        
        # Add save button
        save_button = ttk.Button(save_frame, text="Save Configuration", 
                                command=self.save_blueprint_config)
        save_button.pack(side="right", padx=5)
    
    def create_combined_ships_blueprint_tab(self, parent_tab):
        """Create the combined ships blueprint tab"""
        if 'ships' in self.discovered_modules or 'capital_ships' in self.discovered_modules:
            # Frame for ship blueprint management
            ship_frame = ttk.LabelFrame(parent_tab, text="Ship Blueprints")
            ship_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Create grid view for ships
            self.create_ship_blueprint_grid(ship_frame)
        else:
            ttk.Label(parent_tab, text="No ship modules discovered").pack(padx=10, pady=10)
    
    def create_combined_components_blueprint_tab(self, parent_tab):
        """Create the combined components blueprint tab with a single table for all components"""
        # Container for all components
        components_container = ttk.Frame(parent_tab)
        components_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Single labelframe for all components
        component_frame = ttk.LabelFrame(components_container, text="Component Blueprints")
        component_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollable canvas
        canvas = tk.Canvas(component_frame)
        scrollbar = ttk.Scrollbar(component_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create grid frame inside canvas
        grid_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=grid_frame, anchor="nw")
        
        # Create headers for the grid
        ttk.Label(grid_frame, text="Component Blueprint", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(grid_frame, text="Unowned", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(grid_frame, text="Owned", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ttk.Label(grid_frame, text="ME%", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        ttk.Label(grid_frame, text="TE%", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=4, padx=5, pady=5, sticky="w")
        
        row = 1
        has_components = False
        
        # Add regular components
        if 'components' in self.discovered_modules and self.discovered_modules['components']:
            has_components = True
            components = self.discovered_modules['components']
            
            for comp_name, comp_data in components.items():
                # Display name
                ttk.Label(grid_frame, text=comp_data.display_name).grid(row=row, column=0, padx=5, pady=2, sticky="w")
                
                # Set up ownership radio buttons
                if not hasattr(comp_data, 'ownership_var'):
                    comp_data.ownership_var = tk.StringVar()
                
                # Get ownership status
                ownership_status = get_blueprint_ownership(self.blueprint_config, 'components', comp_name)
                if ownership_status:
                    comp_data.ownership_var.set("owned")
                else:
                    comp_data.ownership_var.set("unowned")
                
                # Unowned radio button
                ttk.Radiobutton(
                    grid_frame, 
                    value="unowned", 
                    variable=comp_data.ownership_var,
                    command=lambda n=comp_name, d=comp_data, v="unowned": self.update_component_ownership(n, d, v)
                ).grid(row=row, column=1, padx=5, pady=2)
                
                # Owned radio button
                ttk.Radiobutton(
                    grid_frame, 
                    value="owned", 
                    variable=comp_data.ownership_var,
                    command=lambda n=comp_name, d=comp_data, v="owned": self.update_component_ownership(n, d, v)
                ).grid(row=row, column=2, padx=5, pady=2)
                
                # ME% input field
                if not hasattr(comp_data, 'me_var'):
                    comp_data.me_var = tk.StringVar()
                me_value = get_blueprint_me(self.blueprint_config, 'components', comp_name)
                comp_data.me_var.set(str(me_value))
                me_entry = ttk.Entry(grid_frame, width=4, textvariable=comp_data.me_var)
                me_entry.grid(row=row, column=3, padx=5, pady=2)
                me_entry.bind("<FocusOut>", lambda event, n=comp_name: self.validate_me(event, 'components', n))
                
                # TE% input field
                if not hasattr(comp_data, 'te_var'):
                    comp_data.te_var = tk.StringVar()
                te_value = get_blueprint_te(self.blueprint_config, 'components', comp_name)
                comp_data.te_var.set(str(te_value))
                te_entry = ttk.Entry(grid_frame, width=4, textvariable=comp_data.te_var)
                te_entry.grid(row=row, column=4, padx=5, pady=2)
                te_entry.bind("<FocusOut>", lambda event, n=comp_name: self.validate_te(event, 'components', n))
                
                row += 1
        
        # Add capital components
        if hasattr(self.module_registry, 'capital_components') and self.module_registry.capital_components:
            has_components = True
            self.discovered_modules['capital_components'] = self.module_registry.capital_components
            capital_components = self.module_registry.capital_components
            
            for comp_name, comp_data in capital_components.items():
                # Display name
                ttk.Label(grid_frame, text=comp_data.display_name).grid(row=row, column=0, padx=5, pady=2, sticky="w")
                
                # Set up ownership radio buttons
                if not hasattr(comp_data, 'ownership_var'):
                    comp_data.ownership_var = tk.StringVar()
                
                # Get ownership status - capital components use 'component_blueprints' config key
                ownership_status = get_blueprint_ownership(self.blueprint_config, 'component_blueprints', comp_name)
                if ownership_status:
                    comp_data.ownership_var.set("owned")
                else:
                    comp_data.ownership_var.set("unowned")
                
                # Unowned radio button
                ttk.Radiobutton(
                    grid_frame, 
                    value="unowned", 
                    variable=comp_data.ownership_var,
                    command=lambda n=comp_name, d=comp_data, v="unowned": self.update_cap_component_ownership(n, d, v)
                ).grid(row=row, column=1, padx=5, pady=2)
                
                # Owned radio button
                ttk.Radiobutton(
                    grid_frame, 
                    value="owned", 
                    variable=comp_data.ownership_var,
                    command=lambda n=comp_name, d=comp_data, v="owned": self.update_cap_component_ownership(n, d, v)
                ).grid(row=row, column=2, padx=5, pady=2)
                
                # ME% input field
                if not hasattr(comp_data, 'me_var'):
                    comp_data.me_var = tk.StringVar()
                me_value = get_blueprint_me(self.blueprint_config, 'component_blueprints', comp_name)
                comp_data.me_var.set(str(me_value))
                me_entry = ttk.Entry(grid_frame, width=4, textvariable=comp_data.me_var)
                me_entry.grid(row=row, column=3, padx=5, pady=2)
                me_entry.bind("<FocusOut>", lambda event, n=comp_name: self.validate_capital_component_me(event, n))
                
                # TE% input field
                if not hasattr(comp_data, 'te_var'):
                    comp_data.te_var = tk.StringVar()
                te_value = get_blueprint_te(self.blueprint_config, 'component_blueprints', comp_name)
                comp_data.te_var.set(str(te_value))
                te_entry = ttk.Entry(grid_frame, width=4, textvariable=comp_data.te_var)
                te_entry.grid(row=row, column=4, padx=5, pady=2)
                te_entry.bind("<FocusOut>", lambda event, n=comp_name: self.validate_capital_component_te(event, n))
                
                row += 1
        
        # Configure the canvas to adjust scrolling based on the grid size
        grid_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        
        # Display message if no components found
        if not has_components:
            ttk.Label(components_container, text="No component modules discovered").pack(padx=10, pady=5)
    
    def create_ship_blueprint_grid(self, parent):
        """Create a grid for ship blueprints"""
        if 'ships' in self.discovered_modules or 'capital_ships' in self.discovered_modules:
            self.create_blueprint_grid(parent, "Ships", self.get_combined_ships_dict())
        else:
            ttk.Label(parent, text="No ship modules discovered.").pack(padx=10, pady=10)
    
    def create_blueprint_grid(self, parent, modules_type, modules_dict):
        """Create a grid view for blueprint management"""
        # Container with scrollbar
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Add filter frame at the top
        filter_frame = ttk.Frame(container)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create filter options - Ship Type and Faction
        ttk.Label(filter_frame, text="Ship Type:").grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")
        ship_type_var = tk.StringVar(value="All")
        ship_types = ["All"]
        
        # Faction filter
        ttk.Label(filter_frame, text="Faction:").grid(row=0, column=2, padx=(15, 5), pady=5, sticky="w")
        faction_var = tk.StringVar(value="All")
        factions = ["All"]
        
        # Extract available ship types and factions
        for module_name, module in modules_dict.items():
            # Extract ship type
            if hasattr(module, 'ship_type') and module.ship_type not in ship_types:
                ship_types.append(module.ship_type)
            
            # Extract faction
            if hasattr(module, 'faction') and module.faction not in factions:
                factions.append(module.faction)
        
        # Create dropdown menus
        ship_type_dropdown = ttk.Combobox(filter_frame, textvariable=ship_type_var, values=ship_types, state="readonly", width=20)
        ship_type_dropdown.grid(row=0, column=1, padx=0, pady=5, sticky="w")
        
        faction_dropdown = ttk.Combobox(filter_frame, textvariable=faction_var, values=factions, state="readonly", width=20)
        faction_dropdown.grid(row=0, column=3, padx=0, pady=5, sticky="w")
        
        # Create a search button
        apply_filter_btn = ttk.Button(filter_frame, text="Apply Filter", 
                                     command=lambda: self.populate_grid(grid_frame, modules_type, modules_dict, ship_type_var.get(), faction_var.get()))
        apply_filter_btn.grid(row=0, column=4, padx=15, pady=5)
        
        # Reset button
        reset_filter_btn = ttk.Button(filter_frame, text="Reset", 
                                    command=lambda: self.reset_filter(ship_type_dropdown, faction_dropdown, grid_frame, modules_type, modules_dict))
        reset_filter_btn.grid(row=0, column=5, padx=5, pady=5)
        
        # Add canvas and scrollbar
        canvas_frame = ttk.Frame(container)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
        
        # Configure scrollbars
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.configure(yscrollcommand=scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Create frame for grid
        grid_frame = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=grid_frame, anchor="nw")
        
        # Add headers
        ttk.Label(grid_frame, text=f"{modules_type} Blueprint", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(grid_frame, text="Ship Type", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(grid_frame, text="Faction", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(grid_frame, text="Unowned", font=("Arial", 10, "bold")).grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(grid_frame, text="Owned", font=("Arial", 10, "bold")).grid(row=0, column=4, padx=5, pady=5)
        ttk.Label(grid_frame, text="ME%", font=("Arial", 10, "bold")).grid(row=0, column=5, padx=5, pady=5)
        ttk.Label(grid_frame, text="TE%", font=("Arial", 10, "bold")).grid(row=0, column=6, padx=5, pady=5)
        
        # Separator
        separator = ttk.Separator(grid_frame, orient='horizontal')
        separator.grid(row=1, column=0, columnspan=7, sticky="ew", padx=5, pady=2)
        
        # Populate the grid
        self.populate_grid(grid_frame, modules_type, modules_dict)
        
        # Configure the canvas
        def _configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Set min width to avoid shrinking
            canvas.itemconfig(canvas_window, width=max(event.width, grid_frame.winfo_reqwidth()))
        
        grid_frame.bind("<Configure>", _configure_canvas)
        canvas.bind("<Configure>", _configure_canvas)
        
    def create_component_blueprint_grid(self, parent):
        """Create a grid for component blueprints"""
        if 'components' in self.discovered_modules:
            self.create_component_blueprint_grid_without_filters(parent, "Components", self.discovered_modules['components'])
        else:
            ttk.Label(parent, text="No component modules discovered.").pack(padx=10, pady=10)
    
    def create_component_blueprint_grid_without_filters(self, parent, modules_type, modules_dict):
        """Create a grid view for blueprint management without ship filters"""
        # Container with scrollbar
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create a canvas with scrollbar
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create frame for grid
        grid_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=grid_frame, anchor="nw")
        
        # Add headers
        ttk.Label(grid_frame, text="Component Blueprint", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(grid_frame, text="Unowned", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(grid_frame, text="Owned", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(grid_frame, text="ME%", font=("Arial", 10, "bold")).grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(grid_frame, text="TE%", font=("Arial", 10, "bold")).grid(row=0, column=4, padx=5, pady=5)
        
        # Add separator
        separator = ttk.Separator(grid_frame, orient='horizontal')
        separator.grid(row=1, column=0, columnspan=5, sticky="ew", pady=5)
        
        # Populate grid with components
        row = 2
        for comp_name, comp_data in sorted(modules_dict.items()):
            # Component name
            ttk.Label(grid_frame, text=comp_data.display_name).grid(row=row, column=0, padx=5, pady=2, sticky="w")
            
            # Ownership RadioButtons
            # Check if the comp_data already has an ownership_var attribute, if not create one
            if not hasattr(comp_data, 'ownership_var'):
                # Get ownership value from blueprint config
                ownership_status = get_blueprint_ownership(self.blueprint_config, 'components', comp_name)
                # Convert to lowercase to match the values expected by our radio buttons
                ownership_value = "owned" if ownership_status == "Owned" else "unowned"
                comp_data.ownership_var = tk.StringVar(value=ownership_value)
            
            # Unowned radiobutton
            ttk.Radiobutton(
                grid_frame, 
                value="unowned", 
                variable=comp_data.ownership_var,
                command=lambda n=comp_name, v="unowned": update_blueprint_ownership(self.blueprint_config, 'components', n, v)
            ).grid(row=row, column=1, padx=5, pady=2)
            
            # Owned radiobutton
            ttk.Radiobutton(
                grid_frame, 
                value="owned", 
                variable=comp_data.ownership_var,
                command=lambda n=comp_name, v="owned": update_blueprint_ownership(self.blueprint_config, 'components', n, v)
            ).grid(row=row, column=2, padx=5, pady=2)
            
            # ME% input field
            if not hasattr(comp_data, 'me_var'):
                comp_data.me_var = tk.StringVar()
            me_value = get_blueprint_me(self.blueprint_config, 'components', comp_name)
            comp_data.me_var.set(str(me_value))
            me_entry = ttk.Entry(grid_frame, width=4, textvariable=comp_data.me_var)
            me_entry.grid(row=row, column=3, padx=5, pady=2)
            me_entry.bind("<FocusOut>", lambda event, n=comp_name: self.validate_me(event, 'components', n))
            
            # TE% input field
            if not hasattr(comp_data, 'te_var'):
                comp_data.te_var = tk.StringVar()
            te_value = get_blueprint_te(self.blueprint_config, 'components', comp_name)
            comp_data.te_var.set(str(te_value))
            te_entry = ttk.Entry(grid_frame, width=4, textvariable=comp_data.te_var)
            te_entry.grid(row=row, column=4, padx=5, pady=2)
            te_entry.bind("<FocusOut>", lambda event, n=comp_name: self.validate_te(event, 'components', n))
            
            row += 1
        
        # Configure the canvas to adjust scrolling based on the grid size
        grid_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
    
    def create_capital_component_blueprint_grid(self, parent_tab):
        """Create a grid for capital component blueprints"""
        # Create a frame with scrollbar
        frame = ttk.Frame(parent_tab)
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create scrollable canvas
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create a frame for grid contents
        grid_frame = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=grid_frame, anchor="nw")
        
        # Add headers
        ttk.Label(grid_frame, text="Capital Component Blueprint", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(grid_frame, text="Unowned", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(grid_frame, text="Owned", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(grid_frame, text="ME%", font=("Arial", 10, "bold")).grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(grid_frame, text="TE%", font=("Arial", 10, "bold")).grid(row=0, column=4, padx=5, pady=5)
        
        # Add separator
        separator = ttk.Separator(grid_frame, orient='horizontal')
        separator.grid(row=1, column=0, columnspan=5, sticky="ew", pady=5)
        
        # Populate grid with capital component blueprints
        row = 2
        if 'capital_components' in self.discovered_modules:
            for comp_name, comp_data in sorted(self.discovered_modules['capital_components'].items()):
                # Display name
                ttk.Label(grid_frame, text=comp_data.display_name).grid(row=row, column=0, padx=5, pady=2, sticky="w")
                
                # Create ownership variable if it doesn't exist
                if not hasattr(comp_data, 'ownership_var'):
                    # Get ownership value from blueprint config
                    ownership_status = get_blueprint_ownership(self.blueprint_config, 'component_blueprints', comp_name)
                    # Convert to lowercase to match the values expected by our radio buttons
                    ownership_value = "owned" if ownership_status == "Owned" else "unowned"
                    comp_data.ownership_var = tk.StringVar(value=ownership_value)
                
                # Unowned radiobutton
                ttk.Radiobutton(
                    grid_frame, 
                    value="unowned", 
                    variable=comp_data.ownership_var,
                    command=lambda n=comp_name, d=comp_data, v="unowned": self.update_cap_component_ownership(n, d, v)
                ).grid(row=row, column=1, padx=5, pady=2)
                
                # Owned radiobutton
                ttk.Radiobutton(
                    grid_frame, 
                    value="owned", 
                    variable=comp_data.ownership_var,
                    command=lambda n=comp_name, d=comp_data, v="owned": self.update_cap_component_ownership(n, d, v)
                ).grid(row=row, column=2, padx=5, pady=2)
                
                # ME% input field
                if not hasattr(comp_data, 'me_var'):
                    comp_data.me_var = tk.StringVar()
                me_value = get_blueprint_me(self.blueprint_config, 'component_blueprints', comp_name)
                comp_data.me_var.set(str(me_value))
                me_entry = ttk.Entry(grid_frame, width=4, textvariable=comp_data.me_var)
                me_entry.grid(row=row, column=3, padx=5, pady=2)
                me_entry.bind("<FocusOut>", lambda event, n=comp_name: self.validate_capital_component_me(event, n))
                
                # TE% input field
                if not hasattr(comp_data, 'te_var'):
                    comp_data.te_var = tk.StringVar()
                te_value = get_blueprint_te(self.blueprint_config, 'component_blueprints', comp_name)
                comp_data.te_var.set(str(te_value))
                te_entry = ttk.Entry(grid_frame, width=4, textvariable=comp_data.te_var)
                te_entry.grid(row=row, column=4, padx=5, pady=2)
                te_entry.bind("<FocusOut>", lambda event, n=comp_name: self.validate_capital_component_te(event, n))
                
                row += 1
        
        # Configure the canvas to adjust scrolling based on the grid size
        grid_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        
        # Make sure the canvas size changes with window size
        def _configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=event.width)
            
        frame.bind("<Configure>", _configure_canvas)
    
    def populate_grid(self, grid_frame, modules_type, modules_dict, ship_type_filter="All", faction_filter="All"):
        """Populate the grid with modules that match the filter criteria"""
        # Clear existing grid content (except headers and separator)
        for widget in grid_frame.winfo_children():
            grid_info = widget.grid_info()
            if grid_info and int(grid_info['row']) > 1:  # Skip headers and separator
                widget.destroy()
        
        # For clarity on UI - show message if empty
        if len(modules_dict) == 0:
            empty_label = ttk.Label(grid_frame, text=f"No {modules_type} found. Module dictionary is empty.")
            empty_label.grid(row=2, column=0, columnspan=7, padx=5, pady=5, sticky="w")
            return
        
        row = 2
        module_count = 0
        
        # Get category for config lookup based on module type
        config_category = self.get_category_from_module_type(modules_type)
        
        debug_print(f"Populating grid for {modules_type}, config category: {config_category}")
        
        # Iterate through modules and add to grid if they match filter criteria
        for module_name, module in sorted(modules_dict.items(), key=lambda x: x[1].display_name):
            # Apply ship type filter
            if ship_type_filter != "All" and hasattr(module, 'ship_type') and module.ship_type != ship_type_filter:
                continue
                
            # Apply faction filter
            if faction_filter != "All" and hasattr(module, 'faction') and module.faction != faction_filter:
                continue
            
            # Display module name
            ttk.Label(grid_frame, text=module.display_name).grid(row=row, column=0, padx=5, pady=2, sticky="w")
            
            # Display ship type if available
            if hasattr(module, 'ship_type'):
                ttk.Label(grid_frame, text=module.ship_type).grid(row=row, column=1, padx=5, pady=2)
            else:
                ttk.Label(grid_frame, text="N/A").grid(row=row, column=1, padx=5, pady=2)
                
            # Display faction if available
            if hasattr(module, 'faction'):
                ttk.Label(grid_frame, text=module.faction).grid(row=row, column=2, padx=5, pady=2)
            else:
                ttk.Label(grid_frame, text="N/A").grid(row=row, column=2, padx=5, pady=2)
                
            # Create ownership variable if it doesn't exist
            if not hasattr(module, 'ownership_var'):
                module.ownership_var = tk.StringVar()
            
            # For ships tab, need to determine correct category based on ship type
            category_for_module = config_category
            if modules_type == "Ships" and hasattr(module, 'is_capital_ship') and module.is_capital_ship:
                category_for_module = "capital_ship_blueprints"
            
            # Get ownership status with the correct category
            ownership = get_blueprint_ownership(self.blueprint_config, category_for_module, module_name)
            
            debug_print(f"Module {module_name} - Config category: {category_for_module} - Status: {ownership}")
            
            # Set the correct radio button based on ownership
            if ownership == "Owned":
                module.ownership_var.set("owned")
                debug_print(f"Setting {module_name} radio to 'owned'")
            else:
                module.ownership_var.set("unowned")
                debug_print(f"Setting {module_name} radio to 'unowned'")
            
            # Store the correct category with the module for later use
            module.config_category = category_for_module
            
            # Unowned radio button
            ttk.Radiobutton(
                grid_frame, 
                value="unowned", 
                variable=module.ownership_var,
                command=lambda n=module_name, m=module, v="unowned": self.update_ownership(n, m.config_category, v)
            ).grid(row=row, column=3, padx=5, pady=2)
            
            # Owned radio button
            ttk.Radiobutton(
                grid_frame, 
                value="owned", 
                variable=module.ownership_var,
                command=lambda n=module_name, m=module, v="owned": self.update_ownership(n, m.config_category, v)
            ).grid(row=row, column=4, padx=5, pady=2)
            
            # ME% input field
            if not hasattr(module, 'me_var'):
                module.me_var = tk.StringVar()
                
            me_value = get_blueprint_me(self.blueprint_config, category_for_module, module_name)
            module.me_var.set(str(me_value))
            
            me_entry = ttk.Entry(grid_frame, width=4, textvariable=module.me_var)
            me_entry.grid(row=row, column=5, padx=5, pady=2)
            me_entry.bind("<FocusOut>", lambda event, n=module_name, c=category_for_module: self.validate_me(event, c, n))
            
            # TE% input field
            if not hasattr(module, 'te_var'):
                module.te_var = tk.StringVar()
                
            te_value = get_blueprint_te(self.blueprint_config, category_for_module, module_name)
            module.te_var.set(str(te_value))
            
            te_entry = ttk.Entry(grid_frame, width=4, textvariable=module.te_var)
            te_entry.grid(row=row, column=6, padx=5, pady=2)
            te_entry.bind("<FocusOut>", lambda event, n=module_name, c=category_for_module: self.validate_te(event, c, n))
            
            row += 1
            module_count += 1
        
        if module_count == 0:
            # No modules match the filter criteria
            empty_label = ttk.Label(grid_frame, text=f"No {modules_type} match the selected filters.")
            empty_label.grid(row=2, column=0, columnspan=7, padx=5, pady=5, sticky="w")
            
        # Update grid frame to recalculate size
        grid_frame.update_idletasks()
    
    def apply_filter(self, grid_frame, modules_dict, ship_type_filter, faction_filter):
        """Apply filter to the blueprint grid"""
        # Get the modules_type from grid_frame's master window title
        parent = grid_frame.master.master.master  # Canvas > Frame > Container
        modules_type = None
        for item in parent.winfo_children():
            if isinstance(item, ttk.LabelFrame):
                modules_type = item.cget("text").replace(" Blueprints", "")
                break
        
        if modules_type:
            self.populate_grid(grid_frame, modules_type, modules_dict, ship_type_filter, faction_filter)
        
    def reset_filter(self, ship_type_dropdown, faction_dropdown, grid_frame, modules_type, modules_dict):
        """Reset filters to show all modules"""
        ship_type_dropdown.set("All")
        faction_dropdown.set("All")
        self.populate_grid(grid_frame, modules_type, modules_dict)
            
    def get_category_from_module_type(self, module_type):
        """
        Convert module type string to config category key
        
        Args:
            module_type: String name of module type (e.g., 'Ships', 'Capital Ships')
            
        Returns:
            Category key for the blueprint config (e.g., 'ship_blueprints', 'capital_ship_blueprints')
        """
        category_mapping = {
            "Ships": "ship_blueprints",
            "Capital Ships": "capital_ship_blueprints",
            "Components": "components",
            "Capital Components": "component_blueprints"
        }
        
        return category_mapping.get(module_type, module_type.lower())
        
    def validate_me_entry(self, module):
        """
        Validate ME% entry to ensure it's a valid number
        
        Args:
            module: Module with ME% entry to validate
        """
        try:
            # Get ME% value
            me_value = int(module.me_var.get())
            
            # Validate ME% (0-10 is typical range in EVE)
            if me_value < 0:
                me_value = 0
            elif me_value > 10:
                me_value = 10
                
            # Set validated value
            module.me_var.set(str(me_value))
            
            # Get the category for this module
            for category_type, modules in self.discovered_modules.items():
                if module in modules.values():
                    category = self.get_category_from_module_type(category_type)
                    module_name = next(name for name, mod in modules.items() if mod == module)
                    update_blueprint_me(self.blueprint_config, category, module_name, me_value)
                    break
            
        except ValueError:
            # Reset to 0 if invalid
            module.me_var.set("0")
    
    def validate_te_entry(self, module):
        """
        Validate TE% entry to ensure it's a valid number
        
        Args:
            module: Module with TE% entry to validate
        """
        try:
            # Get TE% value
            te_value = int(module.te_var.get())
            
            # Validate TE% (0-20 is typical range in EVE)
            if te_value < 0:
                te_value = 0
            elif te_value > 20:
                te_value = 20
                
            # Set validated value
            module.te_var.set(str(te_value))
            
            # Get the category for this module
            for category_type, modules in self.discovered_modules.items():
                if module in modules.values():
                    category = self.get_category_from_module_type(category_type)
                    module_name = next(name for name, mod in modules.items() if mod == module)
                    update_blueprint_te(self.blueprint_config, category, module_name, te_value)
                    break
            
        except ValueError:
            # Reset to 0 if invalid
            module.te_var.set("0")
    
    def validate_capital_component_me(self, event, comp_name):
        """
        Validate ME% entry for capital components
        
        Args:
            event: FocusOut event
            comp_name: Name of the capital component
        """
        try:
            # Get ME% value from the entry widget
            me_entry = event.widget
            me_value = int(me_entry.get())
            
            # Validate ME% (0-10 is typical range in EVE)
            if me_value < 0:
                me_value = 0
            elif me_value > 10:
                me_value = 10
                
            # Set validated value
            me_entry.delete(0, tk.END)
            me_entry.insert(0, str(me_value))
            
            # Update blueprint config
            update_blueprint_me(self.blueprint_config, 'component_blueprints', comp_name, me_value)
            
        except ValueError:
            # Reset to 0 if invalid
            me_entry.delete(0, tk.END)
            me_entry.insert(0, "0")
    
    def validate_capital_component_te(self, event, comp_name):
        """
        Validate TE% entry for capital components
        
        Args:
            event: FocusOut event
            comp_name: Name of the capital component
        """
        try:
            # Get TE% value from the entry widget
            te_entry = event.widget
            te_value = int(te_entry.get())
            
            # Validate TE% (0-20 is typical range in EVE)
            if te_value < 0:
                te_value = 0
            elif te_value > 20:
                te_value = 20
                
            # Set validated value
            te_entry.delete(0, tk.END)
            te_entry.insert(0, str(te_value))
            
            # Update blueprint config
            update_blueprint_te(self.blueprint_config, 'component_blueprints', comp_name, te_value)
            
        except ValueError:
            # Reset to 0 if invalid
            te_entry.delete(0, tk.END)
            te_entry.insert(0, "0")
    
    def create_blueprint_window(self, blueprint_window):
        """Create the blueprint management window interface"""
        # Configure the window size (800x600)
        blueprint_window.geometry("800x600")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(blueprint_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tab for Ships
        if 'ships' in self.discovered_modules or 'capital_ships' in self.discovered_modules:
            ships_tab = ttk.Frame(notebook)
            notebook.add(ships_tab, text="Ships")
            
            self.create_blueprint_grid(
                ships_tab, 
                "Ships",
                self.get_combined_ships_dict()
            )
            
        # Create tab for Components
        if 'components' in self.discovered_modules or 'capital_components' in self.discovered_modules:
            components_tab = ttk.Frame(notebook)
            notebook.add(components_tab, text="Components")
            
            self.create_combined_components_blueprint_tab(components_tab)
            
        # Create status display
        status_frame = ttk.Frame(blueprint_window)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Status label
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=5)
        
        # Create button frame at the bottom
        button_frame = ttk.Frame(blueprint_window)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        
        # Save button
        save_button = ttk.Button(
            button_frame, 
            text="Save Changes", 
            command=self.save_blueprint_changes
        )
        save_button.pack(side=tk.RIGHT, padx=5)
        
        # Also save when the window is closed
        blueprint_window.protocol("WM_DELETE_WINDOW", lambda: self.on_close(blueprint_window))
        
    def on_close(self, window):
        """Handle window closing - ensure changes are saved"""
        # Save changes before closing
        self.save_blueprint_changes()
        
        # Destroy the window
        window.destroy()
        
    def save_blueprint_changes(self):
        """Save all blueprint changes to the config file"""
        try:
            # First, update the configuration with all changes
            self.update_all_ownership_values()
            
            # Import the function directly here to avoid any import issues
            from core.config.blueprint_config import save_blueprint_ownership
            
            # Save the configuration directly
            result = save_blueprint_ownership(self.blueprint_config)
            
            if result:
                self.status_var.set("Blueprint ownership settings saved successfully")
                
                # Apply ownership settings to the registry to ensure they take effect immediately
                from core.config.blueprint_config import apply_blueprint_ownership
                
                # Apply updated ownership to the module registry
                apply_blueprint_ownership(self.blueprint_config, self.module_registry)
                
            else:
                self.status_var.set("Error: Failed to save blueprint settings")
                
        except Exception as e:
            error_msg = f"Error saving blueprint configuration: {str(e)}"
            self.status_var.set(error_msg)
    
    def show_blueprint_grid(self):
        """Show blueprint management in a popup window"""
        blueprint_window = tk.Toplevel(self.parent)
        blueprint_window.title("Blueprint Management")
        blueprint_window.geometry("800x600")
        
        # Create the blueprint window interface
        self.create_blueprint_window(blueprint_window)
        
        # Apply the current theme to the window
        if hasattr(self.parent, 'settings') and 'theme' in self.parent.settings:
            self.apply_theme(blueprint_window, self.parent.settings.get('theme', 'light'))
        
        # Ensure the window protocol is set to handle closing
        blueprint_window.protocol("WM_DELETE_WINDOW", lambda: self.on_close(blueprint_window))
        
        # Force a refresh of all UI elements to ensure they reflect the current config
        debug_print("Initial refresh of blueprint window UI elements")
        self.refresh_registry_if_needed(initial_load=True)
        
        # Update the window to force refresh of all elements
        blueprint_window.update_idletasks()
        
    def update_all_ownership_values(self):
        """Update all ownership values in the blueprint config"""
        # Update ownership status for all modules
        for category_name, modules in self.discovered_modules.items():
            category = self.get_category_from_module_type(category_name)
            
            # Skip empty categories
            if not category or not modules:
                continue
            
            for module_name, module in modules.items():
                # Special handling for capital components
                if category_name == 'capital_components':
                    if hasattr(module, 'ownership_var'):
                        try:
                            ownership_status = module.ownership_var.get()
                            is_owned = (ownership_status == "owned")
                            
                            # Make sure the category exists
                            if 'component_blueprints' not in self.blueprint_config:
                                self.blueprint_config['component_blueprints'] = {}
                            
                            # Create or update entry
                            if module_name not in self.blueprint_config['component_blueprints']:
                                self.blueprint_config['component_blueprints'][module_name] = {
                                    'owned': is_owned,
                                    'invented': False,  # Components cannot be invented
                                    'me': 0,
                                    'te': 0
                                }
                            else:
                                # Update existing entry
                                self.blueprint_config['component_blueprints'][module_name]['owned'] = is_owned
                        except Exception as e:
                            pass
                
                # Ships, Capital Ships, and Components
                elif hasattr(module, 'ownership_var'):
                    try:
                        # Get the ownership status from the UI variable
                        var_value = module.ownership_var.get()
                        is_owned = (var_value == "owned")
                        
                        invented_var = getattr(module, 'invented_var', None)
                        is_invented = invented_var.get() if invented_var else False
                        
                        me_var = getattr(module, 'me_var', None)
                        me_value = int(me_var.get()) if me_var and me_var.get().isdigit() else 0
                        
                        te_var = getattr(module, 'te_var', None)
                        te_value = int(te_var.get()) if te_var and te_var.get().isdigit() else 0
                        
                        # Make sure the category exists
                        if category not in self.blueprint_config:
                            self.blueprint_config[category] = {}
                        
                        # Create or update entry
                        if module_name not in self.blueprint_config[category]:
                            self.blueprint_config[category][module_name] = {
                                'owned': is_owned,
                                'invented': is_invented,
                                'me': me_value,
                                'te': te_value
                            }
                        else:
                            # Update existing entry
                            current_value = self.blueprint_config[category][module_name].get('owned', False)
                            self.blueprint_config[category][module_name]['owned'] = is_owned
                            self.blueprint_config[category][module_name]['invented'] = is_invented
                            self.blueprint_config[category][module_name]['me'] = me_value
                            self.blueprint_config[category][module_name]['te'] = te_value
                            if current_value != is_owned:
                                pass
                    except Exception as e:
                        pass
        
        # Save ME% values for all modules including capital components
        for category_name, modules in self.discovered_modules.items():
            category = self.get_category_from_module_type(category_name)
            for module_name, module in modules.items():
                if hasattr(module, 'me_var'):
                    try:
                        me_value = int(module.me_var.get())
                        # Ensure ME is not negative
                        if me_value < 0:
                            me_value = 0
                            module.me_var.set("0")
                        
                        # Special handling for capital components
                        if category_name == 'capital_components':
                            if 'component_blueprints' not in self.blueprint_config:
                                self.blueprint_config['component_blueprints'] = {}
                            if module_name not in self.blueprint_config['component_blueprints']:
                                self.blueprint_config['component_blueprints'][module_name] = {
                                    'owned': False,
                                    'invented': False,
                                    'me': me_value,
                                    'te': 0
                                }
                            else:
                                self.blueprint_config['component_blueprints'][module_name]['me'] = me_value
                        else:
                            # Update the ME in config
                            update_blueprint_me(self.blueprint_config, category, module_name, me_value)
                    except ValueError:
                        # Invalid ME value, set to 0
                        module.me_var.set("0")
                        if category_name == 'capital_components':
                            if 'component_blueprints' in self.blueprint_config and module_name in self.blueprint_config['component_blueprints']:
                                self.blueprint_config['component_blueprints'][module_name]['me'] = 0
                        else:
                            update_blueprint_me(self.blueprint_config, category, module_name, 0)
            
        # Save TE% values for all modules including capital components
        for category_name, modules in self.discovered_modules.items():
            category = self.get_category_from_module_type(category_name)
            for module_name, module in modules.items():
                if hasattr(module, 'te_var'):
                    try:
                        te_value = int(module.te_var.get())
                        # Ensure TE is not negative
                        if te_value < 0:
                            te_value = 0
                            module.te_var.set("0")
                        
                        # Special handling for capital components
                        if category_name == 'capital_components':
                            if 'component_blueprints' not in self.blueprint_config:
                                self.blueprint_config['component_blueprints'] = {}
                            if module_name not in self.blueprint_config['component_blueprints']:
                                self.blueprint_config['component_blueprints'][module_name] = {
                                    'owned': False,
                                    'invented': False,
                                    'me': 0,
                                    'te': te_value
                                }
                            else:
                                self.blueprint_config['component_blueprints'][module_name]['te'] = te_value
                        else:
                            # Update the TE in config
                            update_blueprint_te(self.blueprint_config, category, module_name, te_value)
                    except ValueError:
                        # Invalid TE value, set to 0
                        module.te_var.set("0")
                        if category_name == 'capital_components':
                            if 'component_blueprints' in self.blueprint_config and module_name in self.blueprint_config['component_blueprints']:
                                self.blueprint_config['component_blueprints'][module_name]['te'] = 0
                        else:
                            update_blueprint_te(self.blueprint_config, category, module_name, 0)
        
        # Save the configuration
        success = save_blueprint_ownership(self.blueprint_config)
        
        if success:
            self.status_var.set("Blueprint configuration saved successfully")
            return True
        else:
            self.status_var.set("Error saving blueprint configuration")
            return False
                
    def reset_all_ship_ownership(self):
        """Reset ownership status for all ships and capital ships"""
        try:
            # Reset ships
            if hasattr(self.module_registry, 'ships'):
                for ship_name, ship in self.module_registry.ships.items():
                    if hasattr(ship, 'owned_status'):
                        ship.owned_status = False
                        
                    # Also update the blueprint config
                    if 'ship_blueprints' in self.blueprint_config and ship_name in self.blueprint_config['ship_blueprints']:
                        self.blueprint_config['ship_blueprints'][ship_name]['owned'] = False
            
            # Reset capital ships
            if hasattr(self.module_registry, 'capital_ships'):
                for ship_name, ship in self.module_registry.capital_ships.items():
                    if hasattr(ship, 'owned_status'):
                        ship.owned_status = False
                        
                    # Also update the blueprint config
                    if 'capital_ship_blueprints' in self.blueprint_config and ship_name in self.blueprint_config['capital_ship_blueprints']:
                        self.blueprint_config['capital_ship_blueprints'][ship_name]['owned'] = False
            
            # Save the updated configuration
            from core.config.blueprint_config import save_blueprint_ownership
            success = save_blueprint_ownership(self.blueprint_config)
            
            if success:
                self.status_var.set("All ship ownership has been reset")
                return True
            else:
                self.status_var.set("Error: Failed to save reset changes")
                return False
                
        except Exception as e:
            error_msg = f"Error resetting ship ownership: {str(e)}"
            self.status_var.set(error_msg)
            return False
            
    def update_ownership(self, module_name, category, value):
        """Update the ownership status and save to config"""
        # Convert "owned"/"unowned" string to proper format for config
        ownership_value = "Owned" if value == "owned" else "Unowned"
        
        # Update the blueprint configuration
        update_blueprint_ownership(self.blueprint_config, category, module_name, ownership_value)
        
        # Refresh the module registry if required
        self.refresh_registry_if_needed()
        
    def update_module_ownership(self, module_name, module, value, module_type):
        """Update module ownership based on the module type"""
        # Determine what type of module this is and use the appropriate update method
        if hasattr(module, 'ship_type'): # This is a ship (regular or capital)
            self.update_ship_ownership(module_name, module, value)
        elif module_type == "Components":
            self.update_component_ownership(module_name, module, value)
        elif module_type == "Capital Components":
            self.update_cap_component_ownership(module_name, module, value)
        else:
            # Generic fallback using the correct category from module type
            category = self.get_category_from_module_type(module_type)
            # Convert from UI value (owned/unowned) to config value (Owned/Unowned)
            config_value = "Owned" if value == "owned" else "Unowned"
            # Update in config
            update_blueprint_ownership(self.blueprint_config, category, module_name, config_value)
            # Update module state
            module.owned_status = (config_value == "Owned")
            # Update status
            self.status_var.set(f"Updated {module.display_name} ownership to {config_value}")
        
    def update_ship_ownership(self, module_name, module, value):
        """Update ship blueprint ownership in configuration"""
        # For ships tab, determine if this is a regular ship or a capital ship
        if hasattr(module, 'is_capital_ship') and module.is_capital_ship:
            category = "capital_ship_blueprints"
        else:
            category = "ship_blueprints"
            
        # Convert from UI value (owned/unowned) to config value (Owned/Unowned)
        config_value = "Owned" if value == "owned" else "Unowned"
        
        # Update in config
        update_blueprint_ownership(self.blueprint_config, category, module_name, config_value)
        
        # Update module state
        module.owned_status = (config_value == "Owned")
        
        # Update status
        self.status_var.set(f"Updated {module.display_name} ownership to {config_value}")

    def update_component_ownership(self, module_name, module, value):
        """Update component blueprint ownership in configuration"""
        # Convert from UI value (owned/unowned) to config value (Owned/Unowned)
        config_value = "Owned" if value == "owned" else "Unowned"
        
        # Update in config
        update_blueprint_ownership(self.blueprint_config, 'components', module_name, config_value)
        
        # Update module state
        module.owned_status = (config_value == "Owned")
        
        # Update status
        self.status_var.set(f"Updated {module.display_name} ownership to {config_value}")

    def update_cap_component_ownership(self, module_name, module, value):
        """Update capital component blueprint ownership in configuration"""
        # Convert from UI value (owned/unowned) to config value (Owned/Unowned)
        config_value = "Owned" if value == "owned" else "Unowned"
        
        # Update in config
        update_blueprint_ownership(self.blueprint_config, 'component_blueprints', module_name, config_value)
        
        # Update module state
        module.owned_status = (config_value == "Owned")
        
        # Update status
        self.status_var.set(f"Updated {module.display_name} ownership to {config_value}")

    def validate_me(self, event, category, module_name):
        """Validate and update ME% value"""
        entry_widget = event.widget
        value = entry_widget.get()
        
        try:
            # Validate as a number between 0 and 10
            me_value = int(value)
            if me_value < 0:
                me_value = 0
            elif me_value > 10:
                me_value = 10
                
            # Update the entry with validated value
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, str(me_value))
            
            # Update the config
            update_blueprint_me(self.blueprint_config, category, module_name, me_value)
            
        except ValueError:
            # Reset to 0 if invalid
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, "0")
            update_blueprint_me(self.blueprint_config, category, module_name, 0)
            
        # Update GUI if needed
        self.refresh_registry_if_needed()
            
    def validate_te(self, event, category, module_name):
        """Validate and update TE% value"""
        entry_widget = event.widget
        value = entry_widget.get()
        
        try:
            # Validate as a number between 0 and 20
            te_value = int(value)
            if te_value < 0:
                te_value = 0
            elif te_value > 20:
                te_value = 20
                
            # Update the entry with validated value
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, str(te_value))
            
            # Update the config
            update_blueprint_te(self.blueprint_config, category, module_name, te_value)
            
        except ValueError:
            # Reset to 0 if invalid
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, "0")
            update_blueprint_te(self.blueprint_config, category, module_name, 0)
            
        # Update GUI if needed
        self.refresh_registry_if_needed()
        
    def refresh_registry_if_needed(self, initial_load=False):
        """Refresh the module registry if it's available"""
        if hasattr(self, 'module_registry') and self.module_registry:
            debug_print("Refreshing module registry and UI elements")
            
            # Apply blueprint config to the registry objects only on initial load
            if initial_load:
                if hasattr(self.module_registry, 'ships'):
                    for ship_name, ship in self.module_registry.ships.items():
                        if 'ship_blueprints' in self.blueprint_config and ship_name in self.blueprint_config['ship_blueprints']:
                            ship.owned_status = self.blueprint_config['ship_blueprints'][ship_name].get('owned', False)
                            debug_print(f"Updated registry ship {ship_name} to owned_status={ship.owned_status}")
                
                if hasattr(self.module_registry, 'capital_ships'):
                    for ship_name, ship in self.module_registry.capital_ships.items():
                        if 'capital_ship_blueprints' in self.blueprint_config and ship_name in self.blueprint_config['capital_ship_blueprints']:
                            ship.owned_status = self.blueprint_config['capital_ship_blueprints'][ship_name].get('owned', False)
                            debug_print(f"Updated registry capital ship {ship_name} to owned_status={ship.owned_status}")
            
            # Also update objects in discovered_modules to match config on initial load
            # This ensures the UI elements (like radio buttons) show the correct state
            for category_name, modules in self.discovered_modules.items():
                config_category = self.get_category_from_module_type(category_name)
                
                for module_name, module in modules.items():
                    if config_category in self.blueprint_config and module_name in self.blueprint_config[config_category]:
                        is_owned = self.blueprint_config[config_category][module_name].get('owned', False)
                        
                        # Update module object ownership attribute
                        if hasattr(module, 'owned_status'):
                            module.owned_status = is_owned
                        elif hasattr(module, 'blueprint_owned'):
                            module.blueprint_owned = is_owned
                        
                        # Update UI StringVar only on initial load
                        if initial_load and hasattr(module, 'ownership_var'):
                            ownership_value = "owned" if is_owned else "unowned"
                            if module.ownership_var.get() != ownership_value:
                                debug_print(f"Updating UI element for {module_name}, setting ownership_var from {module.ownership_var.get()} to {ownership_value}")
                                module.ownership_var.set(ownership_value)

    def get_combined_ships_dict(self):
        """Get a combined dictionary of ships and capital ships"""
        combined_dict = {}
        
        if 'ships' in self.discovered_modules:
            combined_dict.update(self.discovered_modules['ships'])
        
        if 'capital_ships' in self.discovered_modules:
            combined_dict.update(self.discovered_modules['capital_ships'])
        
        return combined_dict

    def apply_theme(self, window, theme):
        """Apply the selected theme to the blueprint window
        
        Args:
            window: The window to apply the theme to
            theme: The theme to apply ('light' or 'dark')
        """
        if theme == "dark":
            window.config(bg="#2e2e2e")
            style = ttk.Style(window)
            style.theme_use('clam')  # Use clam as base
            
            # Configure the dark theme
            style.configure("TFrame", background="#2e2e2e")
            style.configure("TLabel", background="#2e2e2e", foreground="#ffffff")
            style.configure("TButton", background="#3c3c3c", foreground="#ffffff")
            style.configure("TNotebook", background="#2e2e2e", foreground="#ffffff")
            style.configure("TNotebook.Tab", background="#3c3c3c", foreground="#ffffff")
            style.map("TNotebook.Tab",
                background=[("selected", "#4c4c4c"), ("active", "#3c3c3c")],
                foreground=[("selected", "#ffffff"), ("active", "#ffffff")])
            
            # Configure the LabelFrame
            style.configure("TLabelframe", background="#2e2e2e", foreground="#ffffff")
            style.configure("TLabelframe.Label", background="#2e2e2e", foreground="#ffffff")
            
            # Configure the Radiobuttons with proper contrast
            style.configure("TRadiobutton", background="#2e2e2e", foreground="#ffffff")
            
            # Configure the Entry with proper contrast
            style.configure("TEntry", fieldbackground="#3c3c3c", foreground="#ffffff")
            
            # Configure the Spinbox with proper contrast
            style.configure("TSpinbox", fieldbackground="#3c3c3c", foreground="#ffffff")
        else:
            # Reset to default theme
            style = ttk.Style(window)
            style.theme_use('default')
