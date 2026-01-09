import csv
import os
import sys
import re
from jinja2 import Environment, FileSystemLoader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_class_types():
    return {
        "LS": "Humanities",
        "SS": "Social Sciences",
        "NS": "Natural Sciences",
        "MS": "Mathematics",
        "LA": "Language",
    }


def map_class_types(department, coursenumber, courseletter):
    csv_file = os.path.join(BASE_DIR, "coursecrit.csv")

    if not os.path.exists(csv_file):
        return None

    # Read all rows into memory to avoid repeated file handles and allow multiple passes
    rows = []
    with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)  # Skip header
        except StopIteration:
            return None
        rows = list(reader)

    # First pass: exact match
    for data in rows:
        if len(data) < 6:
            continue
        # CSV columns: 0=id??, 1=dept, 2=num, 3=letter, ..., 5=type
        # PHP: $data[1] == $department && $data[2] == $coursenumber && $data[3] == $courseletter
        if (
            data[1] == department
            and data[2] == coursenumber
            and data[3] == courseletter
        ):
            return data[5]

    # Second pass: wildcard
    if department != "AP" and department != "IB":
        for data in rows:
            if len(data) < 6:
                continue
            if data[1] == department and data[2] == "*":
                return data[5]

    # print(f"No match found for: {department} - {coursenumber} - {courseletter}")
    return None


def get_students():
    students = []
    csv_file = os.path.join(BASE_DIR, "pbk_screening.csv")

    if not os.path.exists(csv_file):
        return students

    with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return students

        for data in reader:
            if len(data) >= 21:
                student = {
                    "name": data[0],
                    "fname": data[1],
                    "mname": data[2],
                    "lname": data[3],
                    "id": data[4],
                    "college": data[5],
                    "major": data[6],
                    "major_desc": data[7],
                    "level": data[8],
                    "sex": data[9],
                    "cumunits": data[10],
                    "cumgpa": data[11],
                    "email": data[12],
                    "pm_line1": data[13],
                    "pm_city": data[14],
                    "pm_state": data[15],
                    "pm_zip": data[16],
                    "pm_country": data[17],
                    "pm_phone": data[18],
                    "gradqtr": data[19],
                    "reg_status": data[20],
                    "major2": "",
                    "major2_desc": "",
                    "apln_term": data[19],
                    "lang": "N",
                    "country": "United States" if data[17] == "USA" else data[17],
                }
                students.append(student)
    return students


def get_classes(student_id):
    classes = {k: [] for k in get_class_types()}
    csv_file = os.path.join(BASE_DIR, "pbk_screening_classes.csv")

    if not os.path.exists(csv_file):
        return classes

    with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        try:
            next(reader)  # header
        except StopIteration:
            return classes

        for data in reader:
            if data[0] == student_id:
                # PHP: preg_replace('/[^0-9]/', '', $data[2])
                coursenumber = re.sub(r"[^0-9]", "", data[2])
                courseletter = re.sub(r"[0-9]", "", data[2])

                type_ = map_class_types(data[1], coursenumber, courseletter)

                if type_ in classes:
                    classes[type_].append(
                        {"dept": data[1], "crsnum": data[2], "grade": data[7]}
                    )
    return classes


def get_ap_classes(student_id):
    ap_classes = {k: [] for k in get_class_types()}
    csv_file = os.path.join(BASE_DIR, "pbk_screening_apclasses.csv")

    if not os.path.exists(csv_file):
        return ap_classes

    with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        try:
            next(reader)
        except StopIteration:
            return ap_classes

        for data in reader:
            if data[0] == student_id:
                type_ = map_class_types(data[3], data[4], "")

                if type_ in ap_classes:
                    ap_classes[type_].append(
                        {"crsnum": data[4], "description": data[5], "units": data[8]}
                    )
    return ap_classes


def get_ib_classes(student_id):
    ib_classes = {k: [] for k in get_class_types()}
    csv_file = os.path.join(BASE_DIR, "pbk_screening_ibclasses.csv")

    if not os.path.exists(csv_file):
        return ib_classes

    with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        try:
            next(reader)
        except StopIteration:
            return ib_classes

        for data in reader:
            if data[0] == student_id:
                type_ = map_class_types(data[3], data[4], "")

                if type_ in ib_classes:
                    ib_classes[type_].append(
                        {"crsnum": data[4], "description": data[5], "units": data[8]}
                    )
    return ib_classes


def get_transfer_classes(student_id):
    transfer_classes = []
    csv_file = os.path.join(BASE_DIR, "pbk_screening_transferclasses.csv")

    if not os.path.exists(csv_file):
        return transfer_classes

    with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        try:
            next(reader)
        except StopIteration:
            return transfer_classes

        for data in reader:
            if data[0] == student_id:
                transfer_classes.append(
                    {
                        "dept": data[3],
                        "crsnum": data[4],
                        "title": data[5],
                        "units": data[8],
                        "grade": data[9],
                    }
                )
    return transfer_classes


def main():
    students = get_students()

    # Enrich students with their classes
    for student in students:
        s_id = student["id"]
        student["classes"] = get_classes(s_id)
        student["apClasses"] = get_ap_classes(s_id)
        student["ibClasses"] = get_ib_classes(s_id)
        student["transferClasses"] = get_transfer_classes(s_id)

    env = Environment(loader=FileSystemLoader(BASE_DIR))
    template = env.get_template("pbk_styling.j2")

    # Helper to count classes with grades for the template if needed,
    # but I did it in jinja directly.

    output = template.render(students=students, class_types=get_class_types())

    print(output)


if __name__ == "__main__":
    main()
