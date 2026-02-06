import csv
import os
import sys
import re
from typing import Dict, List, Optional, Set, Tuple, Any, TypedDict, cast
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


class Student(TypedDict):
    name: str
    fname: str
    mname: str
    lname: str
    id: str
    id: str
    college: str
    college_name: str
    major: str
    major_desc: str
    level: str
    sex: str
    cumunits: str
    cumgpa: str
    email: str
    pm_line1: str
    pm_city: str
    pm_state: str
    pm_zip: str
    pm_country: str
    pm_phone: str
    gradqtr: str
    reg_status: str
    major2: str
    major2_desc: str
    apln_term: str
    lang: str
    country: str
    include_city: bool
    csv_row: int
    classes: Dict[str, List["ClassItem"]]
    apClasses: Dict[str, List["ApIbClassItem"]]
    apTransferClasses: List["UncategorizedClassItem"]
    ibClasses: Dict[str, List["ApIbClassItem"]]
    ibTransferClasses: List["UncategorizedClassItem"]
    transferClasses: List["TransferClassItem"]
    bin: int


class ClassItem(TypedDict):
    dept: str
    crsnum: str
    grade: str
    types: List[str]


class ApIbClassItem(TypedDict):
    dept: str
    crsnum: str
    description: str
    units: str


class UncategorizedClassItem(TypedDict):
    dept: str
    crsnum: str
    title: str
    units: str
    grade: str


class TransferClassItem(TypedDict):
    dept: str
    crsnum: str
    title: str
    units: str
    grade: str


# Always include classes from these departments as LS classes
ALWAYS_INCLUDE_DEPT = ["HUM", "MMW", "DOC", "ETHN", "THHI", "CULT", "CAT"]

CLASS_TYPES = {
    "LS": "Humanities",
    "SS": "Social Sciences",
    "NS": "Natural Sciences",
    "MS": "Mathematics",
    "LA": "Language",
}


def get_class_types() -> Dict[str, str]:
    return CLASS_TYPES


def _find_exact_match(
    df: pd.DataFrame, department: str, coursenumber: str, courseletter: str
) -> Set[str]:
    """
    Find matches where department, number, and letter match exactly.
    """
    matches = set()
    match = df[
        (df["department"] == department)
        & (df["coursenumber"] == coursenumber)
        & (df["courseletter"] == courseletter)
    ]
    if not match.empty:
        matches.update(match["classtype"].tolist())
    return matches


def _find_fuzzy_match(
    df: pd.DataFrame, department: str, coursenumber: str, courseletter: str
) -> Set[str]:
    """
    Find matches handling sloppy input vs CSV formatting:
    1. Input has letter, CSV has combined number+letter.
    2. Input has combined number+letter, CSV has separate.
    """
    matches = set()

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
    return matches


def _find_wildcard_match(
    df: pd.DataFrame, department: str, coursenumber: str
) -> Set[str]:
    """
    Find matches based on wildcard rules (coursenumber='*').
    Uses 'anyUD' column to distinguish upper div (>=100) vs lower div (<100).
    """
    matches = set()
    # Skip AP/IB for wildcards as per original logic
    if department == "AP" or department == "IB":
        return matches

    wildcard_matches = df[
        (df["department"] == department) & (df["coursenumber"] == "*")
    ]

    if wildcard_matches.empty:
        return matches

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

    return matches


def map_class_types(department: str, coursenumber: str, courseletter: str) -> List[str]:
    df = _get_df("coursecrit.csv")

    if df is None:
        return []

    matches: Set[str] = set()

    # 1. Exact Match
    matches.update(_find_exact_match(df, department, coursenumber, courseletter))

    # 2. Fuzzy Match (if no exact matches found yet)
    # Original logic only did fuzzy if !matches. Preserve that?
    # Original: "If no exact match, try alternate formats" -> yes.
    if not matches:
        matches.update(_find_fuzzy_match(df, department, coursenumber, courseletter))

    # 3. Wildcard Match
    # Original logic ran this regardless of previous matches
    matches.update(_find_wildcard_match(df, department, coursenumber))

    return list(matches)


def _get_country_lookup() -> Dict[str, Dict[str, Any]]:
    """
    Load country codes and return a mapping of code to info (name, include_city).
    """
    country_df = _get_df("country_codes.csv")
    if country_df is None:
        return {}

    lookup = {}
    for _, row in country_df.iterrows():
        lookup[row["country_code"]] = {
            "name": row["country_name"],
            "include_city": row["include_city"] == "Y",
        }
    return lookup


def _get_college_lookup() -> Dict[str, str]:
    """
    Load colleges and return a mapping of code to name.
    """
    college_df = _get_df("colleges.csv")
    if college_df is None:
        return {}
    return dict(zip(college_df["college_code"], college_df["college_name"]))


def get_students() -> List[Student]:
    students: List[Student] = []
    df = _get_df("pbk_screening.csv")

    if df is None:
        return students

    country_lookup = _get_country_lookup()
    college_lookup = _get_college_lookup()

    # Iterate over the rows and construct the student dictionary
    # to_dict('records') is efficient enough for this step
    records = df.to_dict("records")

    for index, data in enumerate(records):
        pm_country_code = data.get("Permanent Mailing Country Line 1", "")
        country_info = country_lookup.get(
            pm_country_code, {"name": pm_country_code, "include_city": False}
        )

        # Use TypedDict constructor for better type checking if we weren't just appending dicts
        # But here we construct the dict explicitly to match Student TypedDict
        student: Student = {
            "name": data.get("Full Name", ""),
            "fname": data.get("First Name", ""),
            "mname": data.get("Middle Name", ""),
            "lname": data.get("Last Name", ""),
            "id": data.get("PID", ""),
            "college": data.get("College", ""),
            "college_name": college_lookup.get(data.get("College", ""), ""),
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
            "pm_country": pm_country_code,
            "pm_phone": data.get("Permanent Phone Number", ""),
            "gradqtr": data.get("Graduating Quarter", ""),
            "reg_status": data.get("Registration Status", ""),
            "major2": "",
            "major2_desc": "",
            "apln_term": data.get("Apln Term", ""),
            "lang": "N",
            "country": country_info["name"],
            "include_city": country_info["include_city"],
            "csv_row": index + 1,
            "classes": {},
            "apClasses": {},
            "apTransferClasses": [],
            "ibClasses": {},
            "ibTransferClasses": [],
            "transferClasses": [],
            "bin": 0,
        }
        students.append(student)
    return students


def _course_sort_key(item: Dict[str, Any]) -> Tuple[str, int, str]:
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


def _get_student_records(filename: str, student_id: str) -> List[Dict[str, Any]]:
    """
    Load CSV, filter by student ID, and return as list of dicts.
    """
    df = _get_df(filename)
    if df is None:
        return []

    student_rows = df[df["id"] == student_id]
    if student_rows.empty:
        return []

    return student_rows.to_dict("records")


def _sort_class_dict(class_dict: Dict[str, List[Any]]) -> None:
    """
    Sort lists within a dictionary of classes using the standard sort key.
    """
    for key in class_dict:
        class_dict[key].sort(key=_course_sort_key)


def get_classes(student_id: str) -> Dict[str, List[ClassItem]]:
    classes: Dict[str, List[ClassItem]] = {k: [] for k in CLASS_TYPES}
    records = _get_student_records("pbk_screening_classes.csv", student_id)

    for data in records:
        # PHP: preg_replace('/[^0-9]/', '', $data[2])
        crsnum = data.get("crsnum", "")
        grade = data.get("grade", "").strip()
        units_str = data.get("units", "0")

        # Filter 1: Exclude grade column equal to W (should include w and W)
        if grade.upper() == "W":
            continue

        # Filter 2: Exclude crsnum column equal to "90"
        if crsnum.strip() == "90":
            continue

        # Filter 3: Only include units that are greater than 2
        try:
            units = float(units_str)
            if units <= 2:
                continue
        except (ValueError, TypeError):
            continue

        coursenumber = re.sub(r"[^0-9]", "", crsnum)
        courseletter = re.sub(r"[0-9]", "", crsnum)

        types = map_class_types(data.get("dept", ""), coursenumber, courseletter)

        # Filter types to only include valid CLASS_TYPES
        types = [t for t in types if t in CLASS_TYPES]

        # Always include classes from these departments as LS classes
        if data.get("dept", "") in ALWAYS_INCLUDE_DEPT:
            if "LS" not in types:
                types.append("LS")

        class_item: ClassItem = {
            "dept": data.get("dept", ""),
            "crsnum": crsnum,
            "grade": data.get("grade", ""),
            "types": types,
        }

        if types:
            for type_ in types:
                if type_ in classes:
                    classes[type_].append(class_item)

    _sort_class_dict(classes)

    return classes


def _process_ap_ib_classes(
    filename: str, student_id: str
) -> Tuple[Dict[str, List[ApIbClassItem]], List[UncategorizedClassItem]]:
    """
    Shared logic for AP and IB classes:
    1. Load & Deduplicate
    2. Map types
    3. Return categorized (dict) and uncategorized (list)
    """
    categorized: Dict[str, List[ApIbClassItem]] = {k: [] for k in CLASS_TYPES}
    uncategorized: List[UncategorizedClassItem] = []

    df = _get_df(filename)
    if df is None:
        return categorized, uncategorized

    student_rows = df[df["id"] == student_id]
    if student_rows.empty:
        return categorized, uncategorized

    # Deduplicate rows based on output columns
    # Note: original code used subset=["dept", "crsnum", "title", "units"]
    student_rows = student_rows.drop_duplicates(
        subset=["dept", "crsnum", "title", "units"]
    )

    records = student_rows.to_dict("records")

    for data in records:
        dept = data.get("dept", "")
        crsnum = data.get("crsnum", "")
        title = data.get("title", "")
        units = data.get("units", "")

        types = map_class_types(dept, crsnum, "")

        if types:
            for type_ in types:
                if type_ in categorized:
                    categorized[type_].append(
                        {
                            "dept": dept,
                            "crsnum": crsnum,
                            "description": title,
                            "units": units,
                        }
                    )
        else:
            # If no type map, add to uncategorized list (will go to transfer)
            uncategorized.append(
                {
                    "dept": dept,
                    "crsnum": crsnum,
                    "title": title,
                    "units": units,
                    "grade": "P",
                }
            )

    _sort_class_dict(categorized)
    uncategorized.sort(key=_course_sort_key)

    return categorized, uncategorized


def get_ap_classes(
    student_id: str,
) -> Tuple[Dict[str, List[ApIbClassItem]], List[UncategorizedClassItem]]:
    return _process_ap_ib_classes("pbk_screening_apclasses.csv", student_id)


def get_ib_classes(
    student_id: str,
) -> Tuple[Dict[str, List[ApIbClassItem]], List[UncategorizedClassItem]]:
    return _process_ap_ib_classes("pbk_screening_ibclasses.csv", student_id)


def get_transfer_classes(student_id: str) -> List[TransferClassItem]:
    transfer_classes: List[TransferClassItem] = []
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

    records = student_classes.to_dict("records")

    for data in records:
        transfer_classes.append(
            {
                "dept": data.get("dept", ""),
                "crsnum": data.get("crsnum", ""),
                "title": data.get("title", ""),
                "units": data.get("units", ""),
                "grade": data.get("grade", ""),
            }
        )

    transfer_classes.sort(key=_course_sort_key)

    return transfer_classes


import argparse


def generate_csv(students: List[Student]) -> None:
    """
    Generate CSV output for the given list of students.
    Columns: File #, Full Name, PID, Email, Major
    """
    writer = csv.writer(sys.stdout)
    writer.writerow(["File #", "Full Name", "PID", "Email", "Major"])

    # "File #" is a simple counter (1, 2, 3...) based on the output row number
    for i, student in enumerate(students, start=1):
        writer.writerow(
            [
                str(i),
                student["name"],
                student["id"],
                student["email"],
                student["major_desc"],
            ]
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PBK report.")
    parser.add_argument(
        "--html", action="store_true", help="Output HTML report (default)"
    )
    parser.add_argument("--csv", action="store_true", help="Output CSV report")

    args = parser.parse_args()

    # Default to HTML if neither or both are specified (or prioritize one? Standard argparse behavior is mutually exclusive usually better, but user said 'update with 2 arguments', implied flags. I'll prioritize csv if both, or just run whatever is requested. Let's make CSV exclusive or default to HTML if nothing.)
    # Actually, simply checking args.csv first is fine. If they pass both, do they want both?
    # "should output what is currently outputed" for html. "should return a csv output" for csv.
    # I will support executing one. If both are passed, I'll error or just pick one. I'll make them mutually exclusive group for cleanliness.
    # Wait, the prompt says "update pbk_styling.py with 2 command line arguments".

    # Let's adjust parser logic inside the standard main block.

    students = get_students()

    # Enrich students with their classes
    #
    # Bin 1: Condition 1
    # - College is RE or FI
    # - AND Has ZERO LA classes (in classes, apClasses, or ibClasses)
    # - AND pm_country IS US
    #
    bin1_students = []

    #
    # Bin 2: Condition 2
    # - Does not match Bin 1
    # - Has more than 8 transfer classes (Len(transferClasses) > 8)
    #
    bin2_students = []

    #
    # Bin 3: Remainder
    #
    bin3_students = []

    for student in students:
        s_id = student["id"]
        student["classes"] = get_classes(s_id)
        student["apClasses"], student["apTransferClasses"] = get_ap_classes(s_id)
        student["ibClasses"], student["ibTransferClasses"] = get_ib_classes(s_id)
        student["transferClasses"] = get_transfer_classes(s_id)

        has_la_classes = (
            len(student["classes"]["LA"]) != 0
            or len(student["apClasses"]["LA"]) != 0
            or len(student["ibClasses"]["LA"]) != 0
        )

        # Bin 1 Logic
        # - College is NOT RE or FI
        # - AND Has ZERO LA classes
        # - AND pm_country IS US
        is_bin1 = (
            (student["college"] != "RE" and student["college"] != "FI")
            and (not has_la_classes)
            and (student["pm_country"] == "US")
        )

        if is_bin1:
            student["bin"] = 1
            bin1_students.append(student)
        # Bin 2: High Transfer (>= 8 classes)
        elif len(student["transferClasses"]) >= 8:
            student["bin"] = 2
            bin2_students.append(student)
        else:
            student["bin"] = 3
            bin3_students.append(student)

    # Concatenate the bins
    students = bin1_students + bin2_students + bin3_students

    if args.csv:
        generate_csv(students)
    else:
        # Default behavior: HTML
        env = Environment(loader=FileSystemLoader(BASE_DIR))
        template = env.get_template("pbk_styling.j2")

        output = template.render(students=students, class_types=get_class_types())

        print(output)


if __name__ == "__main__":
    main()
