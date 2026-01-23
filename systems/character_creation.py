"""Character creation module - handles the entire character creation flow."""

class CharacterCreation:
    """Handles all character creation logic."""
    
    def __init__(self, formatter, races, planets, starsigns, maneuvers):
        self.formatter = formatter
        self.races = races
        self.planets = planets
        self.starsigns = starsigns
        self.maneuvers = maneuvers
    
    def welcome(self, player):
        """Start character creation process for new players"""
        self.formatter.send_to_player(player, f"""
{self.formatter.format_header('=== CHARACTER CREATION ===')}
Welcome to Tyrant of the Dark Skies!

First, choose your race (affects attributes and starting skills):

""")
        for race_id, race in self.races.items():
            if 'color' in race:
                race_display = f"{self.formatter.format_brackets(race_id.upper(), race['color'])}: {race['description']}"
            else:
                race_display = f"[{race_id.upper()}]: {race['description']}"
            self.formatter.send_to_player(player, race_display)
            
        self.formatter.send_to_player(player, f"\nType {self.formatter.format_command('race <name>')} to choose your race.")
        player.creation_state = "choosing_race"
    
    def handle_race_choice(self, player, race_name):
        """Handle race selection during character creation"""
        race_name = race_name.lower()
        if race_name not in self.races:
            available_races = ", ".join([self.formatter.format_brackets(r.upper(), self.races[r]['color']) for r in self.races.keys()])
            self.formatter.send_to_player(player, f"Unknown race. Choose from: {available_races}")
            return
            
        player.race = race_name
        race = self.races[race_name]
        
        # Apply racial attribute modifiers
        for attr, modifier in race["attribute_modifiers"].items():
            player.attributes[attr] = 10 + modifier
            
        # Apply free points for humans
        player.free_attribute_points = race.get("free_points", 0)
        
        # Apply racial starting skills
        for skill, value in race["starting_skills"].items():
            if skill in player.skills:
                player.skills[skill] = max(player.skills[skill], value)
        
        # Flow: Race -> (if human, assign points) -> Planet -> Starsign -> Maneuver
        if player.free_attribute_points > 0:
            # Human with free points - need to assign them first
            self.formatter.send_to_player(player, f"\n{self.formatter.format_header('Assign Attribute Points:')}")
            self.formatter.send_to_player(player, f"You have {player.free_attribute_points} free attribute points to assign.")
            self.formatter.send_to_player(player, f"Current attributes: {player.attributes}")
            self.formatter.send_to_player(player, f"Type {self.formatter.format_command('assign <attribute>')} to add a point to an attribute.")
            self.formatter.send_to_player(player, f"Available attributes: physical, mental, spiritual, social")
            player.creation_state = "assigning_points"
        else:
            # Non-human or no free points - go straight to planet selection
            self.show_planet_selection(player)
    
    def handle_attribute_assignment(self, player, attribute_name):
        """Handle attribute point assignment during character creation"""
        attribute_name = attribute_name.lower()
        valid_attributes = ["physical", "mental", "spiritual", "social"]
        
        if attribute_name not in valid_attributes:
            self.formatter.send_to_player(player, f"Invalid attribute. Choose from: {', '.join(valid_attributes)}")
            return
        
        if player.free_attribute_points <= 0:
            self.formatter.send_to_player(player, "You have no free points remaining.")
            return
        
        # Add point to attribute
        player.attributes[attribute_name] += 1
        player.free_attribute_points -= 1
        
        self.formatter.send_to_player(player, f"Added 1 point to {attribute_name}. New value: {player.attributes[attribute_name]}")
        self.formatter.send_to_player(player, f"Remaining free points: {player.free_attribute_points}")
        
        if player.free_attribute_points > 0:
            self.formatter.send_to_player(player, f"Type {self.formatter.format_command('assign <attribute>')} to assign another point.")
        else:
            self.formatter.send_to_player(player, f"\nAll points assigned! Moving to planet selection...")
            self.show_planet_selection(player)
            player.creation_state = "choosing_planet"
    
    def show_planet_selection(self, player):
        """Show available planets for selection"""
        self.formatter.send_to_player(player, f"""
{self.formatter.format_header('Choose Your Planet:')}
Your planet represents cosmic guardianship and destiny. Planets are permanent and shape your character's 
style of play from level 1 onward. Each planet grants one starting maneuver, provides a passive effect 
that scales by tier, and offers attribute bonuses and starting skills.

""")

        for planet_id, planet in self.planets.items():
            if 'color' in planet:
                planet_display = f"{self.formatter.format_brackets(planet_id.upper(), planet['color'])}: {planet['name']}"
            else:
                planet_display = f"[{planet_id.upper()}]: {planet['name']}"
            self.formatter.send_to_player(player, planet_display)
            self.formatter.send_to_player(player, f"  Theme: {planet['theme']}")
            
            if "cosmic_role" in planet:
                self.formatter.send_to_player(player, f"  Cosmic Role: {planet['cosmic_role']}")
            
            if "description" in planet:
                self.formatter.send_to_player(player, f"  {planet['description']}")
            
            if "attribute_bonuses" in planet:
                bonuses = planet["attribute_bonuses"]
                bonus_list = []
                for attr, value in bonuses.items():
                    if value > 0:
                        bonus_list.append(f"+{value} {attr.capitalize()}")
                if bonus_list:
                    self.formatter.send_to_player(player, f"  Attribute Bonuses: {', '.join(bonus_list)}")
            
            if "passive_effect" in planet:
                self.formatter.send_to_player(player, f"  {self.formatter.format_header('Passive Effect:')} {planet['passive_effect']}")
                if "passive_description" in planet:
                    self.formatter.send_to_player(player, f"    {planet['passive_description']}")
            
            if "gift_maneuver" in planet:
                self.formatter.send_to_player(player, f"  Gift Maneuver: {planet['gift_maneuver']}")
            
            self.formatter.send_to_player(player, "")
        
        self.formatter.send_to_player(player, f"\nType {self.formatter.format_command('planet <name>')} to choose your planet.")
        player.creation_state = "choosing_planet"
    
    def handle_planet_choice(self, player, planet_name):
        """Handle planet selection during character creation"""
        planet_name = planet_name.lower()
        if planet_name not in self.planets:
            available_planets = ", ".join([self.formatter.format_brackets(p.upper(), self.planets[p].get('color', 'cyan')) for p in self.planets.keys()])
            self.formatter.send_to_player(player, f"Unknown planet. Choose from: {available_planets}")
            return
            
        player.planet = planet_name
        planet = self.planets[planet_name]
        
        # Apply planet attribute bonuses
        if "attribute_bonuses" in planet:
            for attr, bonus in planet["attribute_bonuses"].items():
                player.attributes[attr] += bonus
        
        # Apply planet starting skills
        if "starting_skills" in planet:
            for skill, value in planet["starting_skills"].items():
                if skill in player.skills:
                    player.skills[skill] = max(player.skills[skill], value)
                else:
                    player.skills[skill] = value
        
        # Store gift maneuver
        if "gift_maneuver" in planet:
            player.gift_maneuver = planet["gift_maneuver"]
            if player.gift_maneuver not in player.known_maneuvers:
                player.known_maneuvers.append(player.gift_maneuver)
            if player.gift_maneuver not in player.active_maneuvers:
                player.active_maneuvers.append(player.gift_maneuver)
        
        self.formatter.send_to_player(player, f"\nYou chose {self.formatter.format_header(planet['name'])}!")
        self.formatter.send_to_player(player, f"Theme: {planet['theme']}")
        if "attribute_bonuses" in planet:
            self.formatter.send_to_player(player, f"Attribute bonuses: {planet['attribute_bonuses']}")
        if "passive_effect" in planet:
            self.formatter.send_to_player(player, f"Passive effect: {planet['passive_effect']}")
        if "gift_maneuver" in planet:
            self.formatter.send_to_player(player, f"Gift maneuver: {planet['gift_maneuver']}")
        
        # Flow: Planet -> Starsign
        self.show_starsign_selection(player)
        player.creation_state = "choosing_starsign"
    
    def show_starsign_selection(self, player):
        """Show available starsigns for selection"""
        self.formatter.send_to_player(player, f"""
{self.formatter.format_header('Choose Your Starsign:')}
Your starsign represents fate at birth. Star Signs are permanent, always active, and focused on fate, 
temperament, and narrative flavor. Each provides +2 to one attribute, -1 to another, and a Fated Mark.

""")

        for starsign_id, starsign in self.starsigns.items():
            if 'color' in starsign:
                starsign_display = f"{self.formatter.format_brackets(starsign_id.upper(), starsign['color'])}: {starsign['name']}"
            else:
                starsign_display = f"[{starsign_id.upper()}]: {starsign['name']}"
            self.formatter.send_to_player(player, starsign_display)
            self.formatter.send_to_player(player, f"  Theme: {starsign['theme']}")
            
            if "description" in starsign:
                self.formatter.send_to_player(player, f"  {starsign['description']}")
            
            if "attribute_modifiers" in starsign:
                mods = starsign["attribute_modifiers"]
                mod_list = []
                for attr, value in mods.items():
                    if value > 0:
                        mod_list.append(f"+{value} {attr.capitalize()}")
                    elif value < 0:
                        mod_list.append(f"{value} {attr.capitalize()}")
                if mod_list:
                    self.formatter.send_to_player(player, f"  Attributes: {', '.join(mod_list)}")
            
            if "fated_mark" in starsign:
                fated_mark = starsign["fated_mark"]
                if "name" in fated_mark:
                    self.formatter.send_to_player(player, f"  {self.formatter.format_header('Fated Mark:')} {fated_mark['name']}")
                if "description" in fated_mark:
                    self.formatter.send_to_player(player, f"    {fated_mark['description']}")
            
            self.formatter.send_to_player(player, "")
        
        self.formatter.send_to_player(player, f"\nType {self.formatter.format_command('starsign <name>')} to choose your starsign.")
        player.creation_state = "choosing_starsign"
    
    def handle_starsign_choice(self, player, starsign_name):
        """Handle starsign selection during character creation"""
        starsign_name = starsign_name.lower()
        if starsign_name not in self.starsigns:
            available_starsigns = ", ".join([self.formatter.format_brackets(s.upper(), self.starsigns[s]['color']) for s in self.starsigns.keys()])
            self.formatter.send_to_player(player, f"Unknown starsign. Choose from: {available_starsigns}")
            return
            
        player.starsign = starsign_name
        starsign = self.starsigns[starsign_name]
        
        # Apply starsign attribute modifiers
        for attr, modifier in starsign["attribute_modifiers"].items():
            player.attributes[attr] += modifier
            
        # Store fated mark
        player.fated_mark = starsign.get("fated_mark", {})
        
        self.formatter.send_to_player(player, f"\nYou chose {self.formatter.format_header(starsign['name'])}!")
        self.formatter.send_to_player(player, f"Theme: {starsign['theme']}")
        self.formatter.send_to_player(player, f"Attribute modifiers: {starsign['attribute_modifiers']}")
        
        if "fated_mark" in starsign:
            fated_mark_desc = starsign["fated_mark"]["description"]
            self.formatter.send_to_player(player, f"\n{self.formatter.format_header('Fated Mark:')}")
            self.formatter.send_to_player(player, f"{fated_mark_desc}")
        
        # Flow: Starsign -> Maneuver
        self.show_starting_maneuvers(player)
        player.creation_state = "choosing_maneuver"
    
    def show_starting_maneuvers(self, player):
        """Show available starting maneuvers"""
        self.formatter.send_to_player(player, f"\n{self.formatter.format_header('Choose Your Starting Maneuver:')}")
        self.formatter.send_to_player(player, f"You already have the gift maneuver from your planet: {player.gift_maneuver}")
        self.formatter.send_to_player(player, "Choose one additional starting maneuver:")
        
        gift_maneuver = self.planets[player.planet].get("gift_maneuver", "")
        available_count = 0
        
        for maneuver_id, maneuver in self.maneuvers.items():
            if maneuver_id == gift_maneuver:
                continue
            
            tier = maneuver.get("tier", "").lower()
            if tier not in ["lower", "low"]:
                continue
            
            required_level = maneuver.get("required_level", 1)
            if required_level > 1:
                continue
            
            required_race = maneuver.get("required_race")
            if required_race and player.race != required_race:
                continue
            
            can_learn = True
            if "required_skills" in maneuver and maneuver["required_skills"]:
                for skill, required in maneuver["required_skills"].items():
                    if player.skills.get(skill, 0) < required:
                        can_learn = False
                        break
            
            if can_learn:
                available_count += 1
                maneuver_name = maneuver.get('name', maneuver_id)
                maneuver_desc = maneuver.get('description', 'No description')
                
                race_note = ""
                if required_race:
                    race_note = f" [{required_race.capitalize()} only]"
                
                skill_note = ""
                if "required_skills" in maneuver and maneuver["required_skills"]:
                    skill_reqs = ", ".join([f"{s} {r}" for s, r in maneuver["required_skills"].items()])
                    skill_note = f" (Requires: {skill_reqs})"
                
                self.formatter.send_to_player(player, f"  {maneuver_id}: {maneuver_name}{race_note}{skill_note}")
                self.formatter.send_to_player(player, f"    {maneuver_desc}")
                    
        if available_count == 0:
            self.formatter.send_to_player(player, "  No additional maneuvers available. Defaulting to shield_bash.")
            self.formatter.send_to_player(player, "  shield_bash: Shield Bash - Bash with shield to stagger")
            
        self.formatter.send_to_player(player, f"\nType {self.formatter.format_command('maneuver <name>')} to choose your starting maneuver.")
    
    def handle_maneuver_choice(self, player, maneuver_name, get_room_func, save_player_func, look_command_func):
        """Handle maneuver selection during character creation"""
        maneuver_name = maneuver_name.lower()
        
        if maneuver_name not in self.maneuvers:
            available_maneuvers = []
            for man_id, maneuver in self.maneuvers.items():
                if maneuver.get("tier", "").lower() in ["lower", "low"] and man_id not in player.known_maneuvers:
                    available_maneuvers.append(f"{maneuver.get('name', man_id)} ({man_id})")
            
            if available_maneuvers:
                maneuvers_list = ", ".join(available_maneuvers)
                self.formatter.send_to_player(player, f"Available maneuvers: {maneuvers_list}")
            else:
                self.formatter.send_to_player(player, "No available maneuvers remaining.")
            return
            
        maneuver = self.maneuvers[maneuver_name]
        
        if maneuver.get("tier", "").lower() not in ["lower", "low"]:
            self.formatter.send_to_player(player, "You can only choose Lower tier maneuvers at character creation.")
            return
            
        if "required_skills" in maneuver:
            for skill, required in maneuver["required_skills"].items():
                if player.skills.get(skill, 0) < required:
                    self.formatter.send_to_player(player, f"You need {skill} {required} to learn this maneuver.")
                    return
                
        if maneuver_name in player.known_maneuvers:
            self.formatter.send_to_player(player, "You already know this maneuver from your planet gift.")
            return
            
        player.known_maneuvers.append(maneuver_name)
        player.active_maneuvers.append(maneuver_name)
        
        # Show character summary
        self.formatter.send_to_player(player, f"\n{self.formatter.format_header('=== CHARACTER COMPLETE ===')}")
        self.formatter.send_to_player(player, f"Name: {player.name}")
        self.formatter.send_to_player(player, f"Race: {self.races[player.race]['name']}")
        self.formatter.send_to_player(player, f"Planet: {self.planets[player.planet]['name']}")
        self.formatter.send_to_player(player, f"Tier: Low (Level 1)")
        self.formatter.send_to_player(player, f"Active Maneuvers: {', '.join(player.active_maneuvers)}")
        self.formatter.send_to_player(player, "\nYour adventure begins!")
        
        player.creation_state = "complete"
        
        # Place character in world
        room = get_room_func(player.room_id)
        if room:
            room.players.add(player.name)
            
        save_player_func(player)
        look_command_func(player, [])
