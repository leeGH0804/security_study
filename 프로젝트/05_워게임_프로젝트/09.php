<?php
session_start();
ini_set('display_errors', 1);
error_reporting(E_ALL);
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

// 문제 기본 값
$version = "1";
$prev_hash = "ef7797e13d3a75526946a3bcf00daec9fc9c9c4d51ddc7cc5df888f74dd434d1";
$merkle = "7975edd9e7393c229e744913fe0d0bb86fb4cf46906e2e51152137e20ad15590";
$time = "2025-04-30 11:00:00";
$bits = "00000fffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
$difficulty = "00000";
$middle_pattern = "aaa";

$nonce = "";
$hash = "";
$success = false;

if ($_SERVER["REQUEST_METHOD"] === "POST" && isset($_POST["nonce"])) {
  $nonce = trim($_POST["nonce"]);
  $header_data = $version . $prev_hash . $merkle . $time . $bits . $nonce;
  $hash = hash("sha256", $header_data);

  if (substr($hash, 0, strlen($difficulty)) === $difficulty &&
      strpos($hash, $middle_pattern) !== false) {

    // 정답 제출 확인
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
    $error = "❌ Invalid hash. It must start with '{$difficulty}' and contain '{$middle_pattern}'.";
  }
}

$success = isset($_GET["success"]);
?>

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TimeMachine09</title>
  <?php if ($success): ?>
    <meta http-equiv="refresh" content="3;url=../../main.php">
  <?php endif; ?>
  <style>
    body {
      background: black;
      color: white;
      font-family: monospace;
      text-align: center;
      padding: 30px;
    }
    table {
      margin: 0 auto;
      border-collapse: collapse;
    }
    th, td {
      padding: 8px 16px;
      border: 1px solid #444;
    }
    input[type="text"] {
      width: 100px;
      text-align: center;
    }
    .green { color: #00ff00; }
    .red { color: red; }
  </style>
</head>
<body>
<?php if ($success): ?>
  <p class="green">✅ Mining success! Back to main...</p>
  <img src="../../img/success_crypto.png" alt="Mining Success" style="margin-top:20px; width:200px;">
<?php else: ?>

  <h1>No.09 Cryptocurrency Mining</h1>

  <form method="post">
    <table>
      <tr><th>Version</th><td><?= $version ?></td></tr>
      <tr><th>Previous Hash</th><td><?= $prev_hash ?></td></tr>
      <tr><th>Merkle Hash</th><td><?= $merkle ?></td></tr>
      <tr><th>Time</th><td><?= $time ?></td></tr>
      <tr><th>Bits</th><td><?= $bits ?></td></tr>
      <tr>
        <th>Nonce</th>
        <td><input type="text" name="nonce" value="<?= htmlspecialchars($nonce) ?>" required></td>
      </tr>
      <tr>
        <th>SHA-256 Hash</th>
        <td class="<?= $hash && !isset($error) ? 'green' : 'red' ?>">
          <?= $hash ?: 'Submit nonce to calculate' ?>
        </td>
      </tr>
    </table>
    <br>
    <input type="submit" value="Mine">
  </form>

  <a href="machine.py" download style="color:#00ffff; display:block; margin: 20px 0;">
    📥 machine
  </a>

  <?php if (isset($error)) echo "<p class='red'>$error</p>"; ?>

<?php endif; ?>

<br><br>
<a href="../../main.php" style="color:#00ff99;">Back to Main</a>
<?php include '../../includes/ping_loader.php'; ?>
<script src="../../js/inactivity.js"></script>

</body>
</html>
