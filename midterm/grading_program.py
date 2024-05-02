'''
You do not need to change the code in this file.
You only need to ensure that the TAs can run your algorithm here.
'''
from MTP_lib import *
from algorithm_module import heuristic_algorithm

def check_format(machine, completion_time):
    for m in machine:
        if len(m) != 2:
            return False
        if not isinstance(m[0], int):
            return False
        if not isinstance(m[1], int):
            return False

    for c in completion_time:
        if len(c) != 2:
            return False
        if not (isinstance(c[0], int) or isinstance(c[0], float)):
            return False
        if not (isinstance(c[1], int) or isinstance(c[1], float)):
            return False

    return True


if __name__ == '__main__':

    # read all instances (csv files) under data folder
    all_data_list = os.listdir('data')

    # evaluate all instances
    result_df = pd.DataFrame(columns = ['Data name', 'Time', 'Tardiness', 'Makespan', 'Feasibility'])

    for file_name in all_data_list:
        tardiness = 0
        makespan = 0
        feasibility = False

        start_time = time.time()

        try:
            '''
            1. We will import your algorithm here and give you file_path (e.g.,'data/instance01.csv') as the function argument.
            2. You need to return two two-dimensional lists 'machine' and 'completion_time'.
            '''
            file_path = 'data/' + file_name
            machine, completion_time = heuristic_algorithm(file_path)
        except:
            print('The algorithm has errors.')

        end_time = time.time()
        spent_time = end_time - start_time

        try:
            '''
            We will check the format, feasibility, and calculate the objective values here.
            '''
            if not check_format(machine, completion_time):
                print('The format has errors.')

            # feasibility, tardiness, makespan = find_obj_value(file_path, machine, completion_time)
        except:
            print('The algorithm has errors.')

        result_df = pd.concat([result_df, pd.DataFrame([{'Data name': file_name,
                                                         'Time': spent_time,
                                                         'Tardiness': tardiness,
                                                         'Makespan': makespan,
                                                         'Feasibility': feasibility}])], ignore_index = True)

    # output result
    result_df.to_csv('result.csv', index = False)
