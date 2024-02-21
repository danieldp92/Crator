import os
import csv

res_path = "resources"


def save_file(content, dir):
    with open(dir, 'w') as file:
        file.write(content)


def save_list(list_data, path):
    # write list to a text file
    with open(path, 'w') as file:
        for item in list_data:
            file.write(item + '\n')


def read_csv_file(file_path):
    data = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            data.append(tuple(row))
    return data


def save_csv(data, path):
    with open(path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)
