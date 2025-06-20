
DVWA v1.0.7

# File Inclusion

## Security Level : low

### 풀이

![image](https://github.com/user-attachments/assets/07cff482-6d27-46ab-8a76-2b2af65e606b)

URL 주소를 보면 /?page=include.php 라고 되어 있음. page의 파라미터로 전달된 값을 화면에 출력하는 것으로 보임. 이를 이용

![image](https://github.com/user-attachments/assets/4ec8a20b-4f08-4aa7-bd9e-8ba7ce9ec072)

/?page=/etc/passwd 를 입력하니 상단에 /etc/passwd 내용이 출력(LFI)

![image](https://github.com/user-attachments/assets/b0853c50-80db-472b-8339-14a23cf59b01)

![image](https://github.com/user-attachments/assets/d3efde0b-3dfb-4665-b468-325f4ac6ac76)


page의 파라미터 값으로 csrf에서 사용했던 http 주소를 입력하니 csrf.html이 실행되면서 비밀번호가 hack123으로 변경됨(RFI)

### 페이지 소스

<img src=https://github.com/user-attachments/assets/570ce82a-bf5f-489e-82e2-306234f1b843 width=600>

해당 코드는 $_GET['page'] 파라미터로 전달된 값을 별도의 필터링이나 검증 없이 $file 변수에 그대로 할당

이처럼 사용자 입력값을 직접 사용하는 경우, 파일 포함(File Inclusion) 취약점(예: LFI, RFI)이 발생

## Security Level : medium

### 풀이

![image](https://github.com/user-attachments/assets/338eb960-9795-4977-8c55-f958624d9f63)

LFI 공격은 그대로 가능

![image](https://github.com/user-attachments/assets/9911c3fb-f4c0-4e6f-9566-4805b7c15c81)

RFI 공격은 차단됨

### 페이지 소스

<img src=https://github.com/user-attachments/assets/fcb16351-6d7e-4025-b7a3-5aeeba63feb8 width=600>

http나 https는 공백으로 대체하여 RFI공격은 차단

## Security Level : high

### 풀이

![image](https://github.com/user-attachments/assets/863a488d-767c-419e-91a6-9f58dc098436)

/etc/passwd 를 입력하여 LFI 공격을 시도하면 ERROR: File not found! 라는 오류 메시지가 발생

### 페이지 소스

![image](https://github.com/user-attachments/assets/e69ad4cc-44fa-4ecd-9b84-83eb915ad5a3)

해당 코드는 파라미터를 통해 전달된 값이 "include.php"와 정확히 일치하는 경우에만 처리를 허용

그 외의 입력은 "ERROR: File not found!"를 출력하며 실행을 종료

즉, include.php 파일만 허용하고 모든 다른 파일 요청은 차단하는 구조

다만, 이러한 방식의 경우 허용할 파일이 많거나 파일명이 어렵다면 적용하기 어렵다는 단점 존재

## 대처 방안

웹 사이트에서 접근하려는 파일이 있는 디렉터리에 chroot 환경 적용

※ chroot 환경

현재의 루트 디렉토리를 변경하여 가상의 격리된 파일 시스템 환경

애플리케이션 소스 파일을 수정하여 파일 내용을 웹 브라우저에 표시할 수 있는 디렉터리를 특정 디렉터리로 한정하고 이 외의 다른 디렉터리에서는 파일 내용을 표시할 수 없도록 설정

PHP를 사용하는 경우 php.ini 에서 magic_quotes_gpc를 On으로 설정하여 '(싱글 쿼트), "(더블 쿼트), \(백슬래시), NULL(널 바이트) 입력 시 \(백슬래시)로 치환되도록 설정(php 7.4.0부터 사용되지 않, php 8.0부터 제거)

웹 사이트에서 사용되는 파라미터 값 대상으로 특수 문자를 필터링하도록 웹 방화벽(WAF) 룰셋 적용
