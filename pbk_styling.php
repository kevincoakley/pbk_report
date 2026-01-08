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
}