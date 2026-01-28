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
        reader = csv.DictReader(f)
        rows = list(reader)

    # First pass: exact match
    for data in rows:
        # PHP: $data[1] == $department && $data[2] == $coursenumber && $data[3] == $courseletter
        if (
            data["department"] == department
            and data["coursenumber"] == coursenumber
            and data["courseletter"] == courseletter
        ):
            return data["classtype"]

    # Second pass: wildcard
    if department != "AP" and department != "IB":
        for data in rows:
            if data["department"] == department and data["coursenumber"] == "*":
                return data["classtype"]

    # print(f"No match found for: {department} - {coursenumber} - {courseletter}")
    return None


def get_students():
    students = []
    csv_file = os.path.join(BASE_DIR, "pbk_screening.csv")

    if not os.path.exists(csv_file):
        return students

    with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)

        for data in reader:
            student = {
                "name": data["Full Name"],
                "fname": data["First Name"],
                "mname": data["Middle Name"],
                "lname": data["Last Name"],
                "id": data["PID"],
                "college": data["College"],
                "major": data["Major Code"],
                "major_desc": data["Major Description"],
                "level": data["Class Level"],
                "sex": data["Gender"],
                "cumunits": data["Cumulative Units"],
                "cumgpa": data["Cumulative GPA"],
                "email": data["Email(UCSD)"],
                "pm_line1": data["Permanent Mailing Addresss Line 1"],
                "pm_city": data["Permanent Mailing City Line 1"],
                "pm_state": data["Permanent Mailing State Line 1"],
                "pm_zip": data["Permanent Mailing Zip Code Line 1"],
                "pm_country": data["Permanent Mailing Country Line 1"],
                "pm_phone": data["Permanent Phone Number"],
                "gradqtr": data["Graduating Quarter"],
                "reg_status": data["Registration Status"],
                "major2": "",
                "major2_desc": "",
                "apln_term": data["Graduating Quarter"],
                "lang": "N",
                "country": (
                    "United States"
                    if data["Permanent Mailing Country Line 1"] == "USA"
                    else data["Permanent Mailing Country Line 1"]
                ),
            }
            students.append(student)
    return students


def get_classes(student_id):
    classes = {k: [] for k in get_class_types()}
    csv_file = os.path.join(BASE_DIR, "pbk_screening_classes.csv")

    if not os.path.exists(csv_file):
        return classes

    with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)

        for data in reader:
            if data["id"] == student_id:
                # PHP: preg_replace('/[^0-9]/', '', $data[2])
                coursenumber = re.sub(r"[^0-9]", "", data["crsnum"])
                courseletter = re.sub(r"[0-9]", "", data["crsnum"])

                type_ = map_class_types(data["dept"], coursenumber, courseletter)

                if type_ in classes:
                    classes[type_].append(
                        {
                            "dept": data["dept"],
                            "crsnum": data["crsnum"],
                            "grade": data["grade"],
                        }
                    )
    return classes


def get_ap_classes(student_id):
    ap_classes = {k: [] for k in get_class_types()}
    csv_file = os.path.join(BASE_DIR, "pbk_screening_apclasses.csv")

    if not os.path.exists(csv_file):
        return ap_classes

    with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)

        for data in reader:
            if data["id"] == student_id:
                type_ = map_class_types(data["dept"], data["crsnum"], "")

                if type_ in ap_classes:
                    ap_classes[type_].append(
                        {
                            "crsnum": data["crsnum"],
                            "description": data["title"],
                            "units": data["units"],
                        }
                    )
    return ap_classes


def get_ib_classes(student_id):
    ib_classes = {k: [] for k in get_class_types()}
    csv_file = os.path.join(BASE_DIR, "pbk_screening_ibclasses.csv")

    if not os.path.exists(csv_file):
        return ib_classes

    with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)

        for data in reader:
            if data["id"] == student_id:
                type_ = map_class_types(data["dept"], data["crsnum"], "")

                if type_ in ib_classes:
                    ib_classes[type_].append(
                        {
                            "crsnum": data["crsnum"],
                            "description": data["title"],
                            "units": data["units"],
                        }
                    )
    return ib_classes


def get_transfer_classes(student_id):
    transfer_classes = []
    csv_file = os.path.join(BASE_DIR, "pbk_screening_transferclasses.csv")

    if not os.path.exists(csv_file):
        return transfer_classes

    with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)

        for data in reader:
            if data["id"] == student_id:
                transfer_classes.append(
                    {
                        "dept": data["dept"],
                        "crsnum": data["crsnum"],
                        "title": data["title"],
                        "units": data["units"],
                        "grade": data["grade"],
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
