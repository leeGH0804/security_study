
# Brute Force(무차별 대입 공격)

## Security Level : Low

### 풀이

![image](https://github.com/user-attachments/assets/bc2e4c48-49a5-432c-b7dd-c2cae3755d13)

좌측 하단에 username: admin이라고 되어 있다. 그리고 로그인을 실패했을 때 "Username and/or password incorrect." 라는 메시지가 출력

이를 이용해서 hydra를 사용해서 비밀번호를 찾기

<img src=https://github.com/user-attachments/assets/fbfb341c-6c73-4582-8e17-1693c05f1edd width=500>

hydra -l admin -P /usr/share/wordlists/rockyou.txt 192.168.56.110 http-get-form "/vulnerabilities/brute/:username=^USER^&password=^PASS^&Login=Login:H=Cookie:PHPSESSID=j0hhk5h9tv98ldtfn6aajf83h6; security=low:F=Username and/or password incorrect."

username: admin  
password : password

![image](https://github.com/user-attachments/assets/9e8950f1-766e-4c92-94c6-d2b8330dc09d)

로그인 성공!

### 페이지 소스

<img src=https://github.com/user-attachments/assets/fc1852e5-049d-4453-bda0-b9659fef4229 width=600>

필터 없이 입력값을 받아서 sql injection 공격도 가능  

SELECT * FROM `users` WHERE user='$user' AND password='$pass';  

SELECT * FROM `users` WHERE user='admin' -- ' AND password='$pass'; 로 입력되어 -- 뒤에 부분은 주석처리됨.  

따라서, SELECT * FROM `users` WHERE user='admin' -- 되어 user가 admin에 해당하는 모든 값을 조회

![image](https://github.com/user-attachments/assets/fc27cae2-8f5c-4c02-9ece-78353e8bdbb0)

로그인 성공!

## Security Level : Medium

### 풀이

이번에는 burp suite를 이용하여 brute force 공격을 시도

![image](https://github.com/user-attachments/assets/a5909784-27ef-4fe4-bc08-f3f1afaf0d19)

Payload값이 password일 때 Length 값이 5053으로 다르다는 것을 확인

### 페이지 소스

<img src=https://github.com/user-attachments/assets/d60ce18b-f009-4722-a0ed-d33f3f580bfd width=600>

$user = mysql_real_escape_string( $user );   
$pass = mysql_real_escape_string( $pass ); 추가됨  

mysql_real_escape_string : 특수 문자열을 이스케이프하는 함수  

$pass = md5( $pass ); : 입력받은 비밀번호를 md5로 암호화하여 조회

따라서 low와 동일하게 admin' -- 를 입력하면  

SELECT * FROM `users` WHERE user='admin\' -- ' AND password='$pass'; 와 같이 입력됨.

그러므로 low와 같은 방식으로는 SQL Injection이 적용되지 않음.

※ mysql_real_escape_string 우회 방법

멀티바이트를 사용하는 언어셋 환경에서는 백슬래시 앞에 %a1~%fe 의 값이 들어오면 %a1\가 한 개의 문자처럼 취급됨.  

%a1'를 입력하면 %a1\'이 되고, %a1%5c%27이 됨. 멀티바이트를 사용하는 언어셋 환경에서는 %a1%5c를 하나의 문자로 보아 이 둘을 묶음. 그렇게 되면 이스케이프 문자는 없어지고 '만 남게됨.

이를 이용하여 %a1' or 1=1 # 를 입력하여 mysql_real_escape_string 함수를 우회할 수 있음.

※ 멀티바이트를 사용하는 언어셋 환경

다양한 언어의 문자를 표현하기 위해 1바이트 이상을 사용하는 문자 인코딩 방식. 멀티바이트 문자셋에는 ', \ 와 같은 특수문자가 한 글자의 일부로 들어갈 수 있음.  

힌트가 되는 함수 : mb_convert_encoding()

## Security Level : high

### 풀이

![image](https://github.com/user-attachments/assets/e0da81f8-6183-40b7-b22c-d54165e75a8b)

OWASP ZAP으로 brute force를 실행한 결과 페이로드 값에 password 일 때 Reflected 표시가 나타남.

### 페이지 소스

<img src=https://github.com/user-attachments/assets/8547e8b9-8891-4611-946f-1e049e7f54ce width=600>

$user = stripslashes( $user );  
$pass = stripslashes( $pass );  

stripslashes : 백슬래시 제거하는 함수

구버전 php의 기능 중 하나인 magic_quotes_gpc는 특수문자 앞에 자동으로 \를 붙여주는 기능

앞에서 언급한 것처럼 멀티바이트를 사용하는 언어셋 환경의 경우 이를 우회할 수 있고 그대로 적용된다면 SQL이 정상적으로 작동하지 않을 가능성이 있음.

그래서 원래의 입력값으로 데이터를 복구하기 위해 stripslashes로 \를 지워줌.  

그리고 mysql_real_escape_string()로 SQL 기준으로 이스케이프 처리를 다시 함.  

## 대응방안

위와 코드 변경이 있어도 brute force 공격은 가능.  

brute force 공격의 대응 방안으로 로그인 횟수를 제한하거나 captcha 활용, 공격을 감지하고 방어할 수 있는 IDS/IPS 구축과 모니터링이 있음.






