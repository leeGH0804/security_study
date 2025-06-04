<?php
ini_set('display_errors', 1);
error_reporting(E_ALL);
session_start();
require_once __DIR__ . '/../../includes/db.php';

if (!isset($_SESSION['user_id'])) {
  header("Location: /index.php");
  exit;
}

$user_id = $_SESSION['user_id'];
$owner = "timemachine";
$filename = basename(__FILE__);
$number = (int) preg_replace('/[^0-9]/', '', $filename);
$key = $owner . str_pad($number, 2, "0", STR_PAD_LEFT);

$stmt = $mysqli->prepare("SELECT id, flag FROM problems WHERE owner = ? AND number = ?");
$stmt->bind_param("si", $owner, $number);
$stmt->execute();
$problem = $stmt->get_result()->fetch_assoc();

if (!$problem) {
  die("문제가 존재하지 않습니다.");
}

$success = false;

if ($_SERVER["REQUEST_METHOD"] === "POST" && isset($_POST["flag"])) {
  $submitted_flag = trim($_POST["flag"]);
  if ($submitted_flag === $problem["flag"]) {
    $stmt = $mysqli->prepare("SELECT id FROM clears WHERE user_id = ? AND problem_id = ?");
    $stmt->bind_param("ii", $user_id, $problem["id"]);
    $stmt->execute();
    $already = $stmt->get_result()->fetch_assoc();

    if (!$already) {
      $stmt = $mysqli->prepare("INSERT INTO clears (user_id, problem_id) VALUES (?, ?)");
      $stmt->bind_param("ii", $user_id, $problem["id"]);
      $stmt->execute();
    }

    header("Location: ?success=1");
    exit;
  } else {
    $error = "Wrong.";
  }
}

$success = isset($_GET["success"]);
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TimeMachine05</title>
  <?php if ($success): ?>
    <meta http-equiv="refresh" content="3;url=../../main.php">
  <?php endif; ?>
  <style>
    body {
      margin: 0;
      padding: 0;
      background-color: black;
      color: white;
      font-family: Arial, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      text-align: center;
    }
    h1 {
      margin-top: 20px;
      font-size: 2.5em;
    }
    a {
      color: #00ff99;
      text-decoration: none;
      margin-top: 20px;
    }
    input[type="text"], button {
      padding: 10px;
      margin: 10px;
      font-size: 16px;
    }
  </style>
</head>
<body>
  <h1>No.05 Scientific Revolution</h1>

  <?php if ($success): ?>
    <p style="color: lime;">✅ Correct! Returning to the main page...</p>
  <?php else: ?>
    <p>To prove our claim, we must use a telescope.</p>

    <iframe id="telescope" width="0" height="0" frameborder="0" srcdoc='
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <title>TimeMachine05</title>
      </head>
      <body style="background-color:black; display:flex; align-items:center; justify-content:center; height:100vh;">
        <img src="../../img/constellation.png" style="max-width:90%;">
      </body>
      </html>
    '></iframe>

    <form method="post">
      <input type="text" name="flag" placeholder="Enter the constellation" required />
      <button type="submit">SUBMIT</button>
    </form>
    <?php if (isset($error)) echo "<p style='color:red;'>$error</p>"; ?>
  <?php endif; ?>

  <a href="../../main.php">Back to Main</a>
<?php include '../../includes/ping_loader.php'; ?>
<script src="../../js/inactivity.js"></script>

</body>
</html>
