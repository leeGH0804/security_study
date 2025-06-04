<?php
session_start();
require_once __DIR__ . '/../../../includes/db.php';

if (!isset($_SESSION['user_id'])) {
  header("Location: /index.php");
  exit;
}

$key = "timemachine04";
$success = isset($_GET["success"]);

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $id = trim($_POST['id']);
    $pw = $_POST['pw'];

    if (isset($_SESSION['users'][$id]) && $_SESSION['users'][$id] === $pw) {
        if (strpos($id, "admin") !== false) {
            // 문제 ID 가져오기
            $stmt = $mysqli->prepare("SELECT id FROM problems WHERE owner = 'timemachine' AND number = 4");
            $stmt->execute();
            $problem = $stmt->get_result()->fetch_assoc();

            if ($problem) {
                // 클리어 중복 확인
                $stmt = $mysqli->prepare("SELECT id FROM clears WHERE user_id = ? AND problem_id = ?");
                $stmt->bind_param("ii", $_SESSION['user_id'], $problem["id"]);
                $stmt->execute();
                $already = $stmt->get_result()->fetch_assoc();

                if (!$already) {
                    $stmt = $mysqli->prepare("INSERT INTO clears (user_id, problem_id) VALUES (?, ?)");
                    $stmt->bind_param("ii", $_SESSION['user_id'], $problem["id"]);
                    $stmt->execute();
                }
            }

            header("Location: login.php?success=1");
            exit;
        } else {
            $error = "You are not an admin.";
        }
    } else {
        $error = "Login failed!";
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Witch Hunt - Login</title>
  <?php if ($success): ?>
    <meta http-equiv="refresh" content="3;url=../../../main.php">
  <?php endif; ?>
  <style>
    body {
      background-color: black;
      color: white;
      font-family: monospace;
      text-align: center;
      padding-top: 50px;
    }
    input, button {
      margin: 5px;
      padding: 8px;
      font-size: 1em;
    }
    a {
      color: #00ff99;
      text-decoration: none;
      display: block;
      margin-top: 20px;
    }
  </style>
</head>
<body>

  <?php if ($success): ?>
    <p style="color: lime;">✅ Correct! Returning to main...</p>
  <?php else: ?>

    <h1>Login to the Witch Gathering</h1>

    <form method="post">
      <input type="text" name="id" placeholder="Enter ID" required><br>
      <input type="password" name="pw" placeholder="Enter Password" required><br>
      <button type="submit">Login</button>
    </form>

    <?php if (isset($error)) echo "<p style='color:red;'>$error</p>"; ?>

    <a href="../04.php">Back to Main</a>

  <?php endif; ?>

</body>
</html>
