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

if (isset($_GET['hint']) && $_GET['hint'] === 'hint') {
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TimeMachine02</title>
  <style>
    body {
      margin: 0;
      background: black;
      color: white;
      font-family: monospace;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      text-align: center;
    }
    img {
      max-width: 90%;
      height: auto;
      margin-bottom: 30px;
    }
    .back-link {
      margin-top: 20px;
      color: #00ff99;
      text-decoration: none;
      font-size: 1.2em;
    }
  </style>
</head>
<body>
  <h1>No.02 Ancient Egypt</h1>
  <h2>Hint: Decode the Hieroglyphs</h2>
  <img src="../../img/hieroglyphs_hint.png" alt="Hieroglyphs Hint">
  <a class="back-link" href="02.php">Back to Problem</a>

</body>
</html>

<?php
exit;
}


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
    $error = "Incorrect.";
  }
}

$success = isset($_GET["success"]);
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TimeMachine02</title>
  <style>
    body {
      margin: 0;
      background: black;
      color: white;
      font-family: monospace;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 50px 20px;
      overflow-x: hidden;
      text-align: center;
    }
    h1 {
      margin-bottom: 10px;
    }
    .hint-text {
      color: darkred;
      font-size: 1em;
      margin-bottom: 10px;
    }
    .insert-image {
      max-width: 80%;
      height: auto;
      margin: 20px 0;
    }
    .input-area {
      margin-top: 30px;
      display: flex;
      gap: 10px;
      justify-content: center;
    }
    input[type="text"] {
      padding: 6px;
      font-size: 1em;
      width: 250px;
    }
    button {
      padding: 6px 12px;
      font-size: 1em;
      cursor: pointer;
    }
    .message-area {
      margin-top: 20px;
      font-size: 1em;
    }
    .message-area.success {
      color: lime;
    }
    .message-area.error {
      color: red;
    }
    .back-link {
      margin-top: 30px;
      color: #00ff99;
      text-decoration: none;
    }
  </style>
  <?php if ($success): ?>
    <meta http-equiv="refresh" content="4;url=../../main.php">
  <?php endif; ?>
</head>
<body>

<?php if ($success): ?>
  <div class="message-area success">✅ Correct! Returning to the main page...</div>
<?php else: ?>

  <h1>No.02. Ancient Hieroglyphs</h1>
  <p>Please enter the message:</p>
  <p class="hint-text">hint=hint</p>

  <img src="../../img/hieroglyphs.png" class="insert-image" alt="Hieroglyphs">

  <div class="input-area">
    <form method="post">
      <input type="text" name="flag" placeholder="Enter FLAG" required />
      <button type="submit">Submit</button>
    </form>
  </div>

  <?php if (isset($error)): ?>
    <div class="message-area error"><?= htmlspecialchars($error) ?></div>
  <?php endif; ?>

<?php endif; ?>

<a class="back-link" href="../../main.php">Back to Main</a>
<?php include '../../includes/ping_loader.php'; ?>
<script src="../../js/inactivity.js"></script>

</body>
</html>
