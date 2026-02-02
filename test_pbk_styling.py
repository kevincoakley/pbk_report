import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import io
import pandas as pd

# Ensure valid import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pbk_styling


class TestPbkStyling(unittest.TestCase):

    def test_get_class_types(self):
        expected = {
            "LS": "Humanities",
            "SS": "Social Sciences",
            "NS": "Natural Sciences",
            "MS": "Mathematics",
            "LA": "Language",
        }
        self.assertEqual(pbk_styling.get_class_types(), expected)

    @patch("pbk_styling._get_df")
    def test_map_class_types(self, mock_get_df):
        # Setup mock CSV data
        csv_content = (
            "courseid,department,coursenumber,courseletter,anyUD,classtype\n"
            "1,MATH,101,A,N,MS\n"
            "2,HIST,*,*,N,SS\n"
            "3,PSYC,60,A,N,MS\n"
            "4,PSYC,60,A,N,SS\n"
            "5,SIO,20R,,N,NS\n"
            "6,COGS,18,A,N,SS\n"
        )
        df = pd.read_csv(io.StringIO(csv_content), dtype=str).fillna("")
        mock_get_df.return_value = df

        # Test exact match
        result = pbk_styling.map_class_types("MATH", "101", "A")
        self.assertEqual(result, ["MS"])

        # Test multiple exact matches
        result = pbk_styling.map_class_types("PSYC", "60", "A")
        self.assertEqual(sorted(result), ["MS", "SS"])

        # Test messy data: Input Split ("20", "R") -> CSV Combined ("20R", "")
        result = pbk_styling.map_class_types("SIO", "20", "R")
        self.assertEqual(result, ["NS"])

        # Test messy data: Input Combined ("18A", "") -> CSV Split ("18", "A")
        result = pbk_styling.map_class_types("COGS", "18A", "")
        self.assertEqual(result, ["SS"])

        # Test wildcard match logic
        # 1. Match anyUD=N with course < 100 (SS)
        result = pbk_styling.map_class_types("HIST", "99", "")
        self.assertEqual(result, ["SS"])

        # 2. Match anyUD=Y with course >= 100 (LS) -- assuming added row
        # Add a more complex dataframe setup for this test
        csv_content_complex = (
            "courseid,department,coursenumber,courseletter,anyUD,classtype\n"
            "1,MATH,101,A,N,MS\n"
            "2,HIST,*,*,N,SS\n"
            "3,LIT,*,*,Y,LS\n"
            "4,MIX,*,*,N,SS\n"
            "5,MIX,*,*,Y,LS\n"
            "6,BOTH,100,,N,MS\n"
            "7,BOTH,*,*,Y,SS\n"
        )
        df_complex = pd.read_csv(io.StringIO(csv_content_complex), dtype=str).fillna("")
        mock_get_df.return_value = df_complex

        # Test BOTH: Matches exact (MS) and wildcard (SS) because 100 >= 100 and AnyUD=Y
        # Wait, AnyUD=Y means >= 100.
        # Row 6: BOTH 100 -> MS
        # Row 7: BOTH * -> SS (AnyUD=Y, so 100 matches)
        # Expected: ["MS", "SS"]
        result = pbk_styling.map_class_types("BOTH", "100", "")
        self.assertEqual(sorted(result), ["MS", "SS"])

        # Test LIT: anyUD=Y, course=105 -> LS
        result = pbk_styling.map_class_types("LIT", "105", "")
        self.assertEqual(result, ["LS"])

        # Test LIT: anyUD=Y, course=50 -> [] (mismatch condition)
        result = pbk_styling.map_class_types("LIT", "50", "")
        self.assertEqual(result, [])

        # Test MIX: has both N (SS) and Y (LS) rows
        # Course 10 (matches N -> SS)
        result = pbk_styling.map_class_types("MIX", "10", "")
        self.assertEqual(result, ["SS"])

        # Course 150 (matches Y -> LS)
        result = pbk_styling.map_class_types("MIX", "150", "")
        self.assertEqual(result, ["LS"])

        # Test no match
        result = pbk_styling.map_class_types("ART", "101", "A")
        self.assertEqual(result, [])

        # Test file not exists
        mock_get_df.return_value = None
        result = pbk_styling.map_class_types("MATH", "101", "A")
        self.assertEqual(result, [])

    @patch("pbk_styling._get_df")
    def test_get_students(self, mock_get_df):
        headers = "Full Name,First Name,Middle Name,Last Name,PID,College,Major Code,Major Description,Class Level,Gender,Cumulative Units,Cumulative GPA,Email(UCSD),Permanent Mailing Addresss Line 1,Permanent Mailing City Line 1,Permanent Mailing State Line 1,Permanent Mailing Zip Code Line 1,Permanent Mailing Country Line 1,Permanent Phone Number,Graduating Quarter,Registration Status"
        row1 = "Doe,John,M,Doe,12345,Col,Maj,Desc,U,M,100,4.0,e@mail,Addr,City,ST,12345,US,555,2023,Reg"
        row2 = "Smith,Jane,F,Smith,67890,Col,Maj,Desc,U,F,100,4.0,e@mail,Addr,City,ST,12345,XX,555,2023,Reg"
        csv_content = f"{headers}\n{row1}\n{row2}\n"

        country_content = "country_code,country_name\nUS,United States\nCA,Canada\n"

        def side_effect(filename):
            if filename == "pbk_screening.csv":
                return pd.read_csv(io.StringIO(csv_content), dtype=str).fillna("")
            if filename == "country_codes.csv":
                return pd.read_csv(io.StringIO(country_content), dtype=str).fillna("")
            return None

        mock_get_df.side_effect = side_effect

        students = pbk_styling.get_students()
        self.assertEqual(len(students), 2)

        # Test valid country lookup
        self.assertEqual(students[0]["id"], "12345")
        self.assertEqual(students[0]["country"], "United States")

        # Test fallback to code when not found
        self.assertEqual(students[1]["id"], "67890")
        self.assertEqual(students[1]["country"], "XX")

        # Test file not exists
        mock_get_df.side_effect = None
        mock_get_df.return_value = None
        self.assertEqual(pbk_styling.get_students(), [])

    @patch("pbk_styling.map_class_types")
    @patch("pbk_styling._get_df")
    def test_get_classes(self, mock_get_df, mock_map):
        headers = "id,dept,crsnum,grade,units"
        # 1. Valid class
        row1 = "12345,MATH,101A,A,4.0"
        # 2. Grade W
        row2 = "12345,MATH,102,W,4.0"
        # 3. Grade w
        row3 = "12345,MATH,103,w,4.0"
        # 4. Crsnum 90
        row4 = "12345,MATH,90,A,4.0"
        # 5. Crsnum 90 with space
        row5 = "12345,MATH, 90 ,A,4.0"
        # 6. Units 2.0
        row6 = "12345,MATH,104,A,2.0"
        # 7. Units 1.0
        row7 = "12345,MATH,105,A,1.0"
        # 8. PSYC 60 (Multiple types)
        row8 = "12345,PSYC,60,A,4.0"

        csv_content = f"{headers}\n{row1}\n{row2}\n{row3}\n{row4}\n{row5}\n{row6}\n{row7}\n{row8}\n"

        df = pd.read_csv(io.StringIO(csv_content), dtype=str).fillna("")
        mock_get_df.return_value = df

        # Mock map_class_types to return list
        def side_effect(d, n, l):
            if d == "MATH":
                return ["MS"]
            if d == "PSYC" and n == "60":
                return ["MS", "SS"]
            return []

        mock_map.side_effect = side_effect

        classes = pbk_styling.get_classes("12345")

        # Check MATH
        self.assertIn("MS", classes)
        # Should be 2 classes in MS (MATH 101A and PSYC 60)
        ms_courses = [c["crsnum"] for c in classes["MS"]]
        self.assertIn("101A", ms_courses)
        self.assertIn("60", ms_courses)

        # Check PSYC 60 also in SS
        self.assertIn("SS", classes)
        ss_courses = [c["crsnum"] for c in classes["SS"]]
        self.assertIn("60", ss_courses)

        # Test Force Include (e.g. HUM)
        # Setup mock for force include scenario
        # 1. Dept HUM (in ALWAYS_INCLUDE_DEPT), map returns [] -> Should be in LS
        # 2. Dept HUM (in ALWAYS_INCLUDE_DEPT), map returns ["LS"] -> Should be in LS once

        row9 = "12345,HUM,1,A,4.0"
        csv_content_force = f"{headers}\n{row9}\n"
        df_force = pd.read_csv(io.StringIO(csv_content_force), dtype=str).fillna("")
        mock_get_df.return_value = df_force

        # Scenario 1: map returns []
        mock_map.side_effect = lambda d, n, l: []
        classes = pbk_styling.get_classes("12345")
        self.assertEqual(len(classes["LS"]), 1)
        self.assertEqual(classes["LS"][0]["dept"], "HUM")

        # Scenario 2: map returns ["LS"] (should not duplicate)
        mock_map.side_effect = lambda d, n, l: ["LS"]
        classes = pbk_styling.get_classes("12345")
        self.assertEqual(len(classes["LS"]), 1)

        mock_map.assert_called()

    @patch("pbk_styling.map_class_types")
    @patch("pbk_styling._get_df")
    def test_get_ap_classes(self, mock_get_df, mock_map):
        headers = "id,entityid,entityname,dept,crsnum,title,term,term_seq,units,grade,course_level,tranafct,approx_flag,approx_course_dept,approx_course_crsnum,term_received,attend_from,attend_to,approx_group_id,approx_group_type,refresh,download_shared_unique_key"
        # Include duplicate rows that differ in ignored columns (e.g. approx_course_crsnum)
        row1 = "12345,OTHRADPL,Advanced Placement Credit,MATH,101,Calc,S112,4580,4.0,P,LD,,0,HIST,1a,,,,0000,,2026-01-03,A0000001-OTHRADPL-AP-MA4"
        row2 = "12345,OTHRADPL,Advanced Placement Credit,MATH,101,Calc,S112,4580,4.0,P,LD,,0,HIST,1b,,,,0000,,2026-01-03,A0000001-OTHRADPL-AP-MA4"
        csv_content = f"{headers}\n{row1}\n{row2}\n"

        df = pd.read_csv(io.StringIO(csv_content), dtype=str).fillna("")
        mock_get_df.return_value = df

        # Mock map_class_types side effect to return [] for second row if needed
        # But here we set return_value to ["MS"], so all will be categorized.
        # Let's adjust mock_map to verify uncategorized logic too.

        def side_effect(d, n, l):
            if d == "MATH":
                return ["MS"]
            return []

        mock_map.side_effect = side_effect
        mock_map.return_value = None  # Clear fixed return

        # Add a row that will be uncategorized
        row3 = "12345,OTHRADPL,Advanced Placement Credit,HIST,99,History,S112,4580,4.0,P,LD,,0,HIST,1a,,,,0000,,2026-01-03,A0000001-OTHRADPL-AP-MA4"
        csv_content = f"{headers}\n{row1}\n{row2}\n{row3}\n"
        df = pd.read_csv(io.StringIO(csv_content), dtype=str).fillna("")
        mock_get_df.return_value = df

        ap_classes, uncategorized = pbk_styling.get_ap_classes("12345")

        self.assertIn("MS", ap_classes)
        # Should be 1 because of deduplication on relevant cols
        self.assertEqual(len(ap_classes["MS"]), 1)
        self.assertEqual(ap_classes["MS"][0]["crsnum"], "101")

        # Verify uncategorized
        self.assertEqual(len(uncategorized), 1)
        self.assertEqual(uncategorized[0]["dept"], "HIST")
        self.assertEqual(uncategorized[0]["grade"], "P")

    @patch("pbk_styling.map_class_types")
    @patch("pbk_styling._get_df")
    def test_get_ib_classes(self, mock_get_df, mock_map):
        headers = "id,entityid,entityname,dept,crsnum,title,term,term_seq,units,grade,course_level,tranafct,approx_flag,approx_course_dept,approx_course_crsnum,term_received,attend_from,attend_to,approx_group_id,approx_group_type,refresh,download_shared_unique_key"
        # Include duplicate rows that differ in ignored columns
        row1 = "12345,OTHRIBAC,International Baccalaureate Examination,HIST,101,World,SP20,5060,4.0,P,LD,,1,HIST,4a,,,,HS0610,S,2025-12-30,A0000000-OTHRIBAC-IB-HS5-HIST-4"
        row2 = "12345,OTHRIBAC,International Baccalaureate Examination,HIST,101,World,SP20,5060,4.0,P,LD,,1,HIST,4b,,,,HS0610,S,2025-12-30,A0000000-OTHRIBAC-IB-HS5-HIST-4"
        csv_content = f"{headers}\n{row1}\n{row2}\n"

        df = pd.read_csv(io.StringIO(csv_content), dtype=str).fillna("")
        mock_get_df.return_value = df

        mock_map.return_value = ["SS"]

        ib_classes, uncategorized = pbk_styling.get_ib_classes("12345")

        self.assertIn("SS", ib_classes)
        # Should be 1 because of deduplication
        self.assertEqual(len(ib_classes["SS"]), 1)
        self.assertEqual(len(uncategorized), 0)

    @patch("pbk_styling._get_df")
    def test_get_transfer_classes(self, mock_get_df):
        headers = "id,entityid,entityname,dept,crsnum,title,term,term_seq,units,grade,course_level,tranafct,approx_flag,approx_course_dept,approx_course_crsnum,term_received,attend_from,attend_to,approx_group_id,approx_group_type,refresh,download_shared_unique_key"
        # Include duplicate rows that differ in ignored columns
        row1 = "12345,EC004692,Santa Rosa Jr Coll,TRNS,101,Transfer 101,SP13,4610,3,T,LD,,1,CSE,12a,,,,0000,,2025-11-18,A0000000-EC004692-CIS-22B-CSE-12"
        row2 = "12345,EC004692,Santa Rosa Jr Coll,TRNS,101,Transfer 101,SP13,4610,3,T,LD,,1,CSE,12b,,,,0000,,2025-11-18,A0000000-EC004692-CIS-22B-CSE-12"
        csv_content = f"{headers}\n{row1}\n{row2}\n"

        df = pd.read_csv(io.StringIO(csv_content), dtype=str).fillna("")
        mock_get_df.return_value = df

        t_classes = pbk_styling.get_transfer_classes("12345")

        # Should be 1 because of deduplication
        self.assertEqual(len(t_classes), 1)
        self.assertEqual(t_classes[0]["title"], "Transfer 101")

    @patch("pbk_styling.print")
    @patch("pbk_styling.Environment")
    @patch("pbk_styling.get_transfer_classes")
    @patch("pbk_styling.get_ib_classes")
    @patch("pbk_styling.get_ap_classes")
    @patch("pbk_styling.get_classes")
    @patch("pbk_styling.get_students")
    def test_main(
        self,
        mock_students,
        mock_classes,
        mock_ap,
        mock_ib,
        mock_trans,
        mock_env,
        mock_print,
    ):
        # Setup mocks
        mock_students.return_value = [{"id": "12345", "college": "RE"}]
        mock_classes.return_value = {}
        mock_ap.return_value = ({}, [])
        mock_ib.return_value = ({}, [])
        mock_trans.return_value = []

        mock_template = MagicMock()
        mock_env.return_value.get_template.return_value = mock_template
        mock_template.render.return_value = "<html>Result</html>"

        pbk_styling.main()

        # Verify calls
        mock_students.assert_called_once()
        mock_classes.assert_called_with("12345")
        mock_template.render.assert_called()
        mock_print.assert_called_with("<html>Result</html>")

    @patch("pbk_styling.map_class_types")
    @patch("pbk_styling._get_df")
    def test_get_classes_sorting(self, mock_get_df, mock_map):
        headers = "id,dept,crsnum,grade,units"
        # Mixed order in CSV
        # Desired order:
        # ANTH 2
        # ANTH 100
        # ANTH 100A
        # BIO 1

        rows = [
            "12345,ANTH,100A,A,4.0",
            "12345,BIO,1,A,4.0",
            "12345,ANTH,2,A,4.0",
            "12345,ANTH,100,A,4.0",
        ]

        csv_content = f"{headers}\n" + "\n".join(rows)
        df_csv = pd.read_csv(io.StringIO(csv_content), dtype=str).fillna("")
        mock_get_df.return_value = df_csv

        # All map to "LS"
        mock_map.return_value = ["LS"]

        classes = pbk_styling.get_classes("12345")

        # We expect a dictionary with key "LS"
        self.assertIn("LS", classes)
        result_list = classes["LS"]

        # Expected sort order by (dept, numeric_crsnum, alpha_crsnum)
        # ANTH 2
        # ANTH 100
        # ANTH 100A
        # BIO 1

        expected = [
            {"dept": "ANTH", "crsnum": "2"},
            {"dept": "ANTH", "crsnum": "100"},
            {"dept": "ANTH", "crsnum": "100A"},
            {"dept": "BIO", "crsnum": "1"},
        ]

        self.assertEqual(len(result_list), 4)

        for i, exp in enumerate(expected):
            self.assertEqual(result_list[i]["dept"], exp["dept"])
            self.assertEqual(result_list[i]["crsnum"], exp["crsnum"])


if __name__ == "__main__":
    unittest.main()
