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
$host = "localhost";
$user = "moon_user";
$pass = "1q2w3e4r";
$dbname = "moon";

function dbconnect($host, $user, $pass, $dbname) {
  $conn = mysqli_connect($host, $user, $pass, $dbname);
  if (!$conn) {
    die("❌ DB Connection Failed: " . mysqli_connect_error());
  }
  return $conn;
}

if ($_SERVER["REQUEST_METHOD"] === "POST" && isset($_POST["flag"])) {
  $submitted_flag = trim($_POST["flag"]);
  if ($submitted_flag === $problem["flag"]) {
    $stmt = $mysqli->prepare("SELECT id FROM clears WHERE user_id = ? AND problem_id = ?");
    $stmt->bind_param("ii", $_SESSION['user_id'], $problem["id"]);
    $stmt->execute();
    $already = $stmt->get_result()->fetch_assoc();

    if (!$already) {
      $stmt = $mysqli->prepare("INSERT INTO clears (user_id, problem_id) VALUES (?, ?)" );
      $stmt->bind_param("ii", $_SESSION['user_id'], $problem["id"]);
      $stmt->execute();
    }

    header("Location: ?success=1");
    exit;
  } else {
    $error = "Wrong.";
  }
}

$success = isset($_GET["success"]);

if (!$success) {
  $conn = dbconnect($host, $user, $pass, $dbname);

  $name = trim($_SERVER['HTTP_X_MOON_NAME'] ?? '');
  $num = 2;
  $state = 'arrive';

  if (preg_match("/from/i", $name)) {
    echo("<br>Access Denied!<br><br>");
    echo(htmlspecialchars($name));
    exit();
  }

  $count_ck = mysqli_fetch_array(mysqli_query($conn, "SELECT COUNT(*) FROM moon_landing"));
  if ($count_ck[0] >= 70) {
    mysqli_query($conn, "DELETE FROM moon_landing");
  }

  $ck_by_name = mysqli_fetch_array(mysqli_query($conn, "SELECT name, num FROM moon_landing WHERE name='" . addslashes($name) . "'"));
  if (!$ck_by_name && $name !== '') {
    mysqli_query($conn, "INSERT INTO moon_landing(name, num, state) VALUES('{$name}', '{$num}', '{$state}')");
  }

  $ck_armstrong = mysqli_fetch_array(mysqli_query($conn, "SELECT name, num FROM moon_landing WHERE name='Armstrong'"));

  if ($ck_armstrong && isset($ck_armstrong['name']) && $ck_armstrong['name'] === "Armstrong" && intval($ck_armstrong['num']) === 1) {
    $show_moon_image = true;
    mysqli_query($conn, "DELETE FROM moon_landing WHERE name='Armstrong'");
  } elseif ($ck_armstrong && $ck_armstrong['name'] === "Armstrong") {
    $message = "We are the first!";
    mysqli_query($conn, "DELETE FROM moon_landing WHERE name='Armstrong'");
  } elseif ($ck_by_name) {
    $message = htmlentities($ck_by_name['name']) . " is the second to arrive.";
  }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title><?= $key ?> Problem</title>
  <?php if ($success): ?>
    <meta http-equiv="refresh" content="3;url=../../main.php">
  <?php endif; ?>
  <style>
    body {
      background: black;
      color: white;
      font-family: monospace;
      font-size: 10pt;
      text-align: center;
    }
    .moon-image {
      margin-top: 30px;
    }
    .moon-image img {
      max-width: 300px;
      display: block;
      margin: 10px auto;
    }
    .flag-text {
      color: #00ff99;
      margin-top: 10px;
      font-weight: bold;
    }
    .hint {
      margin-top: 40px;
      color: #ccc;
    }
    input[type="text"] {
      padding: 5px;
    }
    button {
      padding: 5px 10px;
      margin-left: 10px;
    }
    a {
      color: #00ff99;
      text-decoration: none;
    }
  </style>
</head>
<body>
  <h1>No08. First Moon Landing</h1>

  <?php if ($success): ?>
    <p style="color: lime;">✅ Correct! Returning to main page...</p>
  <?php else: ?>
    <p>On July 20, 1969, mankind set foot on the Moon for the first time.
    Send the captain's name as data.</p>

    <form method="post">
      <input type="text" name="flag" placeholder="Enter FLAG" required />
      <button type="submit">SUBMIT</button>
    </form>

    <?php if (isset($show_moon_image) && $show_moon_image): ?>
      <div class="moon-image">
        <img src="../../img/moon.png" alt="Moon Landing">
        <div class="flag-text">🏳️ Flag: That's one small step for a man, one giant leap for mankind.</div>
      </div>
    <?php elseif (isset($message)): ?>
      <p style="color: #00ff99; margin-top: 20px;"><?= $message ?></p>
    <?php endif; ?>

    <?php if (isset($error)) echo "<p style='color:red;'>$error</p>"; ?>

    <div class="hint">
      <p><b>How to Send Data via Header</b></p>
      <p><code>X-Moon-Name: name</code></p>
      <h2 style="color: red;">HINT</h2>
      <p><code>INSERT INTO moon_landing(name, num, state) VALUES('{$name}', '2', 'arrive')</code></p>
    </div>
  <?php endif; ?>

  <br><br>
  <a href="../../main.php">Back to Main</a>
<?php include '../../includes/ping_loader.php'; ?>
<script src="../../js/inactivity.js"></script>

</body>
</html>
