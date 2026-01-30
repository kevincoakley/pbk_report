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


# Always include classes from these departments as LS classes
ALWAYS_INCLUDE_DEPT = ["HUM", "MMW", "DOC", "ETHN", "THHI", "CULT", "CAT"]


def map_class_types(department, coursenumber, courseletter):
    df = _get_df("coursecrit.csv")

    if df is None:
        return []

    matches = set()

    # First pass: exact match
    # PHP: $data[1] == $department && $data[2] == $coursenumber && $data[3] == $courseletter
    match = df[
        (df["department"] == department)
        & (df["coursenumber"] == coursenumber)
        & (df["courseletter"] == courseletter)
    ]
    if not match.empty:
        matches.update(match["classtype"].tolist())

    # If no exact match, try alternate formats
    if not matches:
        # Case 1: Input has separate letter, check if CSV has combined (e.g. Input: "20", "R" -> CSV: "20R", "")
        if courseletter:
            combined_num = coursenumber + courseletter
            match = df[
                (df["department"] == department)
                & (df["coursenumber"] == combined_num)
                & (df["courseletter"] == "")
            ]
            if not match.empty:
                matches.update(match["classtype"].tolist())
        # Case 2: Input has no separate letter but number contains letter, check if CSV is split (e.g. Input: "20R", "" -> CSV: "20", "R")
        else:
            c_num = re.sub(r"[^0-9]", "", coursenumber)
            c_let = re.sub(r"[0-9]", "", coursenumber)
            if c_let:
                match = df[
                    (df["department"] == department)
                    & (df["coursenumber"] == c_num)
                    & (df["courseletter"] == c_let)
                ]
                if not match.empty:
                    matches.update(match["classtype"].tolist())

    # Second pass: wildcard
    if department != "AP" and department != "IB":
        wildcard_matches = df[
            (df["department"] == department) & (df["coursenumber"] == "*")
        ]

        if not wildcard_matches.empty:
            try:
                # Use regex to extract only the leading digits for comparison
                # This handles cases like "100A", "100", etc. for numeric comparison
                c_num_match = re.search(r"^\d+", str(coursenumber))
                c_num = int(c_num_match.group()) if c_num_match else 0
            except (ValueError, TypeError):
                c_num = 0

            for _, row in wildcard_matches.iterrows():
                # If anyUD is Y and coursenumber is >= 100, return classtype
                if (row["anyUD"] == "Y") and (c_num >= 100):
                    matches.add(row["classtype"])
                # If anyUD is N and coursenumber is < 100, return classtype
                elif (row["anyUD"] == "N") and (c_num < 100):
                    matches.add(row["classtype"])

    return list(matches)


def get_students():
    students = []
    df = _get_df("pbk_screening.csv")

    if df is None:
        return students

    # Load country codes
    country_df = _get_df("country_codes.csv")
    country_lookup = {}
    if country_df is not None:
        # Create a dictionary mapping country_code to country_name
        country_lookup = dict(
            zip(country_df["country_code"], country_df["country_name"])
        )

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
            "country": country_lookup.get(
                data.get("Permanent Mailing Country Line 1", ""),
                data.get("Permanent Mailing Country Line 1", ""),
            ),
        }
        students.append(student)
    return students


def _course_sort_key(item):
    """
    Sort key for courses:
    1. Department (alphabetical)
    2. Course Number (numeric value)
    3. Course Suffix (alphanumeric)
    """
    dept = item.get("dept", "")
    crsnum = item.get("crsnum", "")

    # Extract number and letter parts
    c_num_str = re.sub(r"[^0-9]", "", crsnum)
    c_let_str = re.sub(r"[0-9]", "", crsnum)

    c_num = int(c_num_str) if c_num_str else 0

    return (dept, c_num, c_let_str)


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

        # Filter 1: Exclude grade column equal to W (should include w and W)
        if data["grade"].strip().upper() == "W":
            continue

        # Filter 2: Exclude crsnum column equal to "90"
        if crsnum.strip() == "90":
            continue

        # Filter 3: Only include units that are greater than 2
        try:
            units = float(data["units"])
            if units <= 2:
                continue
        except (ValueError, TypeError):
            continue

        coursenumber = re.sub(r"[^0-9]", "", crsnum)
        courseletter = re.sub(r"[0-9]", "", crsnum)

        types = map_class_types(data["dept"], coursenumber, courseletter)

        if types:
            for type_ in types:
                if type_ in classes:
                    classes[type_].append(
                        {
                            "dept": data["dept"],
                            "crsnum": data["crsnum"],
                            "grade": data["grade"],
                        }
                    )

        # Always include classes from these departments as LS classes
        # Check if "LS" is NOT in types to avoid duplicates
        if data["dept"] in ALWAYS_INCLUDE_DEPT and (not types or "LS" not in types):
            classes["LS"].append(
                {
                    "dept": data["dept"],
                    "crsnum": data["crsnum"],
                    "grade": data["grade"],
                }
            )

    # Sort classes in each category
    for type_ in classes:
        classes[type_].sort(key=_course_sort_key)

    return classes


def get_ap_classes(student_id):
    ap_classes = {k: [] for k in get_class_types()}
    df = _get_df("pbk_screening_apclasses.csv")

    if df is None:
        return ap_classes, []

    student_classes = df[df["id"] == student_id]

    if student_classes.empty:
        return ap_classes, []

    # Deduplicate rows based on output columns
    student_classes = student_classes.drop_duplicates(
        subset=["dept", "crsnum", "title", "units"]
    )

    uncategorized = []

    for _, data in student_classes.iterrows():
        types = map_class_types(data["dept"], data["crsnum"], "")

        if types:
            for type_ in types:
                if type_ in ap_classes:
                    ap_classes[type_].append(
                        {
                            "dept": data["dept"],
                            "crsnum": data["crsnum"],
                            "description": data["title"],
                            "units": data["units"],
                        }
                    )
        else:
            # If no type map, add to uncategorized list (will go to transfer)
            uncategorized.append(
                {
                    "dept": data["dept"],
                    "crsnum": data["crsnum"],
                    "title": data["title"],
                    "units": data["units"],
                    "grade": "P",
                }
            )

    # Sort classes in each category
    for type_ in ap_classes:
        ap_classes[type_].sort(key=_course_sort_key)

    # Sort uncategorized classes
    uncategorized.sort(key=_course_sort_key)

    return ap_classes, uncategorized


def get_ib_classes(student_id):
    ib_classes = {k: [] for k in get_class_types()}
    df = _get_df("pbk_screening_ibclasses.csv")

    if df is None:
        return ib_classes, []

    student_classes = df[df["id"] == student_id]

    if student_classes.empty:
        return ib_classes, []

    # Deduplicate rows based on output columns
    student_classes = student_classes.drop_duplicates(
        subset=["dept", "crsnum", "title", "units"]
    )

    uncategorized = []

    for _, data in student_classes.iterrows():
        types = map_class_types(data["dept"], data["crsnum"], "")

        if types:
            for type_ in types:
                if type_ in ib_classes:
                    ib_classes[type_].append(
                        {
                            "dept": data["dept"],
                            "crsnum": data["crsnum"],
                            "description": data["title"],
                            "units": data["units"],
                        }
                    )
        else:
            # If no type map, add to uncategorized list (will go to transfer)
            uncategorized.append(
                {
                    "dept": data["dept"],
                    "crsnum": data["crsnum"],
                    "title": data["title"],
                    "units": data["units"],
                    "grade": "P",
                }
            )

    # Sort classes in each category
    for type_ in ib_classes:
        ib_classes[type_].sort(key=_course_sort_key)

    # Sort uncategorized classes
    uncategorized.sort(key=_course_sort_key)

    return ib_classes, uncategorized


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

    transfer_classes.sort(key=_course_sort_key)

    return transfer_classes


def main():
    students = get_students()

    # Enrich students with their classes
    for student in students:
        s_id = student["id"]
        student["classes"] = get_classes(s_id)
        student["apClasses"], student["apTransferClasses"] = get_ap_classes(s_id)
        student["ibClasses"], student["ibTransferClasses"] = get_ib_classes(s_id)
        student["transferClasses"] = get_transfer_classes(s_id)

    env = Environment(loader=FileSystemLoader(BASE_DIR))
    template = env.get_template("pbk_styling.j2")

    # Helper to count classes with grades for the template if needed,
    # but I did it in jinja directly.

    output = template.render(students=students, class_types=get_class_types())

    print(output)


if __name__ == "__main__":
    main()
