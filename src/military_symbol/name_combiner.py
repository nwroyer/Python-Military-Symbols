import re

FIRST = ["PSYOP", "psychological operations", "military information support operations", "MISO"]
SECOND = ['broadcast transmitter antenna', 'broadcast transmitter antennae']
swappable:bool = True

if True: #__name__ == '__main__':
	first = [f for f in FIRST]
	second = [f for f in SECOND]

	for (item_set, new_set) in [(FIRST, first), (SECOND, second)]:
		for item in item_set:
			if '-' in item:
				new_set.append(re.sub(r'\-', '', item))
				new_set.append(re.sub(r' ', '', item))

	results = []
	for item_1 in first:
		for item_2 in second:
			results.append(f'{item_1} {item_2}')
			if swappable:
				results.append(f'{item_2} {item_1}')

	results = list(set([re.sub(r'\s+', ' ', i).strip() for i in results]))
	
	print('[' + ', '.join([f'"{item}"' for item in results]) + '],')