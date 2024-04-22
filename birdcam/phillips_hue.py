from phue import Bridge
import time
import threading

b = Bridge('192.168.0.156')

# If the app is not registered and the button is not pressed, press the button and call connect() (this only needs to be run a single time)
b.connect()

# Get the bridge state (This returns the full dictionary that you can explore)
bridge_state = b.get_api()

# Get a dictionary with the light name as the key
light_names = b.get_light_objects('name')
print(light_names)

# Get all groups configured on the bridge
groups = b.get_group()

print("Groups on the bridge:")
for group_id, group_info in groups.items():
    print("Group ID:", group_id)
    print("Group Name:", group_info['name'])
    print("Group Type:", group_info['type'])
    print("Group Lights:", group_info['lights'])
    print()

# Get all scenes configured on the bridge
scenes = b.get_scene()

print("Scenes on the bridge:")
for scene_id, scene_info in scenes.items():
    print("Scene ID:", scene_id)
    print("Scene Name:", scene_info['name'])
    print("Scene Lights:", scene_info['lights'])
    print()

countertop_lights = b.get_light('Countertop Lights')
print(countertop_lights)
office_light1 = ['Office Fan 1']

def setLights(bird, lights):
    global lights_state
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

#Test setting lights function
setLights('Cyanocitta cristata (Blue Jay)', countertop_lights)
