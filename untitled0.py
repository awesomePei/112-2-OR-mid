import csv
import gurobipy as gp
from gurobipy import GRB

# Define the path to your CSV file
csv_file_path = 'instance05.csv'

# Initialize a list to store the job IDs
job_ids = []
stage1_pts = []
stage2_pts = []
stage1_ms = []
stage2_ms = []
due_times = []

# Open the CSV file in read mode
with open(csv_file_path, 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader)
    # Iterate over each row in the CSV file to retrieve the data
    for row in csvreader:
        # Access the "Job ID" column using its index and append the value to the list
        job_id = int(row[0])
        job_ids.append(job_id)
        stage1_pt = row[1]
        stage1_pts.append(stage1_pt)
        stage2_pt = row[2]
        stage2_pts.append(stage2_pt)
        stage1_m = row[3]
        stage1_ms.append(stage1_m)
        stage2_m = row[4]
        stage2_ms.append(stage2_m)
        due_time = int(row[5])
        due_times.append(due_time)
        
n = len(job_ids)
stage1_ms_int = [[int(num) for num in sublist.split(',')] for sublist in stage1_ms]
stage2_ms_int = [[int(num) for num in sublist.split(',')] if sublist != 'N/A' else [] for sublist in stage2_ms]

# Combine the two lists
combined_list = stage1_ms_int + stage2_ms_int
flattened_list = [item for sublist in combined_list for item in sublist]
# Find the largest number
machine_num = max(flattened_list)
# Find how many machines there are
#machine_num = max(combined_list)

# Create a model
model = gp.Model('job_scheduling')
# Create variables
t = model.addVars(range(1, n+1), name='t')
c = model.addVars(range(1, n+1), range(1, 3), name='c')
x = model.addVars(range(1, n+1), range(1, 3), machine_num, vtype=GRB.BINARY, name='x')
y = model.addVars(range(1, n+1), range(1, 3), range(1, n+1), range(1, 3), machine_num, vtype=GRB.BINARY, name='y')
# Set objective
model.setObjective(sum(t[j] for j in job_ids), sense=GRB.MINIMIZE)
# Constraints
# Constraint 1: Total tardiness
model.addConstr(gp.quicksum(t[j] for j in job_ids) == gp.quicksum(due_times[j-1] for j in job_ids), name="constraint1")

# Constraint 2: Tardiness of job j
for j in job_ids:
    if stage2_pts[j - 1] == 0:
        model.addConstr(t[j] >= c[j, 1] - due_times[j - 1], name=f'constraint2-1-{j}')
    else:
        model.addConstr(t[j] >= c[j, 2] - due_times[j - 1], name=f'constraint2-2-{j}')

# Constraint 3: Non-negativity of tardiness
model.addConstrs((t[j] >= 0 for j in job_ids), name="constraint3")

# Constraint 4: Tardiness difference between stages
model.addConstrs((c[j, 2] - c[j, 1] - float(stage2_pts[j-1]) <= 1 for j in job_ids), name="constraint4")

# Constraint 5: Tardiness difference non-negativity
model.addConstrs((c[j, 2] - c[j, 1] - float(stage2_pts[j-1]) >= 0 for j in job_ids), name="constraint5")

# Constraint 6: Completion time difference
L = int(100000)
for j in job_ids:
    for i in range(1, machine_num + 1):
        if i in stage1_ms_int[j - 1] or i in stage2_ms_int[j - 1]:
            for l in job_ids:
                for k in [1, 2]:
                    for h in [1, 2]:
                        model.addConstrs(c[j, k] + float(stage2_pts[l-1]) - c[l, h] <= L * (1 - y[j, k, l, h, i]), name='constraint6-1')
        else:
            for l in job_ids:
                for k in [1, 2]:
                    for h in [1, 2]:
                        model.addConstrs(y[j, k, l, h, i] <= 10000000, name='constraint6-2')
                        
            
#model.addConstrs((c[j, k] + stage2_pts[l-1] - c[l, h] <= L * (1 - y[j, k, l, h, i]) 
#                  for i in stage1_ms_int[j] for j in job_ids for l in job_ids for k in [1, 2] for h in [1, 2]), name="constraint6-1")             
#model.addConstrs((c[j, k] + stage2_pts[l-1] - c[l, h] <= L * (1 - y[j, k, l, h, i]) 
#                  for i in stage2_ms_int[j] for j in job_ids for l in job_ids for k in [1, 2] for h in [1, 2]), name="constraint6-2")             
        
# Constraint 7: Assignment of jobs to machines
model.addConstrs((gp.quicksum(x[j, k, i] for i in stage1_ms[j-1]) == 1 for j in job_ids for k in [1, 2]), name="constraint7")

# Constraint 8: Machine availability
model.addConstrs((x[j, k, i] == 0 for i in range(1, machine_num+1) for j in job_ids for k in [1, 2] if i not in stage1_ms[j-1]), name="constraint8")

# Constraint 9: Conflict avoidance
model.addConstrs((x[j, k, i] + x[l, h, i] <= y[j, k, l, h, i] + y[l, h, j, k, i] + 1 
                  for i in range(1, machine_num+1) for j in job_ids for l in job_ids for k in [1, 2] for h in [1, 2]), name="constraint9")

# Constraint 10: Non-negativity of completion time
model.addConstrs((c[j, k] >= 0 for j in job_ids for k in [1, 2]), name="constraint10")

model.optimize()