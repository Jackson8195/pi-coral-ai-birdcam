from phue import Bridge
import time
import threading
from collections import Counter

b = Bridge('192.168.0.156')

# If the app is not registered and the button is not pressed, press the button and call connect() (this only needs to be run a single time)
b.connect()

# Get the bridge state (This returns the full dictionary that you can explore)
bridge_state = b.get_api()

hue_birds = [
    ['Cardinalis cardinalis (Northern Cardinal)', 0, 255, 255]
    ['Cyanocitta cristata (Blue Jay)', 45000, 255, 255]
]

def setLights(bird, lights, timer):
    global hue_visitors
    global hue_birds
    try:
        if not timer:
            hue_visitors.append(bird)
        else:
            # Count occurrences of each list element
            counter = Counter(hue_visitors)
            # Get the most common element over the timer duration and its count
            most_common_bird = counter.most_common(1)[0]
            if any(most_common_bird == entry[0] for entry in hue_birds):
                bird_lookup = [entry for entry in hue_birds if entry[0] == most_common_bird]
                b.set_light(lights, {'hue': bird_lookup[1], 'sat': bird_lookup[2], 'bri': bird_lookup[3]})
            #clear the list and reset the timer
            hue_visitors.clear()
            timer = False
    except Exception as e:
        print("An error occurred while setting lights:", e)

'''
    lights_state = 'no_bird,_detect'
    try:
        if bird == 'Cardinalis cardinalis (Northern Cardinal)':
            b.set_light(lights, {'hue': 0, 'sat': 255, 'bri': 255})
            print('Setting lights to Red for Cardinal')
            lights_state = "bird_detect"
        elif bird == 'Cyanocitta cristata (Blue Jay)':
            b.set_light(lights, {'hue': 45000, 'sat': 255, 'bri': 255})
            print('Setting lights to Blue for Blue Jay')
            lights_state = "bird_detect"
        else:
            if lights_state != 'no_bird_detect':
                b.run_scene('Kitchen','Concentrate',4)
                print('Setting lights back to Concentrate')
                lights_state = 'no_bird_detect'
    except Exception as e:
        print("An error occurred while setting lights:", e)
'''

if __name__ == "__main__":
    # Get a dictionary with the light name as the key
    light_names = b.get_light_objects('name')
    print(light_names)
    # Get all scenes configured on the bridge
    scenes = b.get_scene()
    print("Scenes on the bridge:")
    for scene_id, scene_info in scenes.items():
        print("Scene ID:", scene_id)
        print("Scene Name:", scene_info['name'])
        print("Scene Lights:", scene_info['lights'])
        print()
    # Get all groups configured on the bridge
    groups = b.get_group()
    print("Groups on the bridge:")
    for group_id, group_info in groups.items():
        print("Group ID:", group_id)
        print("Group Name:", group_info['name'])
        print("Group Type:", group_info['type'])
        print("Group Lights:", group_info['lights'])
        print()
    #Test setting lights function
    setLights('Cyanocitta cristata (Blue Jay)', 'Countertop Lights')
    pass