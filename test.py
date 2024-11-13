from collections import defaultdict, deque

mods = [
    {"id": 1, "name": "MainMod", "requirements": [2, 3], "patches": [4], "add_id": {"A"}, "override_id": {"C"}},
    {"id": 2, "name": "RequirementMod1", "requirements": [], "patches": [], "add_id": {"B"}, "override_id": set()},
    {"id": 3, "name": "RequirementMod2", "requirements": [], "patches": [], "add_id": set(), "override_id": {"A"}},
    {"id": 4, "name": "PatchMod1", "requirements": [1], "patches": [], "add_id": set(), "override_id": {"D"}},
    {"id": 5, "name": "ZZZIndependentMod", "requirements": [], "patches": [], "add_id": {"E"}, "override_id": set()},
]

id_to_name = {mod["id"]: mod["name"] for mod in mods}
name_to_id = {mod["name"]: mod["id"] for mod in mods}

dependency_graph = defaultdict(list)
in_degree = defaultdict(int)

for mod in mods:
    for patch_id in mod["patches"]:
        dependency_graph[patch_id].append(mod["id"])
        in_degree[mod["id"]] += 1

    for requirement_id in mod["requirements"]:
        dependency_graph[mod["id"]].append(requirement_id)
        in_degree[requirement_id] += 1

add_to_override_dependencies = defaultdict(set)
for mod in mods:
    for add_id in mod["add_id"]:
        for other_mod in mods:
            if add_id in other_mod["override_id"]:
                dependency_graph[mod["id"]].append(other_mod["id"])
                in_degree[other_mod["id"]] += 1

queue = deque(
    sorted(
        [mod["id"] for mod in mods if in_degree[mod["id"]] == 0],
        key=lambda id_: id_to_name[id_]
    )
)
sorted_mods = []

while queue:
    current_id = queue.popleft()
    sorted_mods.append(current_id)
    for neighbor_id in sorted(dependency_graph[current_id], key=lambda id_: id_to_name[id_]):
        in_degree[neighbor_id] -= 1
        if in_degree[neighbor_id] == 0:
            queue.append(neighbor_id)

for mod_id in sorted_mods:
    print(f"{id_to_name[mod_id]} (id: {mod_id})")
