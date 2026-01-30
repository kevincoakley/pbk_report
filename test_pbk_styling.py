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
        )
        df = pd.read_csv(io.StringIO(csv_content), dtype=str).fillna("")
        mock_get_df.return_value = df

        # Test exact match
        result = pbk_styling.map_class_types("MATH", "101", "A")
        self.assertEqual(result, "MS")

        # Test wildcard match logic
        # 1. Match anyUD=N with course < 100 (SS)
        result = pbk_styling.map_class_types("HIST", "99", "")
        self.assertEqual(result, "SS")

        # 2. Match anyUD=Y with course >= 100 (LS) -- assuming added row
        # Add a more complex dataframe setup for this test
        csv_content_complex = (
            "courseid,department,coursenumber,courseletter,anyUD,classtype\n"
            "1,MATH,101,A,N,MS\n"
            "2,HIST,*,*,N,SS\n"
            "3,LIT,*,*,Y,LS\n"
            "4,MIX,*,*,N,SS\n"
            "5,MIX,*,*,Y,LS\n"
        )
        df_complex = pd.read_csv(io.StringIO(csv_content_complex), dtype=str).fillna("")
        mock_get_df.return_value = df_complex

        # Test LIT: anyUD=Y, course=105 -> LS
        result = pbk_styling.map_class_types("LIT", "105", "")
        self.assertEqual(result, "LS")

        # Test LIT: anyUD=Y, course=50 -> None (mismatch condition)
        result = pbk_styling.map_class_types("LIT", "50", "")
        self.assertIsNone(result)

        # Test MIX: has both N (SS) and Y (LS) rows
        # Course 10 (matches N -> SS)
        result = pbk_styling.map_class_types("MIX", "10", "")
        self.assertEqual(result, "SS")

        # Course 150 (matches Y -> LS)
        result = pbk_styling.map_class_types("MIX", "150", "")
        self.assertEqual(result, "LS")

        # Test no match
        result = pbk_styling.map_class_types("ART", "101", "A")
        self.assertIsNone(result)

        # Test file not exists
        mock_get_df.return_value = None
        result = pbk_styling.map_class_types("MATH", "101", "A")
        self.assertIsNone(result)

    @patch("pbk_styling._get_df")
    def test_get_students(self, mock_get_df):
        headers = "Full Name,First Name,Middle Name,Last Name,PID,College,Major Code,Major Description,Class Level,Gender,Cumulative Units,Cumulative GPA,Email(UCSD),Permanent Mailing Addresss Line 1,Permanent Mailing City Line 1,Permanent Mailing State Line 1,Permanent Mailing Zip Code Line 1,Permanent Mailing Country Line 1,Permanent Phone Number,Graduating Quarter,Registration Status"
        row1 = "Doe,John,M,Doe,12345,Col,Maj,Desc,U,M,100,4.0,e@mail,Addr,City,ST,12345,USA,555,2023,Reg"
        csv_content = f"{headers}\n{row1}\n"

        df = pd.read_csv(io.StringIO(csv_content), dtype=str).fillna("")
        mock_get_df.return_value = df

        students = pbk_styling.get_students()
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0]["id"], "12345")
        self.assertEqual(students[0]["country"], "United States")

        # Test file not exists
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

        csv_content = (
            f"{headers}\n{row1}\n{row2}\n{row3}\n{row4}\n{row5}\n{row6}\n{row7}\n"
        )

        df = pd.read_csv(io.StringIO(csv_content), dtype=str).fillna("")
        mock_get_df.return_value = df

        mock_map.side_effect = lambda d, n, l: "MS" if d == "MATH" else None

        classes = pbk_styling.get_classes("12345")

        self.assertIn("MS", classes)
        # Only row1 should be included
        self.assertEqual(len(classes["MS"]), 1)
        self.assertEqual(classes["MS"][0]["crsnum"], "101A")
        self.assertEqual(classes["MS"][0]["grade"], "A")

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

        mock_map.return_value = "MS"

        ap_classes = pbk_styling.get_ap_classes("12345")

        self.assertIn("MS", ap_classes)
        # Should be 1 because of deduplication on relevant cols
        self.assertEqual(len(ap_classes["MS"]), 1)
        self.assertEqual(ap_classes["MS"][0]["crsnum"], "101")

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

        mock_map.return_value = "SS"

        ib_classes = pbk_styling.get_ib_classes("12345")

        self.assertIn("SS", ib_classes)
        # Should be 1 because of deduplication
        self.assertEqual(len(ib_classes["SS"]), 1)

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
        mock_students.return_value = [{"id": "12345"}]
        mock_classes.return_value = {}
        mock_ap.return_value = {}
        mock_ib.return_value = {}
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


if __name__ == "__main__":
    unittest.main()
