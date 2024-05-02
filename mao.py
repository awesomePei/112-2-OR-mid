import pandas as pd
import itertools as it
from gurobipy import Model, GRB, quicksum

# Load and clean your data
data = pd.read_csv('instance01.csv')

def parse_machine_list(machine_list):
    if pd.isna(machine_list):
        return []
    return list(map(int, machine_list.split(',')))

data['Stage-1 Machines'] = data['Stage-1 Machines'].apply(parse_machine_list)
data['Stage-2 Machines'] = data['Stage-2 Machines'].apply(parse_machine_list)

# set up all the machine's id
all_machines = set()
data['Stage-1 Machines'].apply(lambda machines: all_machines.update(machines))
data['Stage-2 Machines'].apply(lambda machines: all_machines.update(machines))

# Initialize the model
model = Model("Job_Scheduling")

# Extract jobs, machines, and assume stages and data are set
jobs = data['Job ID'].unique()
machines = set(sum(data['Stage-1 Machines'].tolist(), []) + sum(data['Stage-2 Machines'].tolist(), []))

# Define a large M
M = 10000000000

c = model.addVars(jobs, [1, 2], name = "c", vtype = GRB.CONTINUOUS, lb = 0.0)  # Completion times
x = model.addVars(jobs, [1, 2], machines, name = "x", vtype = GRB.BINARY)      # Machine assignment
y = model.addVars(jobs, [1, 2], jobs, [1, 2], machines, name = "y", vtype = GRB.BINARY)
T = model.addVars(jobs, name = "T", vtype = GRB.CONTINUOUS, lb = 0.0)          # Tardiness
w = model.addVar(name = "w", vtype = GRB.CONTINUOUS, lb = 0.0)                 # Makespan

# Objective function
model.setObjective(sum(T[j] for j in jobs), GRB.MINIMIZE)
# model.setObjective(w, GRB.MINIMIZE)

# 1. Job assignment for each stage
for j in jobs:
    # For stage 1:
    stage_1_machines = data.at[data.index[data['Job ID'] == j][0], 'Stage-1 Machines']
    # model.addConstr((x[j, 1, k] for k in machines if k not in stage_1_machines) == 0, name=f"Job_Assignment_Stage1_{j}_0")
    model.addConstr(quicksum(x[j, 1, k] for k in stage_1_machines) == 1, name=f"Job_Assignment_Stage1_{j}_1")
    model.addConstr(quicksum(x[j, 1, k] for k in machines) <= 1, name=f"Job_Assignment_Stage1_{j}_2")
    
    # For stage 2:
    stage_2_machines = data.at[data.index[data['Job ID'] == j][0], 'Stage-2 Machines']
    if stage_2_machines == []:
        model.addConstr(quicksum(x[j, 2, k] for k in machines) == 0, name=f"Job_Assignment_Stage2_{j}")
    else:
        # model.addConstr((x[j, 2, k] for k in machines if k not in stage_2_machines) == 0, name=f"Job_Assignment_Stage2_{j}_0")
        model.addConstr(quicksum(x[j, 2, k] for k in stage_2_machines) == 1, name=f"Job_Assignment_Stage2_{j}_1")
        model.addConstr(quicksum(x[j, 2, k] for k in machines) <= 1, name=f"Job_Assignment_Stage2_{j}_2")

# for i in machines:
#     for stage in [1, 2]:
#         model.addConstr(quicksum(x[j, stage, i] for j in jobs) <= 1)

# 2. Interprocess time constraint
for j in jobs:
    p1 = data.loc[data['Job ID'] == j, 'Stage-1 Processing Time'].values[0]
    p2 = data.loc[data['Job ID'] == j, 'Stage-2 Processing Time'].values[0]
    print(f"Job {j}: {p1}, {p2}")
    model.addConstr(c[j, 1] >= p1)
    model.addConstr(c[j, 2] - c[j, 1] - p2 <= 1)
    model.addConstr(c[j, 2] - c[j, 1] - p2 >= 0)
    # if p2 == 0:
    #    model.addConstr(c[j, 2] == c[j, 1])

# 3. Job order constraint

# for i in machines:
for j, l in it.combinations(jobs, 2):
    for k in [1, 2]:
        for h in [1, 2]:
            model.addConstrs((y[j, k, l, h, i] + y[l, h, j, k, i] <= 1) for i in machines)
            
for j in jobs:
    for i in machines:
        model.addConstrs((y[j, 1, j, 2, i] + y[j, 2, j, 1, i] <= 1) for i in machines)

for j, l in it.combinations(jobs, 2):
    # print(j, l);
    for i in machines:
        for k in [1, 2]:
            for h in [1, 2]:
                model.addConstr((x[j, k, i] + x[l, h, i] <= y[j, k, l, h, i] + y[l, k, j, h, i] + 1))
                # model.addConstr((x[j, 1, i] + x[l, 2, i] <= y[j, 1, l, 2, i] + y[l, 2, j, 1, i] + 1))
                # model.addConstr((x[j, 2, i] + x[l, 1, i] <= y[j, 2, l, 1, i] + y[l, 1, j, 2, i] + 1))
                # model.addConstr((x[j, 2, i] + x[l, 2, i] <= y[j, 2, l, 2, i] + y[l, 2, j, 2, i] + 1))
                
for j in jobs:
    for i in machines:
        model.addConstr(x[j, 1, i] + x[j, 2, i] <= y[j, 1, j, 2, i] + y[j, 2, j , 1, i] + 1)

for j, l in it.combinations(jobs, 2):
    p_l1 = data.loc[data['Job ID'] == l, 'Stage-1 Processing Time'].values[0]
    p_l2 = data.loc[data['Job ID'] == l, 'Stage-2 Processing Time'].values[0]
    # For j stage 1
    stage_1_machines = data.at[data.index[data['Job ID'] == j][0], 'Stage-1 Machines']
    for i in stage_1_machines:
        model.addConstr(c[j, 1] + p_l1 - c[l, 1] <= M*(1 - y[j, 1, l, 1, i]))
        model.addConstr(c[j, 1] + p_l2 - c[l, 2] <= M*(1 - y[j, 1, l, 2, i]))
    # For j stage 2
    stage_2_machines = data.at[data.index[data['Job ID'] == j][0], 'Stage-2 Machines']
    for i in stage_2_machines:
        model.addConstr(c[j, 2] + p_l1 - c[l, 1] <= M*(1 - y[j, 2, l, 1, i]))
        model.addConstr(c[j, 2] + p_l2 - c[l, 2] <= M*(1 - y[j, 2, l, 2, i]))
    
    p_j1 = data.loc[data['Job ID'] == j, 'Stage-1 Processing Time'].values[0]
    p_j2 = data.loc[data['Job ID'] == j, 'Stage-2 Processing Time'].values[0]
    # For l stage 1
    stage_1_machines = data.at[data.index[data['Job ID'] == l][0], 'Stage-1 Machines']
    for i in stage_1_machines:
        model.addConstr(c[l, 1] + p_j1 - c[j, 1] <= M*(1 - y[l, 1, j, 1, i]))
        model.addConstr(c[l, 1] + p_j2 - c[j, 2] <= M*(1 - y[l, 1, j, 2, i]))
    # For l stage 2
    stage_2_machines = data.at[data.index[data['Job ID'] == l][0], 'Stage-2 Machines']
    for i in stage_2_machines:
        model.addConstr(c[l, 2] + p_j1 - c[j, 1] <= M*(1 - y[l, 2, j, 1, i]))
        model.addConstr(c[l, 2] + p_j2 - c[j, 2] <= M*(1 - y[l, 2, j, 2, i]))

# 4. Tardiness calculation
for j in jobs:
    d = data.loc[data['Job ID'] == j, 'Due Time'].values[0]
    model.addConstr(T[j] >= c[j, 2] - d)
    model.addConstr(T[j] >= 0)

# 5. Makespan calculation
for j in jobs:
    model.addConstr(w >= c[j, 2])

# Optimize the model
model.optimize()

if model.status == GRB.INFEASIBLE:
    print("Model is infeasible; computing IIS")
    model.computeIIS()
    model.write("model.ilp")

total_t = 0
for j in jobs:
    total_t += T[j].X
if model.status == GRB.OPTIMAL:
    print(f"Total Tardiness: {model.objVal}")
    for j in jobs:
        print(f"Job {j} Tardiness: {T[j].X}")
        for stage in [1, 2]:
            print(f"Stage {stage} completion time: {c[j, stage].X}")
        print(f"Due time: {data.loc[data['Job ID'] == j, 'Due Time'].values[0]}")

for stage in range(1,2):
    for j in jobs:
        for k in machines:
            for stage in [1, 2]:
                if x[j, stage, k].X == 1:
                    print(f"Job {j} Stage {stage} in machine: {k}")

print("Makespan: ", w.X)
