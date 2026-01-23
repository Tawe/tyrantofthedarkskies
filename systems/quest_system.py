"""Quest and task system for EXP rewards."""

class Quest:
    """Represents a quest or task"""
    
    def __init__(self, quest_id, name, description):
        self.quest_id = quest_id
        self.name = name
        self.description = description
        self.exp_reward = 0
        self.objectives = []  # List of objective dicts
        self.completed = False
        self.progress = {}  # {objective_id: progress_value}
    
    def to_dict(self):
        return {
            "quest_id": self.quest_id,
            "name": self.name,
            "description": self.description,
            "exp_reward": self.exp_reward,
            "objectives": self.objectives,
            "completed": self.completed,
            "progress": self.progress
        }
    
    def from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def check_completion(self):
        """Check if all objectives are complete"""
        if not self.objectives:
            return False
        
        for objective in self.objectives:
            obj_id = objective.get("id")
            required = objective.get("required", 1)
            current = self.progress.get(obj_id, 0)
            if current < required:
                return False
        
        self.completed = True
        return True
    
    def update_progress(self, objective_id, amount=1):
        """Update progress on an objective"""
        if objective_id not in self.progress:
            self.progress[objective_id] = 0
        self.progress[objective_id] += amount
        
        # Check if quest is now complete
        return self.check_completion()


class QuestManager:
    """Manages quests for players"""
    
    def __init__(self):
        self.quests = {}  # {quest_id: Quest}
        self.player_quests = {}  # {player_name: [quest_id, ...]}
    
    def add_quest(self, quest):
        """Add a quest to the system"""
        self.quests[quest.quest_id] = quest
    
    def assign_quest(self, player_name, quest_id):
        """Assign a quest to a player"""
        if quest_id not in self.quests:
            return False
        
        if player_name not in self.player_quests:
            self.player_quests[player_name] = []
        
        if quest_id not in self.player_quests[player_name]:
            self.player_quests[player_name].append(quest_id)
        
        return True
    
    def get_player_quests(self, player_name):
        """Get all quests for a player"""
        if player_name not in self.player_quests:
            return []
        
        return [self.quests[qid] for qid in self.player_quests[player_name] if qid in self.quests]
    
    def update_quest_progress(self, player_name, objective_type, target_id=None, amount=1):
        """Update progress on quests matching an objective type"""
        if player_name not in self.player_quests:
            return []
        
        completed_quests = []
        for quest_id in self.player_quests[player_name]:
            quest = self.quests.get(quest_id)
            if not quest or quest.completed:
                continue
            
            # Check if any objective matches
            for objective in quest.objectives:
                if objective.get("type") == objective_type:
                    obj_id = objective.get("id")
                    if target_id is None or objective.get("target_id") == target_id:
                        if quest.update_progress(obj_id, amount):
                            completed_quests.append(quest)
                        break
        
        return completed_quests
