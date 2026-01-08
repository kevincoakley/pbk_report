<?php

// Function to read students from CSV file
function getStudents($db, $cumgpa = null, $cumunits = null, $cumgraded = null, $gqtr = null) {
    $students = [];
    $csvFile = __DIR__ . '/fake_student_dataset_100.csv';
    
    if (!file_exists($csvFile)) {
        return $students;
    }
    
    $handle = fopen($csvFile, 'r');
    $headers = fgetcsv($handle); // Read header row
    
    while (($data = fgetcsv($handle)) !== FALSE) {
        if (count($data) >= 21) {
            $student = [
                'name' => $data[0],
                'fname' => $data[1], 
                'mname' => $data[2],
                'lname' => $data[3],
                'id' => $data[4],
                'college' => $data[5],
                'major' => $data[6],
                'major_desc' => $data[7],
                'level' => $data[8],
                'sex' => $data[9],
                'cumunits' => $data[10],
                'cumgpa' => $data[11],
                'email' => $data[12],
                'pm_line1' => $data[13],
                'pm_city' => $data[14],
                'pm_state' => $data[15],
                'pm_zip' => $data[16],
                'pm_country' => $data[17],
                'pm_phone' => $data[18],
                'gradqtr' => $data[19],
                'reg_status' => $data[20],
                'major2' => '', // Not in CSV, set to empty
                'major2_desc' => '', // Not in CSV, set to empty
                'apln_term' => $data[19], // Use graduating quarter as application term
                'lang' => 'N', // Default to No
                'country' => $data[17] == 'USA' ? 'United States' : $data[17] // Convert country code
            ];
            $students[] = $student;
        }
    }
    fclose($handle);
    
    return $students;
}

// Function to generate random class names in format XXX123
function generateRandomClass() {
    $letters = '';
    $numbers = '';
    
    // Generate 3 random letters
    for ($i = 0; $i < 3; $i++) {
        $letters .= chr(rand(65, 90)); // A-Z
    }
    
    // Generate 3 random numbers
    for ($i = 0; $i < 3; $i++) {
        $numbers .= rand(0, 9);
    }
    
    return $letters . $numbers;
}

// Function to get random grade
function getRandomGrade() {
    $grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F'];
    return $grades[array_rand($grades)];
}

// Function to get class types
function getClassTypes() {
    return [
        'LA' => 'Liberal Arts',
        'SC' => 'Science',
        'MA' => 'Mathematics', 
        'EN' => 'English',
        'HI' => 'History',
        'SO' => 'Social Science',
        'AR' => 'Arts'
    ];
}

// Function to get regular classes by student ID
function getClasses($db, $studentId) {
    $classTypes = array_keys(getClassTypes());
    $classes = [];
    
    foreach ($classTypes as $type) {
        $classes[$type] = [];
        $numClasses = rand(3, 8); // Random number of classes per type
        
        for ($i = 0; $i < $numClasses; $i++) {
            $classes[$type][] = [
                'dept' => substr(generateRandomClass(), 0, 3),
                'crsnum' => substr(generateRandomClass(), 3, 3),
                'grade' => getRandomGrade()
            ];
        }
    }
    
    return $classes;
}

// Function to get AP classes by student ID  
function getAPClasses($db, $studentId) {
    $classTypes = array_keys(getClassTypes());
    $apClasses = [];
    
    foreach ($classTypes as $type) {
        $apClasses[$type] = [];
        $numClasses = rand(0, 3); // Random number of AP classes per type
        
        for ($i = 0; $i < $numClasses; $i++) {
            $className = generateRandomClass();
            $apClasses[$type][] = [
                'crsnum' => $className,
                'description' => 'AP ' . substr($className, 0, 3) . ' Course',
                'units' => rand(3, 6)
            ];
        }
    }
    
    return $apClasses;
}

// Function to get IB classes by student ID
function getIBClasses($db, $studentId) {
    $classTypes = array_keys(getClassTypes());
    $ibClasses = [];
    
    foreach ($classTypes as $type) {
        $ibClasses[$type] = [];
        $numClasses = rand(0, 2); // Random number of IB classes per type
        
        for ($i = 0; $i < $numClasses; $i++) {
            $className = generateRandomClass();
            $ibClasses[$type][] = [
                'crsnum' => $className,
                'description' => 'IB ' . substr($className, 0, 3) . ' Course',
                'units' => rand(3, 6)
            ];
        }
    }
    
    return $ibClasses;
}

// Function to get transfer classes by student ID
function getTransferClasses($db, $studentId) {
    $transferClasses = [];
    $numClasses = rand(5, 15); // Random number of transfer classes
    
    for ($i = 0; $i < $numClasses; $i++) {
        $className = generateRandomClass();
        $transferClasses[] = [
            'dept' => substr($className, 0, 3),
            'crsnum' => substr($className, 3, 3),
            'title' => 'Transfer Course ' . $className,
            'units' => rand(3, 6),
            'grade' => getRandomGrade()
        ];
    }
    
    return $transferClasses;
}

// Mock database connection
$db = null;

/* 
$students = getStudents($db, $_REQUEST['cumgpa'], $_REQUEST['cumunits'], $_REQUEST['cumgraded'], $_REQUEST['gqtr']);

if (isset($_REQUEST['usersel'])  && $_REQUEST['usersel'] == "CSVFile") {


    $heading = array(
        "Full Name",
        "First Name",
        "Middle Name",
        "Last Name",
        "PID",
        "College",
        "Major Code",
        "Major Description",
        "Class Level",
        "Gender",
        "Cumulative Units",
        "Cumulative GPA",
        "Email(UCSD)",
        "Permanent Mailing Addresss Line 1",
        "Permanent Mailing City Line 1",
        "Permanent Mailing State Line 1",
        "Permanent Mailing Zip Code Line 1",
        "Permanent Mailing Country Line 1",
        "Permanent Phone Number",
        "Graduating Quarter",
        "Registration Status"

    );

	header("Content-type: application/csv");
	header("Content-Disposition: attachment; filename=pbk_screening.csv");
	$fp = fopen('php://output', 'w');
	fputcsv($fp, $heading);

	foreach ($students as $row) {
		fputcsv($fp, array(
            $row["name"],
            $row["fname"],
            $row["mname"],
            $row["lname"],
            $row["id"],
            $row["college"],
            $row["major"],
            $row['major_desc'],
            $row["level"],
            $row["sex"],
            $row["cumunits"],
            $row["cumgpa"],
            $row["email"],
            $row["pm_line1"],
            $row["pm_city"],
            $row["pm_state"],
            $row["pm_zip"],
            $row["pm_country"],
            $row["pm_phone"],
            $row["gradqtr"],
            $row["reg_status"]
        ));
	}
	fclose($fp);
} else {

// This program creates an html file for the PBK people to print via the web
// It also creates a file 'pbklist.txt' for the PBK people to send to their printer or whoever
// It first checks GPA and Unit info, then prints student coursework in catagories for review 
*/
?>
<style>
table {
	border-collapse: collapse;
}

table.student {
	border: 1px solid;
	width: 100%;
}

table.classList {
	border: none;
	width: 100%;
}

table.student .info > td {
	border: 1px solid;
	padding-left: 5px;
}

table.classList > tbody > tr > td {
	padding-left: 5px;
}

table.classList > tbody > tr > td:not(:first-child) {
	border-left: 1px solid;
}

h5, h6 {
  margin-bottom: 5px;
}

.class-title {
	font-size: small;
}

</style>
	<?php 
	// Initialize students data from CSV file
	$students = getStudents($db, $_REQUEST['cumgpa'] ?? null, $_REQUEST['cumunits'] ?? null, $_REQUEST['cumgraded'] ?? null, $_REQUEST['gqtr'] ?? null);

	foreach ($students as $i => $row) {
		$classes = getClasses($db, $row['id']);
		$apClasses =  getAPClasses($db, $row['id']);
		$ibClasses =  getIBClasses($db, $row['id']);
		$transferClasses = getTransferClasses($db, $row['id']);
	?>
			<p style="page-break-before:always">&nbsp;</p>
			<table class="student">
				<tr class="info">
					<td width="2%"><?= $i + 1 ?></td>
					<td colspan="2" width="25%">
					<?php if($row['level'] != "SR") : ?>
						<font color="#FF0000" face="Arial, Helvetica, sans-serif"><?= $row['name'] ?></font>
					<?php else : ?>
						<?= $row['name'] ?>
					<?php endif ?>
					</td>
					<td width="15%"><?= $row['id'] ?></td>
					<td width="10%"><small><strong>GPA</strong></small> <?= $row['cumgpa'] ?></td>
					<td width="10%"><small><strong>Units</strong></small> <?= $row['cumunits'] ?></td>
					<td width="10%">
						<?= $row['major'] ?>-<?= $row['major_desc']; ?>
						<?php if($row['major2'] != "") : ?>
							<br><?= $row['major2'] ?>-<?= $row['major2_desc'] ?>
						<?php endif ?>
					</td>
					<td width="15%"><small><strong>Apln Term</strong></small> <?= $row['apln_term'] ?><br /><small><strong>Grad Qtr</strong></small> <?= $row['gradqtr'] ?></td>
					<td width="10%"><small><strong>Coll</strong></small> <?= $row['college'] ?><br /><small><strong>Lvl</strong></small> <?= $row['level'] ?></td>
				</tr>
		<tr>
			<td colspan="9">
				<table class="classList">
					<tr>
					<?php foreach(getClassTypes() AS $classType => $className): ?>
					<?php $numClasses = 0; ?>
						<td valign="top" width="14%">
						<h5><?= $className ?></h5>
							<table width="100%" style="border: none;" cellpadding="0">
							<?php if($classType == 'LA' && $row['lang'] == 'Y'): ?>
							<tr><td colspan="2">LangProficiency</td></tr>
							<?php endif ?>
							<?php foreach ($classes[$classType] as $rowclss): ?>
								<?php if($rowclss['grade']) {
									$numClasses++;
								} ?>
								<tr>
									<td><?= $rowclss['dept'] ?> <?= $rowclss['crsnum'] ?></td>
									<td><?= $rowclss['grade'] ?></td>
								</tr>
							<?php endforeach ?>
							</table>
							<br />
							<strong># of classes: <?= $numClasses ?></strong>
							<?php if(!empty($apClasses[$classType])): ?>
							<h6>AP Classes</h6>
							<?php endif ?>
							<table width="100%" style="border: none;" cellpadding="0">
							<?php foreach ($apClasses[$classType] as $rowclss): ?>
								<tr>
									<td><?= $rowclss['crsnum'] ?> <span class="class-title"><?= $rowclss['description'] ?></span></td>
									<td><?= $rowclss['units'] ?></td>
								</tr>
							<?php endforeach ?>
							</table>
							<?php if(!empty($ibClasses[$classType])): ?>
							<h6>IB Classes</h6>
							<?php endif ?>
							<table width="100%" style="border: none;" cellpadding="0">
							<?php foreach ($ibClasses[$classType] as $rowclss): ?>
								<tr>
									<td><?= $rowclss['crsnum'] ?> <span class="class-title"><?= $rowclss['description'] ?></span></td>
									<td><?= $rowclss['units'] ?></td>
								</tr>
							<?php endforeach ?>
							</table>
							<?php if($classType=='LA' && $row['pm_country'] != 'US'): ?>
								<h6>Home Country</h6>
								<?= $row['country'] ?>
							<?php endif ?>
						</td>
						<?php endforeach ?>
	
						<td valign="top" width="30%">
			<h5>Transfer Classes</h5>
			<table width="100%" cellpadding="0" border="0">
			<?php foreach ($transferClasses as $rowclss): ?>
				 <?php if ($rowclss['dept'] != ""): ?>
					<tr><td><?= $rowclss['dept'] ?></td><td><?= $rowclss['crsnum'] ?></td><td class="class-title"><?= $rowclss['title'] ?></td><td><?= $rowclss['units'] ?></td><td><?= $rowclss['grade'] ?></td></tr>
				<?php endif ?>
			<?php endforeach ?>

			</table>
			</td>
			</tr>
			</table>


			</table>
	<?php }
