import pandas as pd

data = pd.read_csv('/Users/cindychang/Documents/school/大二/OR/midterm/data/instance05.csv')  # Adjust the path accordingly

# machine id split to list
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

# Initialize machine availability for each machine ID
machine_availability = {machine: 0 for machine in all_machines}

# Sort jobs by urgency
data['Urgency'] = data['Due Time'] - (data['Stage-1 Processing Time'] + data['Stage-2 Processing Time'])
sorted_jobs = data.sort_values(by='Urgency')

# Assign jobs to machines
assignments = []
for index, job in sorted_jobs.iterrows():
    job_id = job['Job ID']
    stages = [
        (job['Stage-1 Processing Time'], job['Stage-1 Machines']),
        (job['Stage-2 Processing Time'], job['Stage-2 Machines']) if job['Stage-2 Processing Time'] > 0 else None
    ]

    job_schedule = {}
    for stage_index, stage in enumerate(stages):
        if stage is None or not stage[1]:  # Skip if no second stage or no machines available
            continue

        processing_time, machines = stage
        # Find the first available machine with earliest possible start time
        start_time = None
        assigned_machine = None
        for machine in machines:
            potential_start_time = max(machine_availability.get(machine, 0), job_schedule.get(stage_index - 1, (0, 0))[1])
            if assigned_machine is None or potential_start_time < start_time:
                start_time = potential_start_time
                assigned_machine = machine
        
        if assigned_machine is not None:
            end_time = start_time + processing_time
            machine_availability[assigned_machine] = end_time
            job_schedule[stage_index] = (start_time, end_time, assigned_machine)

    # Save the assigment
    assignments.append((job_id, job_schedule))
    
# Print out the complete schedule    
# print("Job Scheduling:")
# for job_id, schedule in assignments:
#     print(f"\nJob {job_id} Scheduling:")
#     if not schedule:
#         print("  No stages scheduled.")
#     for stage_index, (start_time, end_time, machine) in schedule.items():
#         print(f"  Stage {stage_index + 1}:")
#         print(f"    Machine Assigned: Machine {machine}")
#         print(f"    Start Time: {start_time}")
#         print(f"    End Time: {end_time}")

# Calculate tardiness for each job and print
total_tardiness = 0
for job_id, schedule in assignments:
    job_due_time = sorted_jobs.loc[sorted_jobs['Job ID'] == job_id, 'Due Time'].iloc[0]
    if schedule:
        last_stage_end_time = schedule[max(schedule.keys())][1]
    else:
        last_stage_end_time = 0  # Default to 0 if no stage was scheduled
    
    tardiness = max(0, last_stage_end_time - job_due_time)
    total_tardiness += tardiness
    # print(f"Job {job_id}: Ends at {last_stage_end_time}, Due {job_due_time}, Tardiness {tardiness}")

# print(f"Total Tardiness: {total_tardiness}")


#correct output format
machine_result = [[None, None] for _ in range(len(data))]
completion_time_result = [[None, None] for _ in range(len(data))]

for job_id, schedule in assignments:
    job_index = job_id - 1
    for stage_index, (start_time, end_time, machine_id) in schedule.items():
        machine_result[job_index][stage_index] = machine_id if machine_id is not None else -1
        completion_time_result[job_index][stage_index] = end_time

print(machine_result)
print(completion_time_result)