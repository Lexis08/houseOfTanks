import random

"""class Tank:
    def __int__(self):
        pv = 50

move = 'up'
tank = Tank()
print('GET', '/move?move=' + move + '&tank=', tank)"""

"""price_weapon = 300
weapon_name = 'Gun'
print(f'GET /buy_weapon?price_weapon={price_weapon}&weapon_name={weapon_name}')"""


class Tank:

    def __init__(self):
        self.test = 0


tid_to_tank_dict = {
    1: Tank(),
    2: Tank()
}

response = {
        "action": 0,
        "src_tid": 1,
        "target_tid": 2,
        "face": 0
    }

print("===> Receive shot tag result")
tank = tid_to_tank_dict[response['src_tid']]

# Verifie si target
if response['target_tid']:
    target_tank = tid_to_tank_dict[response['target_tid']]
    print('target tank :', target_tank)
else:
    print('no target')
