import random
import json

def load_templates(path="story_templates.json"):
    with open(path, "r") as f:
        return json.load(f)

# there are 3 intros for every emotional state. This function will decide witch one is to be used
def select_intro(templates, emotion):
    for template in templates:
        if template["emotion"] == emotion:
            return {
                "tone": template["tone"],
                "intention": template["intention"],
                "story_intro": random.choice(template["story_intros"])
            }
    return None
