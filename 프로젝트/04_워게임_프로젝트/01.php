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
  <title>TimeMachine01</title>
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
    }

    h1 {
      margin-bottom: 10px;
      z-index:3;
    }

    .hint-text {
      color: darkred;
      font-size: 1em;
      margin-bottom: 10px;
      z-index:3;
    }

    .fire-img {
      display: block;
      margin: 100px auto 30px auto;
      width: 500px;
      max-width: 80%;
      height: auto;
      opacity: 0;
      transform: scale(0.8);
      transition: opacity 2s ease-in;
      z-index: 5;
      pointer-events: none;
    }

    .fire-img.show {
      opacity: 1;
    }

    .input-area {
      display: flex;
      justify-content: center;
      gap: 10px;
      z-index: 3;
    }

    .corner-note {
      position: absolute;
      top: calc(50% + 110px);
      left: calc(50% + 40px);
      color: transparent;
      user-select: text;
      z-index: 3;
      pointer-events: auto;
    }

    .corner-note::selection {
      color: orange;
      background-color: black;
    }

    form {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 8px;
      margin-top: 20px;
      flex-wrap: wrap;
    }

    input[type="text"] {
      padding: 6px;
      font-size: 0.9em;
      width: 180px;
    }

    .back-link {
      margin-top: 50px;
      text-align: center;
      z-index: 3;
      color: #00ff99;
    }

    .light-effect {
      position: absolute;
      top: 100px;
      left: 50%;
      transform: translateX(-50%);
      width: 800px;
      height: 800px;
      background: radial-gradient(circle at center, rgba(255, 120, 0, 0.4), transparent 70%);
      opacity: 0;
      z-index: 1;
      transition: opacity 2s ease-in;
      pointer-events: none;
    }

    .light-effect.show {
      opacity: 1;
    }

    @media (max-width: 600px) {
      .fire-img {
        width: 80vw;
      }
    }

    button {
      padding: 6px 12px;
      font-size: 0.9em;
      cursor: pointer;
    }

    .message-area {
      margin-top: 20px;
      text-align: center;
      font-size: 1em;
    }

    .message-area.success {
      color: lime;
    }

    .message-area.error {
      color: red;
    }

    #overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: black;
      opacity: 1;
      z-index: 2;
      transition: background-color 2s ease-in, opacity 2s ease-in;
      pointer-events: none;
    }

    #overlay.show {
      background-color: rgba(255, 120, 0, 0.5);
      opacity: 0;
    }

  </style>

  <?php if ($success): ?>
    <meta http-equiv="refresh" content="4;url=../../main.php">
  <?php endif; ?>
</head>
<body>
  <h1>No.01 Prehistory</h1>
  <p>Please enter the message:</p>
  <p class="hint-text">Hint: Discover the fire hidden in the darkness.</p>

  <div id="overlay"></div>
  <div class="light-effect show"></div>
  <img class="fire-img" id="fireImage" src="../../img/fire.png">

  <div class="corner-note" id="cornerNote"></div>

  <div class="input-area">
    <form method="post">
      <input type="text" name="flag" placeholder="Enter Hidden Message" required />
      <button type="submit">Submit</button>
    </form>
  </div>

  <?php if ($success): ?>
    <div class="message-area success">✅ Correct! Returning to the main page...</div>
  <?php elseif (isset($error)): ?>
    <div class="message-area error"><?= htmlspecialchars($error) ?></div>
  <?php endif; ?>

  <div class="light-effect <?= $success ? 'show' : '' ?>" id="lightEffect"></div>

  <div class="back-link">
    <a href="../../main.php" style="color: #00ff99;">Back to Main</a>
  </div>

  <script>
    const hintText = <?= json_encode(str_split($problem["flag"])) ?>;
    document.getElementById("cornerNote").innerText = hintText.join("");

  <?php if ($success): ?>
    setTimeout(() => {
      document.getElementById("fireImage").classList.add('show');
      document.getElementById("lightEffect").classList.add('show');
      document.getElementById("overlay").classList.add('show');
    }, 100);
  <?php endif; ?>
</script>
<?php include '../../includes/ping_loader.php'; ?>
<script src="../../js/inactivity.js"></script>

</body>
</html>
