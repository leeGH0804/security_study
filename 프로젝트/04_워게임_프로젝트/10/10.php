<?php
session_start();
require_once '../../includes/db.php';

ini_set('display_errors', 1);
error_reporting(E_ALL);

if (!isset($_SESSION['user_id'])) {
    header("Location: ../../index.php");
    exit;
}

$user_id = $_SESSION['user_id'];
$current_sid = session_id();

$stmt = $mysqli->prepare("SELECT session_id FROM users WHERE id = ?");
$stmt->bind_param("i", $user_id);
$stmt->execute();
$db_sid = $stmt->get_result()->fetch_assoc()['session_id'] ?? '';

if ($db_sid !== $current_sid) {
    session_unset();
    session_destroy();
    header("Location: ../../index.php");
    exit;
}


// 좌표 조작 (Burp 등에서 x, y 보낼 경우)
if ($_SERVER["REQUEST_METHOD"] === "POST" && isset($_POST["x"]) && isset($_POST["y"])) {
  $x_post = intval($_POST["x"]);
  $y_post = intval($_POST["y"]);
  if ($x_post >= 0 && $x_post <= 4 && $y_post >= 0 && $y_post <= 4) {
    $_SESSION["destination"] = ["x" => $x_post, "y" => $y_post];
    unset($_SESSION["dir_count"], $_SESSION["total"], $_SESSION["count"]);
  }
}

// 초기화 버튼 눌렀을 때
if ($_SERVER["REQUEST_METHOD"] === "POST" && isset($_POST["reset"])) {
  $_SESSION["current"] = ["x" => 0, "y" => 0];
  $_SESSION["count"] = 0;
  unset($_SESSION["dir_count"], $_SESSION["total"]);
}

// 현재 상태 불러오기
$current = $_SESSION["current"] ?? ["x" => 0, "y" => 0];
$destination = $_SESSION["destination"] ?? ["x" => 3, "y" => 2];
$x = $current["x"];
$y = $current["y"];
$tx = $destination["x"];
$ty = $destination["y"];
?>
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>TimeMachine10</title>
  <style>
    body { background: black; color: white; font-family: monospace; text-align: center; }
    .map { display: grid; grid-template-columns: repeat(5, 40px); grid-template-rows: repeat(5, 40px); gap: 5px; justify-content: center; }
    .cell { width: 40px; height: 40px; background: #222; display: flex; align-items: center; justify-content: center; border: 1px solid #555; }
    .car { background-color: #0f0; }
    .goal { background-color: #f00; }
  </style>
</head>
<body>
  <h1>No.10 Autonomous Driving</h1>
  <p style="color: #ccc;">Hint: Submit the hacking coordinates.</p>

  <div class="map" id="map">
    <?php
    for ($gy = 4; $gy >= 0; $gy--) {
      for ($gx = 0; $gx < 5; $gx++) {
        $cls = "cell";
        $content = "&nbsp;";
        if ($gx === $tx && $gy === $ty) {
          $cls .= " goal";
          $content = "🏁";
        }
        echo "<div class='$cls'>$content</div>";
      }
    }
    ?>
  </div>

  <p>Current Position: (<span id="pos-x"><?= $x ?></span>, <span id="pos-y"><?= $y ?></span>)</p>
  <p>Moved: <span id="count"><?= $_SESSION["count"] ?? 0 ?></span> / <span id="total"><?= $_SESSION["total"] ?? "?" ?></span> steps</p>

  <p id="status-message"></p>

  <button onclick="startMove()">🚀 Move to Destination</button>

  <form method="post" action="10.php">
    <button type="submit" name="reset" value="1" style="color:red;">🧹 Reset</button>
  </form>

  <script>
    const map = document.getElementById("map");
    const status = document.getElementById("status-message");

    function startMove() {
      fetch("move.php", { method: "POST" })
        .then(res => res.json())
        .then(data => {
          document.getElementById("pos-x").textContent = data.current.x;
          document.getElementById("pos-y").textContent = data.current.y;
          document.getElementById("count").textContent = data.count;
          document.getElementById("total").textContent = data.total;

          const cells = map.querySelectorAll(".cell");
          cells.forEach(cell => {
            cell.classList.remove("car");
            if (!cell.classList.contains("goal")) cell.innerHTML = "&nbsp;";
          });

          const carIndex = (4 - data.current.y) * 5 + data.current.x;
          cells[carIndex].classList.add("car");
          cells[carIndex].innerHTML = "🚗";

          if (data.success) {
            status.innerHTML = '<span style="color: lime;">✅ Success! Back to main...</span>';
            setTimeout(() => location.href = "../../main.php", 2000);
          } else if (data.current.x === data.destination.x && data.current.y === data.destination.y) {
            status.innerHTML = '<span style="color: orange;">❌ You have not hacked the destination yet.</span>';
          } else {
            status.innerHTML = "";
          }

          if (data.count === data.total && data.current.x === data.destination.x && data.current.y === data.destination.y) {
            return; // Stop after final move
          }

          setTimeout(startMove, 300);
        });
    }

    window.onload = () => {
      const x = parseInt(document.getElementById("pos-x").textContent);
      const y = parseInt(document.getElementById("pos-y").textContent);
      const cells = map.querySelectorAll(".cell");
      const carIndex = (4 - y) * 5 + x;
      cells[carIndex].classList.add("car");
      cells[carIndex].innerHTML = "🚗";
    }
  </script>
<?php include '../../includes/ping_loader.php'; ?>
<script src="../../js/inactivity.js"></script>

</body>
</html>
