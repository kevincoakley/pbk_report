import csv
import os
import sys
import re
from jinja2 import Environment, FileSystemLoader
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Global cache for DataFrames to ensure they are loaded only once
_DFS = {}


def _get_df(filename):
    """
    Helper to load a CSV into a pandas DataFrame and cache it.
    Returns None if file does not exist.
    """
    if filename in _DFS:
        return _DFS[filename]

    file_path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(file_path):
        _DFS[filename] = None
        return None

    try:
        # Keep all data as string to avoid type inference issues (e.g. leading zeros in IDs)
        # Using dtype=str ensures consistent behavior with csv.DictReader
        df = pd.read_csv(file_path, dtype=str, encoding="utf-8", on_bad_lines="skip")
        # Fill NaN with empty strings to match previous behavior where empty fields were strings
        df = df.fillna("")
        _DFS[filename] = df
        return df
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        _DFS[filename] = None
        return None


def get_class_types():
    return {
        "LS": "Humanities",
        "SS": "Social Sciences",
        "NS": "Natural Sciences",
        "MS": "Mathematics",
        "LA": "Language",
    }


def map_class_types(department, coursenumber, courseletter):
    df = _get_df("coursecrit.csv")

    if df is None:
        return None

    # First pass: exact match
    # PHP: $data[1] == $department && $data[2] == $coursenumber && $data[3] == $courseletter
    match = df[
        (df["department"] == department)
        & (df["coursenumber"] == coursenumber)
        & (df["courseletter"] == courseletter)
    ]
    if not match.empty:
        return match.iloc[0]["classtype"]

    # Second pass: wildcard
    if department != "AP" and department != "IB":
        wildcard_match = df[
            (df["department"] == department) & (df["coursenumber"] == "*")
        ]
        if not wildcard_match.empty:
            return wildcard_match.iloc[0]["classtype"]

    # print(f"No match found for: {department} - {coursenumber} - {courseletter}")
    return None


def get_students():
    students = []
    df = _get_df("pbk_screening.csv")

    if df is None:
        return students

    # Iterate over the rows and construct the student dictionary
    # to_dict('records') is efficient enough for this step
    records = df.to_dict("records")

    for data in records:
        student = {
            "name": data.get("Full Name", ""),
            "fname": data.get("First Name", ""),
            "mname": data.get("Middle Name", ""),
            "lname": data.get("Last Name", ""),
            "id": data.get("PID", ""),
            "college": data.get("College", ""),
            "major": data.get("Major Code", ""),
            "major_desc": data.get("Major Description", ""),
            "level": data.get("Class Level", ""),
            "sex": data.get("Gender", ""),
            "cumunits": data.get("Cumulative Units", ""),
            "cumgpa": data.get("Cumulative GPA", ""),
            "email": data.get("Email(UCSD)", ""),
            "pm_line1": data.get("Permanent Mailing Addresss Line 1", ""),
            "pm_city": data.get("Permanent Mailing City Line 1", ""),
            "pm_state": data.get("Permanent Mailing State Line 1", ""),
            "pm_zip": data.get("Permanent Mailing Zip Code Line 1", ""),
            "pm_country": data.get("Permanent Mailing Country Line 1", ""),
            "pm_phone": data.get("Permanent Phone Number", ""),
            "gradqtr": data.get("Graduating Quarter", ""),
            "reg_status": data.get("Registration Status", ""),
            "major2": "",
            "major2_desc": "",
            "apln_term": data.get("Graduating Quarter", ""),
            "lang": "N",
            "country": (
                "United States"
                if data.get("Permanent Mailing Country Line 1") == "USA"
                else data.get("Permanent Mailing Country Line 1", "")
            ),
        }
        students.append(student)
    return students


def get_classes(student_id):
    classes = {k: [] for k in get_class_types()}
    df = _get_df("pbk_screening_classes.csv")

    if df is None:
        return classes

    # Filter for the specific student
    student_classes = df[df["id"] == student_id]

    if student_classes.empty:
        return classes

    for _, data in student_classes.iterrows():
        # PHP: preg_replace('/[^0-9]/', '', $data[2])
        crsnum = data["crsnum"]
        coursenumber = re.sub(r"[^0-9]", "", crsnum)
        courseletter = re.sub(r"[0-9]", "", crsnum)

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
    df = _get_df("pbk_screening_apclasses.csv")

    if df is None:
        return ap_classes

    student_classes = df[df["id"] == student_id]

    if student_classes.empty:
        return ap_classes

    # Deduplicate rows based on output columns
    student_classes = student_classes.drop_duplicates(
        subset=["dept", "crsnum", "title", "units"]
    )

    for _, data in student_classes.iterrows():
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
    df = _get_df("pbk_screening_ibclasses.csv")

    if df is None:
        return ib_classes

    student_classes = df[df["id"] == student_id]

    if student_classes.empty:
        return ib_classes

    # Deduplicate rows based on output columns
    student_classes = student_classes.drop_duplicates(
        subset=["dept", "crsnum", "title", "units"]
    )

    for _, data in student_classes.iterrows():
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
    df = _get_df("pbk_screening_transferclasses.csv")

    if df is None:
        return transfer_classes

    student_classes = df[df["id"] == student_id]

    if student_classes.empty:
        return transfer_classes

    # Deduplicate rows based on output columns
    student_classes = student_classes.drop_duplicates(
        subset=["dept", "crsnum", "title", "units", "grade"]
    )

    for _, data in student_classes.iterrows():
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
