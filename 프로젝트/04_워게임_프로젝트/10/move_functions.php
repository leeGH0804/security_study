<?php
function generate_total_and_path() {
    $dx = $_SESSION["destination"]["x"];
    $dy = $_SESSION["destination"]["y"];
    while (true) {
        $total = rand(10, 15);
        for ($l = 0; $l <= $total; $l++) {
            for ($r = 0; $r <= $total; $r++) {
                for ($u = 0; $u <= $total; $u++) {
                    for ($d = 0; $d <= $total; $d++) {
                        if ($l + $r + $u + $d === $total && $r - $l === $dx && $u - $d === $dy) {
                            $_SESSION["total"] = $total;
                            $_SESSION["dir_count"] = ["left" => $l, "right" => $r, "up" => $u, "down" => $d];
                            return;
                        }
                    }
                }
            }
        }
    }
}

function move_one_step() {
    $cur = &$_SESSION["current"];
    $dirs = &$_SESSION["dir_count"];
    $available = [];
    foreach ($dirs as $dir => $val) {
        if ($val > 0) $available[] = $dir;
    }
    if (!$available) return;
    $choice = $available[array_rand($available)];
    $next = $cur;
    if ($choice === "left") $next["x"]--;
    if ($choice === "right") $next["x"]++;
    if ($choice === "up") $next["y"]++;
    if ($choice === "down") $next["y"]--;
    if ($next["x"] < 0 || $next["x"] > 4 || $next["y"] < 0 || $next["y"] > 4) return;
    if ($next == $_SESSION["destination"] && $_SESSION["count"] != $_SESSION["total"] - 1) return;
    $_SESSION["current"] = $next;
    $dirs[$choice]--;
    $_SESSION["count"]++;
}

function check_and_reset() {
    if ($_SESSION["count"] === $_SESSION["total"] &&
        $_SESSION["current"] === $_SESSION["destination"]) {
        $_SESSION["current"] = ["x" => 0, "y" => 0];
        $_SESSION["count"] = 0;
        unset($_SESSION["total"], $_SESSION["dir_count"]);
    }
}
