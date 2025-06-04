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

// 문제 ID 확보 (flag는 사용하지 않음)
$stmt = $mysqli->prepare("SELECT id FROM problems WHERE owner = ? AND number = ?");
$stmt->bind_param("si", $owner, $number);
$stmt->execute();
$problem = $stmt->get_result()->fetch_assoc();
if (!$problem) {
    die("문제가 존재하지 않습니다.");
}

$correct_word = "panther";

if (!isset($_SESSION["gear_angle"])) {
    $_SESSION["gear_angle"] = 0;
}

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $input = trim($_POST["flag"] ?? "");

    if ($input === $correct_word) {
        $_SESSION["gear_angle"] += 50;
    } else {
        $_SESSION["last_error"] = "No Change.";
    }
    header("Location: " . $_SERVER['PHP_SELF']);
    exit;
}


if ($_SESSION["gear_angle"] >= 1800) {
        // DB 클리어 기록
        $stmt = $mysqli->prepare("SELECT id FROM clears WHERE user_id = ? AND problem_id = ?");
        $stmt->bind_param("ii", $user_id, $problem["id"]);
        $stmt->execute();
        $already = $stmt->get_result()->fetch_assoc();

        if (!$already) {
            $stmt = $mysqli->prepare("INSERT INTO clears (user_id, problem_id) VALUES (?, ?)" );
            $stmt->bind_param("ii", $user_id, $problem["id"]);
            $stmt->execute();
        }

        $success = true;
}


$success = ($_SESSION["gear_angle"] >= 1800);
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TimeMachine06</title>
  <style>
    body {
      background-color: #090909;
      color: white;
      text-align: center;
      font-family: Arial, sans-serif;
    }
    input[type="text"] {
      padding: 8px;
      font-size: 16px;
      margin: 10px 0;
      border: none;
      border-radius: 5px;
    }
    button {
      padding: 8px 16px;
      font-size: 16px;
      background-color: #444;
      color: white;
      border: none;
      border-radius: 5px;
      cursor: pointer;
    }
    button:hover {
      background-color: #666;
    }
    a {
      color: #00ff99;
      text-decoration: none;
    }
    .message-area {
      margin-top: 15px;
      font-size: 1em;
    }
    .success {
      color: lime;
    }
    .error {
      color: red;
    }
  </style>
</head>
<body>

<?php if ($success): ?>
  <p class="message-area success">✅ Success! Returning to main...</p>
  <meta http-equiv="refresh" content="3;url=../../main.php">
<?php else: ?>
  <h1>No.06 Industrial Revolution</h1>
  <p>Input the correct word to turn the gear 5 times!</p>
  <br><br>
  <br><br>
  <img src="../../img/gear.png" alt="Gear" style="width:200px; height:200px; transform: rotate(<?= $_SESSION["gear_angle"] ?>deg); transition: transform 0.5s;">

  <br><br>
  <br><br>
  <br><br>

  <form method="post">
    <input type="text" name="flag" placeholder="Enter word" required />
    <br>
    <button type="submit">SUBMIT</button>
  </form>

  <?php if (isset($_SESSION["last_error"])): ?>
    <p style='color:red;'><?= $_SESSION["last_error"]; unset($_SESSION["last_error"]); ?></p>
  <?php endif; ?>

  <p>Current Gear Angle: <?= $_SESSION["gear_angle"] ?>°</p>

  <p style="margin-top:30px;">Hint: The correct word is in <b>rockyou.txt</b>. Use <b>Thread 1</b></p>
<?php endif; ?>

<br><br>
<a href="../../main.php">Back</a>
<?php include '../../includes/ping_loader.php'; ?>
<script src="../../js/inactivity.js"></script>

</body>
</html>
