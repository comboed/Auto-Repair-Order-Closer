import csv

def read_csv(filename):
    try:
        return list(csv.reader(open(filename), delimiter = ","))
    except:
        print("Unable to locate ro file")
        exit(0)

def write_entry(filename, ro_number, content):
    data = []
    for row in read_csv("./data/" + filename):
        if row[1] == ro_number:
            row[2] = content
        data.append(row)
    save_csv(filename, data)

def save_csv(filename, data):
    with open("./data/" + filename, "w", newline = "") as file:
        csv.writer(file, delimiter = ",").writerows(data)