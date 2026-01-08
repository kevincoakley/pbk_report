<?php

// Function to read students from CSV file
function getStudents() {
    $students = [];
    $csvFile = __DIR__ . '/pbk_screening.csv';
    
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

// Function to get class types
function getClassTypes() {
    return [
        'HU' => 'Humanities',
        'SS' => 'Social Sciences',
        'NS' => 'Natural Sciences', 
        'MA' => 'Mathematics',
        'LA' => 'Language',
    ];
}

// Function to get regular classes by student ID
function getClasses($studentId) {
    $classes = [];
    $csvFile = __DIR__ . '/pbk_screening_classes.csv';
    
    if (!file_exists($csvFile)) {
        return $classes;
    }
    
    $handle = fopen($csvFile, 'r');
    $headers = fgetcsv($handle); // Read header row

    # Added all of the class types to the array to avoid undefined index issues
    foreach (array_keys(getClassTypes()) as $type) {
        $classes[$type] = [];
    }

    while (($data = fgetcsv($handle)) !== FALSE) {
        # $type should be a randomly selected value from (HU, SS, NS, MA, LA)
        $type = array_rand(getClassTypes());

        if ($data[0] == $studentId) {        
            $classes[$type][] = [
                'dept' => $data[1],
                'crsnum' => $data[2],
                'grade' => $data[7]
            ];
        }
    }
    
    return $classes;
}

// Function to get AP classes by student ID  
function getAPClasses($studentId) {
    $apClasses = [];
    $csvFile = __DIR__ . '/pbk_screening_apclasses.csv';
    
    if (!file_exists($csvFile)) {
        return $apClasses;
    }

    $handle = fopen($csvFile, 'r');
    $headers = fgetcsv($handle); // Read header row
    
    # Added all of the class types to the array to avoid undefined index issues
    foreach (array_keys(getClassTypes()) as $type) {
        $apClasses[$type] = [];
    }

    while (($data = fgetcsv($handle)) !== FALSE) {
        # $type should be a randomly selected value from (HU, SS, NS, MA, LA)
        $type = array_rand(getClassTypes());
        
        if ($data[0] == $studentId) {
            $apClasses[$type][] = [
                'crsnum' => $data[4],
                'description' => $data[5],
                'units' => $data[8]
            ];
        }
    }
    
    return $apClasses;
}

// Function to get IB classes by student ID
function getIBClasses($studentId) {
    $ibClasses = [];
    $csvFile = __DIR__ . '/pbk_screening_ibclasses.csv';
    
    if (!file_exists($csvFile)) {
        return $ibClasses;
    }

    $handle = fopen($csvFile, 'r');
    $headers = fgetcsv($handle); // Read header row
    
    # Added all of the class types to the array to avoid undefined index issues
    foreach (array_keys(getClassTypes()) as $type) {
        $ibClasses[$type] = [];
    }

    while (($data = fgetcsv($handle)) !== FALSE) {
        # $type should be a randomly selected value from (HU, SS, NS, MA, LA)
        $type = array_rand(getClassTypes());
        
        if ($data[0] == $studentId) {
            $ibClasses[$type][] = [
                'crsnum' => $data[4],
                'description' => $data[5],
                'units' => $data[8]
            ];
        }
    }
    
    return $ibClasses;
}

// Function to get transfer classes by student ID
function getTransferClasses($studentId) {
    $transferClasses = [];
    $csvFile = __DIR__ . '/pbk_screening_transferclasses.csv';
    
    if (!file_exists($csvFile)) {
        return $transferClasses;
    }

    $handle = fopen($csvFile, 'r');
    $headers = fgetcsv($handle); // Read header row
    
    while (($data = fgetcsv($handle)) !== FALSE) {    
        if ($data[0] == $studentId) {
            $transferClasses[] = [
                'dept' => $data[3],
                'crsnum' => $data[4],
                'title' => $data[5],
                'units' => $data[8],
                'grade' => $data[9]
            ];
        }
    }
    
    return $transferClasses;
}

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
	$students = getStudents();

	foreach ($students as $i => $row) {
		$classes = getClasses($row['id']);
		$apClasses =  getAPClasses($row['id']);
		$ibClasses =  getIBClasses($row['id']);
		$transferClasses = getTransferClasses($row['id']);
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
