import os
import json
from datetime import datetime

class MemoryEntry:
    def __init__(self, key, value, category="general"):
        self.key = key
        self.value = value
        self.category = category
        self.created = datetime.now().isoformat()
        self.last_used = self.created

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "category": self.category,
            "created": self.created,
            "last_used": self.last_used
        }

    @staticmethod
    def from_dict(data):
        entry = MemoryEntry(data["key"], data["value"], data.get("category", "general"))
        entry.created = data.get("created", datetime.now().isoformat())
        entry.last_used = data.get("last_used", entry.created)
        return entry

class NovaMemory:
    def __init__(self, path="nova_memory.json"):
        self.path = path
        self.memory = self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    data = json.load(f)
                    return {k: MemoryEntry.from_dict(v) for k, v in data.items()}
            except Exception:
                return {}
        return {}

    def save(self):
        try:
            with open(self.path, "w") as f:
                json.dump({k: v.to_dict() for k, v in self.memory.items()}, f, indent=2)
        except Exception as e:
            print(f"Error saving memory: {e}")

    def remember(self, key, value, category="general"):
        entry = MemoryEntry(key, value, category)
        self.memory[key] = entry
        self.save()

    def recall(self, key):
        entry = self.memory.get(key)
        if entry:
            entry.last_used = datetime.now().isoformat()
            self.save()
            return entry.value
        return None

    def forget(self, key):
        if key in self.memory:
            del self.memory[key]
            self.save()
            return True
        return False

    def list_all(self):
        return {k: v.to_dict() for k, v in self.memory.items()}

    def summary(self):
        return [f"{v.key}: {v.value}" for v in self.memory.values()]