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

// 문제 불러오기
$stmt = $mysqli->prepare("SELECT id, flag FROM problems WHERE owner = ? AND number = ?");
$stmt->bind_param("si", $owner, $number);
$stmt->execute();
$problem = $stmt->get_result()->fetch_assoc();

if (!$problem) {
  die("문제가 존재하지 않습니다.");
}

$success = false;
$search_results = [];
$error = "";

// 철학자 검색용 별도 DB 연결
$host = "localhost";
$user = "greece_user";
$pass = "1q2w3e4r";
$dbname = "greece";

$conn = new mysqli($host, $user, $pass, $dbname);
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// 처리 로직
if ($_SERVER["REQUEST_METHOD"] === "POST") {

  if (isset($_POST["flag"])) {
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

  } elseif (isset($_POST["name"])) {
    $name = $_POST["name"];
    $query = "SELECT name, quote FROM philosophers WHERE name LIKE '%$name%'";
    $result = $conn->query($query);

    if ($result && $result->num_rows > 0) {
      while ($row = $result->fetch_assoc()) {
        $search_results[] = $row;
      }
    } else {
      $error = "No matching philosopher found.";
    }
  }
}

$success = isset($_GET["success"]);
?>

<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>TimeMachine03</title>
  <style>
    body {
      margin: 0;
      background: black;
      color: white;
      font-family: monospace;
      text-align: center;
      padding: 50px 20px;
    }
    input[type="text"] {
      padding: 8px;
      font-size: 1em;
      width: 250px;
    }
    button {
      padding: 8px 16px;
      font-size: 1em;
      margin-left: 10px;
      cursor: pointer;
    }
    table {
      margin-top: 30px;
      border-collapse: collapse;
      width: 80%;
      margin-left: auto;
      margin-right: auto;
    }
    th, td {
      border: 1px solid #777;
      padding: 10px;
      font-size: 1em;
    }
    th {
      background-color: #999;
    }
    td {
      background-color: #666;
    }
    .back-link {
      margin-top: 50px;
      display: block;
      color: #00ff99;
    }
  </style>

  <?php if ($success): ?>
    <meta http-equiv="refresh" content="3;url=../../main.php">
  <?php endif; ?>
</head>
<body>

<?php if ($success): ?>
  <p style="color: lime;">✅ Correct! Returning to the main page...</p>
<?php else: ?>

<h1>No.03 Ancient Greek Forum</h1>
<p>Enter the name of a philosopher:</p>

<form method="post">
    <input type="text" name="name" placeholder="e.g., Socrates" required />
    <button type="submit">Search</button>
</form>

<?php if (!empty($search_results)): ?>
    <table>
        <thead>
            <tr>
                <th>Philosopher</th>
                <th>Quote</th>
            </tr>
        </thead>
        <tbody>
            <?php foreach ($search_results as $row): ?>
                <tr>
                    <td><?= htmlspecialchars($row['name']) ?></td>
                    <td><?= htmlspecialchars($row['quote']) ?></td>
                </tr>
            <?php endforeach; ?>
        </tbody>
    </table>
<?php endif; ?>

<div style="margin-top: 50px;">
  <h2>Submit the quote</h2>
  <form method="post">
      <input type="text" name="flag" placeholder="Something different..." required />
      <button type="submit">SUBMIT</button>
  </form>
  <?php if (isset($error)) echo "<p style='color:red;'>$error</p>"; ?>
</div>

<?php endif; ?>

<br><br>
<a href="../../main.php" class="back-link">Back to Main</a>
<?php include '../../includes/ping_loader.php'; ?>
<script src="../../js/inactivity.js"></script>

</body>
</html>
