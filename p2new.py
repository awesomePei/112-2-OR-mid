import pandas as pd #type:ignore
from gurobipy import Model, GRB, quicksum #type:ignore

# Load and clean your data
data = pd.read_csv('/Users/cindychang/Documents/school/大二/OR/Mid/112-2-OR-mid/midterm/data/instance05.csv')

def parse_machine_list(machine_list):
    if pd.isna(machine_list):
        return []
    return list(map(int, machine_list.split(',')))

def fillNoMachines(machine_list, jobs, machines):
    for j in jobs:
        if len(machine_list[j-1]) == 0:
            machine_list[j-1] = machines


jobs = data['Job ID'].unique()


data['Stage-1 Machines'] = data['Stage-1 Machines'].apply(parse_machine_list)
data['Stage-2 Machines'] = data['Stage-2 Machines'].apply(parse_machine_list)

# set up all the machine's id
all_machines = set()
data['Stage-1 Machines'].apply(lambda machines: all_machines.update(machines))
data['Stage-2 Machines'].apply(lambda machines: all_machines.update(machines))

    

# Initialize the model
model = Model("Job_Scheduling")

# Extract jobs, machines, and assume stages and data are set

s1_machines = data['Stage-1 Machines'].tolist()
s2_machines = data['Stage-2 Machines'].tolist()

machines = list(set(sum(data['Stage-1 Machines'].tolist(), []) + sum(data['Stage-2 Machines'].tolist(), [])))


print(s2_machines)
fillNoMachines(s2_machines, jobs, machines)


# Add decision variables
s = model.addVars(jobs, [1, 2], name="s", vtype=GRB.CONTINUOUS, lb = 0.0)  # Start times
c = model.addVars(jobs, [1, 2], name="c", vtype=GRB.CONTINUOUS, lb = 0.0)  # Completion times
x = model.addVars(jobs, [1, 2], machines, name="x", vtype=GRB.BINARY)  # Machine assignment
T = model.addVars(jobs, name="T", vtype=GRB.CONTINUOUS, lb = 0.0)  # Tardiness
y = model.addVars(jobs, [1, 2], jobs, [1, 2], machines, name="y", vtype=GRB.BINARY) ##sequence of jobs stage


pt = [
    list(data['Stage-1 Processing Time'][:len(jobs)]),  # Stage-1 processing times
    list(data['Stage-2 Processing Time'][:len(jobs)])   # Stage-2 processing times
]


M = 1000

model.setObjective(quicksum(T[j] for j in jobs), GRB.MINIMIZE)

## 1. Tardiness
for j in jobs:
    d = data.loc[data['Job ID'] == j, 'Due Time'].values[0]
    model.addConstr(T[j] >= c[j, 2] - d)
    model.addConstr(T[j] >= 0)

## 2. Inter-process time
for j in jobs:
    model.addConstr(c[j, 2] - c[j, 1] - pt[1][j-1] <= 1)
    model.addConstr(c[j, 2] - c[j, 1] - pt[1][j-1] >= 0)


## 3. job 指派順序
for j in jobs:
    for k in [1, 2]:
        for l in jobs:
            for h in [1, 2]:
                for i in machines:
                    if (j != l):
                        model.addConstr(c[j, k] + pt[h-1][l-1] - c[l, h] <= M*(1 - y[j, k, l, h, i]))
                        model.addConstr(x[j, k, i] + x[l, h, i] <= y[j, k, l, h, i] + y[l, h, j, k, i] + 1)

## 4. job 指派到 machine
for j in jobs:
    for k in [1, 2]:
        model.addConstr(quicksum(x[j, k, i] for i in machines) == 1)


for j in jobs:
    for i in machines:
        if i in s1_machines[j-1]:
            continue
        else:
            model.addConstr(x[j, 1, i] == 0)  

for j in jobs:
    for i in machines:
        if i in s2_machines[j-1]:
            continue
        else:
            model.addConstr(x[j, 2, i] == 0)           
        

## 5. completion time 天然限制
for j in jobs:
    model.addConstr(c[j, 1] >= pt[0][j-1])
    model.addConstr(c[j, 2] >= pt[0][j-1] + pt[1][j-1])


model.optimize()

if model.status == GRB.INFEASIBLE:
    print("Model is infeasible; computing IIS")
    model.computeIIS()
    model.write("model.ilp")

assigned_machine = 0


for j in jobs:
    for k in [1, 2]:
        for l in jobs:
            for h in [1, 2]:
                print(y[j,k,l,h,1])

for j in jobs:
    for k in [1, 2]:
        for i in machines:
            print(x[j, k, i])



if model.status == GRB.OPTIMAL:
    print(f"Total Tardiness: {model.objVal}")
    for j in jobs:
        print(f"Job {j} Tardiness: {T[j].X}")
        for stage in [1, 2]:
            for i in machines:
                if (round(x[j, stage, i].x) == 1):
                    assigned_machine = i
            print(f"Stage {stage} start time: {s[j, stage].X}, completion time: {c[j, stage].X}, assigned machine: {assigned_machine}")