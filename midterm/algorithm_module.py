from MTP_lib import *

def heuristic_algorithm(file_path):
    '''
    1. Write your heuristic algorithm here.
    2. We would call this function in grading_program.py to evaluate your algorithm.
    3. Please do not change the function name and the file name.
    4. Do not import any extra library. We will import libraries from MTP_lib.py.
    5. The parameter is the file path of a data file, whose format is specified in the document.
    6. You need to return your schedule in two lists "machine" and "completion_time".
        (a) machine[j][0] is the machine ID (an integer) of the machine to process the first stage of job j + 1, and
            machine[j][1] is the machine ID (an integer) of the machine to process the second stage of job j + 1.
            Note. If job j + 1 has only one stage, you may store any integer in machine[j][1].
        (b) completion_time[j][0] is the completion time (an integer or a floating-point number) of the first stage of job j + 1, and
            completion_time[j][1] is the completion time (an integer or a floating-point number) of the second stage of job j + 1.
            Note. If job j + 1 has only one stage, you may store any integer or floating-point number in completion_time[j][1].
        Note 1. If you have n jobs, both the two lists are n by 2 (n rows, 2 columns).
        Note 2. In the list "machine", you should record the IDs of machines
                (i.e., to let machine 1 process the first stage of job 1,
                you should have machine[0][0] == 1 rather than machine[0][0] == 0).
    7. The only PY file that you need and are allowed to submit is this algorithm_module.py.
    '''

    # read data and store the information into your self-defined variables
    fp = open(file_path, 'r')
    # for a_row in fp:
    #    print(a_row) # a_row is a list
    # ...
    data = pd.read_csv(file_path)
    parse_machine_list = lambda machine_list: [] if pd.isna(machine_list) else list(map(int, machine_list.split(',')))

    # Apply the lambda function directly to the columns
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

        # Save the assignment
        assignments.append((job_id, job_schedule))


    #correct output format
    machine = [[0, 0] for _ in range(len(data))]
    completion_time = [[0, 0] for _ in range(len(data))]

    for job_id, schedule in assignments:
        job_index = job_id - 1
        for stage_index, (start_time, end_time, machine_id) in schedule.items():
            machine[job_index][stage_index] = machine_id if machine_id is not None else -1
            completion_time[job_index][stage_index] = end_time

    return machine, completion_time
