
DVWA v1.0.7

# CSRF(Cross Site Request Forgery)

## Security Level : low

### 풀이

![image](https://github.com/user-attachments/assets/547adf2a-42a8-42dd-81fb-fcbb4fc0bfb4)

비밀번호를 변경하는 페이지

![image](https://github.com/user-attachments/assets/a0098882-cd8a-41c6-8391-f84d98463d26)

비밀번호를 변경하면 주소창에 password_new=1234&password_conf=1234&Change=Change 가 입력되어 변경된 패스워드가 암호화되지 않은 상태로 그대로 들어남.

해당 페이지의 소스를 확인하면

![image](https://github.com/user-attachments/assets/8f17c93e-a6b5-473f-b867-fc6110ccc645)

비밀번호를 변경할 때 GET 방식으로 전송한다는 것을 알 수 있음.

그리고 burp suite로 비밀번호 변경 당시를 확인해보면

![image](https://github.com/user-attachments/assets/16758bea-bfb4-4f50-b161-42afac632a85)

GET /vulnerabilities/csrf/?password_new=1234&password_conf=1234&Change=Change HTTP/1.1 로 GET 방식으로 요청(Request)

이를 이용하여 CSRF 공격 시도

![image](https://github.com/user-attachments/assets/f3827ee7-f215-48ad-ba34-e89ab11757c9)

비밀번호 변경 페이지 소스를 이용하여 CSRF용 페이지를 임시로 제작

<img src=https://github.com/user-attachments/assets/2f2b254a-eef1-4161-97fa-1689200e393d width=500>

Gmail을 통해 링크를 걸어 메일 전송

![image](https://github.com/user-attachments/assets/e3a76824-90dc-4a7f-8986-8a6142436c0d)

같은 브라우저에 DVWA에 로그인(Security Level:low로 설정)

![image](https://github.com/user-attachments/assets/4d5232a1-6bf6-481e-95a0-5fbfdf2a208c)
![image](https://github.com/user-attachments/assets/4d5232a1-6bf6-481e-95a0-5fbfdf2a208c)

'여기' 를 클릭하면 비밀번호 변경 페이지로 이동하면서 비밀번호 변경

이 때 주소창을 확인하면 password_new=hack&password_conf=hack&Change=click 로 되어 있음을 알 수 있음.

로그아웃하고 다시 로그인하면 변경된 비밀번호로 로그인 가능

### 페이지 소스

<img src=https://github.com/user-attachments/assets/065ab36b-3a50-4185-b75c-cb1a41f8c8f7 width=600>

페이지 소스를 확인해보면 변경할 비밀번호를 GET 방식으로 받고 입력된 값을 mysql_real_escape_string 함수로 한번 필터링하고 변경

mysql_real_escape_string 는 특수문자 앞에 \(역슬래시)를 붙여 이스케이프하기 위한 함수로 SQL Injection 공격 방지 위해 사용

GET 방식은 URL에 붙여서 데이터를 보내기 때문에 비밀번호의 변경과 같이 보안이 중요한 기능에는 적절한 방식이 아님

또한 비밀번호를 변경하는데 있어서 본인 확인 등 사용자 인증 절차가 없이 비밀번호 변경

이로 인해 CSRF 공격 가능

## Security Level : medium

### 풀이



### 페이지 소스







