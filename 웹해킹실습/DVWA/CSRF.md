
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

'여기' 를 클릭하면 비밀번호 변경 페이지로 이동하면서 비밀번호 변경

이 때 주소창을 확인하면 password_new=hack&password_conf=hack&Change=click 로 되어 있음을 알 수 있음.

로그아웃하고 다시 로그인하면 변경된 비밀번호로 로그인 가능

### 페이지 소스

<img src=https://github.com/user-attachments/assets/065ab36b-3a50-4185-b75c-cb1a41f8c8f7 width=600>

페이지 소스를 확인해보면 변경할 비밀번호를 GET 방식으로 받고 입력된 값을 mysql_real_escape_string() 함수로 한번 필터링하고 변경

mysql_real_escape_string() 는 특수문자 앞에 \(백슬래시)를 붙여 이스케이프하기 위한 함수로 SQL Injection 공격 방지 위해 사용

GET 방식은 URL에 붙여서 데이터를 보내기 때문에 비밀번호의 변경과 같이 보안이 중요한 기능에는 적절한 방식이 아님

또한 비밀번호를 변경하는데 있어서 본인 확인 등 사용자 인증 절차가 없이 비밀번호 변경

이로 인해 CSRF 공격 가능

## Security Level : medium

### 풀이

![image](https://github.com/user-attachments/assets/a6fda992-04e1-4ac7-bad0-1fd28d4a8e61)

비밀번호 변경을 시도했으니 php버전 차이로 인해 eregi() 함수가 실행이 되지 않는 관계로 페이지 소스 분석만 함.

### 페이지 소스

![image](https://github.com/user-attachments/assets/88a7962e-a46b-44b8-8fa5-d2424c17cd9a)

if ( eregi ( "127.0.0.1", $_SERVER['HTTP_REFERER'] ) ){    → HTTP 헤더에 Referer 값에 127.0.0.1 이 있는지 여부 확인

![image](https://github.com/user-attachments/assets/90b367e7-fc87-4903-8b6b-c557af6e384e)

Security Level를 low로 바꾸고 비밀번호를 변경한 뒤 확인해보니 referer에는 url 주소 값이 입력되어 있음.

Security Level : low 와 비교했을 때 외부에서 CSRF 공격을 차단하기 위한 대책으로 이와 같은 방식을 사용

그러나 프록시로 잡은 뒤 Referer 값을 위조하여 전송하거나 같은 웹사이트 내 다른 게시판을 통해 CSRF 공격이 가능할 수 있음.

## Security Level : high

### 풀이

![image](https://github.com/user-attachments/assets/4fda246a-2cee-41a7-8098-376f95d51d64)

비밀번호를 변경하는데 있어서 현재 비밀번호가 필요

CSRF는 현재 비밀번호가 모르는 상태에서도 공격이 가능한 방식

현재 비밀번호를 알고 있다면 CSRF 공격을 할 필요가 없음

이러한 상황에서는 GET 방식을 사용하더라도 현재 비밀번호를 확인하는 과정을 거치기 때문에 CSRF 공격에 대응 가능

### 페이지 소스

![image](https://github.com/user-attachments/assets/cb684aac-4cad-4610-8a4b-c9e64a194097)

$pass_curr = $_GET['password_current'];   → 현재의 비밀번호를 입력받음

$pass_curr = stripslashes( $pass_curr );
$pass_curr = mysql_real_escape_string( $pass_curr );   → SQL Injection 공격 방지

## 대응방안

CSRF토큰 등을 사용하여 웹 사이트에 사용자 입력 값이 저장되는 페이지는 요청이 일회성이 될 수 있도록 설계

사용 중인 프레임워크에 기본적으로 제공되는 CSRF 보호 기능 사용

사용자가 정상적인 프로세스를 통해 요청하였는지 HTTP 헤더의 Referer 검증 로직 구현(eregi(), preg_match() 함수 사용)

정상적인 요청(Request)과 비정상적인 요청(Request)를 구분할 수 있도록 Hidden Form을 사용하여 임의의 암호화된 토큰(세션 ID, Timestamp, nonce 등)을 추가하고 이 토큰을 검증하도록 설계

HTML이나 자바스크립트에 해당되는 태그 사용(<script>, <img onerror=...> 등)을 사전에 제한하고, 서버 단에서 사용자 입력 값에 대한 필터링 구현

HTML Editor 사용으로 인한 상기사항 조치 불가 시, 서버 사이드/서블릿/DAO(Data Access Object) 영역에서 허용된 태그만 통과시키고 나머지는 제거하거나 escape 조치하도록 설계

