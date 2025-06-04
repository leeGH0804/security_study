<?php
session_start();
header('Content-Type: application/json');
ini_set('display_errors', 1);
error_reporting(E_ALL);
require_once("move_functions.php");
require_once __DIR__ . '/../../includes/db.php';

if (!isset($_SESSION['user_id'])) {
  echo json_encode(["error" => "Not logged in"]);
  exit;
}

$user_id = $_SESSION['user_id'];
$owner = "timemachine";
$number = 10;

$stmt = $mysqli->prepare("SELECT id FROM problems WHERE owner = ? AND number = ?");
$stmt->bind_param("si", $owner, $number);
$stmt->execute();
$problem = $stmt->get_result()->fetch_assoc();
if (!$problem) {
  echo json_encode(["error" => "Problem not found"]);
  exit;
}
$problem_id = $problem["id"];

if (!isset($_SESSION["count"])) $_SESSION["count"] = 0;
if (!isset($_SESSION["current"])) $_SESSION["current"] = ["x" => 0, "y" => 0];
if (!isset($_SESSION["destination"])) $_SESSION["destination"] = ["x" => 3, "y" => 2];
if (!isset($_SESSION["total"]) || !isset($_SESSION["dir_count"])) {
  generate_total_and_path();
}

move_one_step();

$current = $_SESSION["current"];
$destination = $_SESSION["destination"];
$count = $_SESSION["count"];
$total = $_SESSION["total"];
$success = ($destination["x"] === 4 && $destination["y"] === 3 && $current["x"] === 4 && $current["y"] === 3);
$done = ($count === $total && $current == $destination);

// 도착 시 DB 기록
if ($success) {
  $stmt = $mysqli->prepare("SELECT id FROM clears WHERE user_id = ? AND problem_id = ?");
  $stmt->bind_param("ii", $user_id, $problem_id);
  $stmt->execute();
  $already = $stmt->get_result()->fetch_assoc();
  if (!$already) {
    $stmt = $mysqli->prepare("INSERT INTO clears (user_id, problem_id) VALUES (?, ?)");
    $stmt->bind_param("ii", $user_id, $problem_id);
    $stmt->execute();
  }
}

// 리셋
if ($done) {
  $_SESSION["current"] = ["x" => 0, "y" => 0];
  $_SESSION["count"] = 0;
  unset($_SESSION["total"], $_SESSION["dir_count"]);
}

echo json_encode([
  "current" => $current,
  "destination" => $destination,
  "count" => $count,
  "total" => $total,
  "success" => $success
]);
