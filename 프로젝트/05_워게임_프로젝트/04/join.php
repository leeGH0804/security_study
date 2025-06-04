<?php
session_start();
require_once __DIR__ . '/../../../includes/db.php';

if (!isset($_SESSION['user_id'])) {
  header("Location: /index.php");
  exit;
}

// DB 내 users 테이블을 대신 사용하는 방식이 아니라면, 여전히 세션 사용자 목록 유지 필요 (문제 의도대로)
if (!isset($_SESSION['users'])) {
    $_SESSION['users'] = []; // 회원 정보 저장 (id => pw)
}

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $id = trim($_POST['id']);
    $pw = $_POST['pw'];

    if ($id === "admin") {
        $error = "This ID cannot be used.";
    } elseif (isset($_SESSION['users'][$id])) {
        $error = "This ID already exists.";
    } else {
        $_SESSION['users'][$id] = $pw;
        $message = "Registration successful!";
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Witch Hunt - Join</title>
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

  <h1>Join the Witch Gathering</h1>

  <form method="post">
    <input type="text" name="id" placeholder="Enter ID" required><br>
    <input type="password" name="pw" placeholder="Enter Password" required><br>
    <button type="submit">Join</button>
  </form>

  <?php if (isset($error)) echo "<p style='color:red;'>$error</p>"; ?>
  <?php if (isset($message)) echo "<p style='color:lightgreen;'>$message</p>"; ?>

  <a href="../04.php">Back to Main</a>

</body>
</html>
