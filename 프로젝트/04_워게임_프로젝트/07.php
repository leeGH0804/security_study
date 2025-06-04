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
$agent = $_SERVER['HTTP_USER_AGENT'] ?? '';
$date = $_SERVER['HTTP_DATE'] ?? '';

$hints = [];
if ($agent === 'Madeleine') {
  switch ($date) {
    case '1932-06-14':
      $hints[] = "We have recovered partial information about the Enigma device:";
      $hints[] = "MODEL: Enigma M3";
      $hints[] = "REFLECTOR: UKW B";
      $hints[] = "FOREIGN CHAR: IGNORE";
      $hints[] = "Agent Madeleine will return on 1935-09-21.";
      break;
    case '1935-09-21':
      $hints[] = "We have acquired additional intelligence on the Enigma device.";
      $hints[] = "ROTOR1 = 8";
      $hints[] = "POSITION1 = E";
      $hints[] = "RING1 = 3";
      $hints[] = "Agent Madeleine will transmit again on 1938-03-12.";
      break;
    case '1938-03-12':
      $hints[] = "This time, we have intercepted critical wiring information.";
      $hints[] = "PLUGBOARD: cw nu bd gr eh is ky";
      $hints[] = "The next scheduled contact is set for 1940-05-10.";
      break;
    case '1940-05-10':
      $hints[] = "We have obtained details about the second rotor of the Enigma machine.";
      $hints[] = "ROTOR2 = 5";
      $hints[] = "POSITION2 = F";
      $hints[] = "RING2 = 12";
      $hints[] = "The next message will arrive on 1941-11-03. We’ll see you then.";
      break;
    case '1941-11-03':
      $hints[] = "We have recovered partial information about the final rotor.";
      $hints[] = "Unfortunately, our agent's identity was compromised — the exact type of ROTOR3 could not be confirmed.";
      $hints[] = "But before the line went dead, this much was clear:";
      $hints[] = "POSITION3 = R";
      $hints[] = "RING3 = 9";
      $hints[] = "ROTOR3 = ??? (unknown)";
      $hints[] = "There will be no more messages. Good luck.";
      break;
  }
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
    $error = "Wrong.";
  }
}

$success = isset($_GET["success"]);
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TimeMachine07</title>
  <?php if ($success): ?>
    <meta http-equiv="refresh" content="3;url=../../main.php">
  <?php endif; ?>
  <style>
    body {
      background: black;
      color: #cccccc;
      font-family: monospace;
      text-align: center;
      padding-top: 100px;
    }
    .highlight {
      font-size: 1.5em;
      margin-top: 20px;
    }
    a {
      color: #00ffff;
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <?php if ($success): ?>
    <p style="color: lime;">✅ Correct! Redirecting to the main page...</p>
  <?php else: ?>
    <h1>No.07 Enigma</h1>
    <p>
      To access this transmission, ensure your <strong>User-Agent</strong> is set to <code>"Madeleine"</code><br>
      and your <strong>Date</strong> header is exactly <code>"1932-06-14"</code>.
    </p>

    <p class="highlight">
      An encrypted message has been intercepted:
    </p>
    <p class="highlight">
      🔐 <strong>vxxps fucwn chrfd</strong>
    </p>

    <p>
      Use the <a href="https://cryptii.com/pipes/enigma-decoder" target="_blank">decode machine</a> to try decrypting it.
    </p>

    <?php if (!empty($hints)): ?>
      <div class="highlight" style="text-align: left; display: inline-block; max-width: 600px;"> <p>📡 Memo:</p>
        <?php foreach ($hints as $hint): ?>
          <p><?= htmlspecialchars($hint) ?></p>
        <?php endforeach; ?>
      </div>
    <?php endif; ?>

    <form method="post">
      <input type="text" name="flag" placeholder="Enter DECODE" required />
      <button type="submit">SUBMIT</button>
    </form>
    <?php if (isset($error)) echo "<p style='color:red;'>$error</p>"; ?>
  <?php endif; ?>
  <br><br>
  <a href="../../main.php">Back to Main</a>
<?php include '../../includes/ping_loader.php'; ?>
<script src="../../js/inactivity.js"></script>

</body>
</html>
