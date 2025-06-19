
# File Inclusion

## Security Level : low

### 풀이

![image](https://github.com/user-attachments/assets/07cff482-6d27-46ab-8a76-2b2af65e606b)

URL 주소를 보면 /?page=include.php 라고 되어있다. 이를 이용해서 다른 파일도 접근할 수 있는지 확인

![image](https://github.com/user-attachments/assets/4ec8a20b-4f08-4aa7-bd9e-8ba7ce9ec072)

/?page=/etc/passwd 를 입력하니 상단에 /etc/passwd 내용이 출력

### 페이지 소스

<img src=https://github.com/user-attachments/assets/570ce82a-bf5f-489e-82e2-306234f1b843 width=600>

해당 코드는 $_GET['page'] 파라미터로 전달된 값을 별도의 필터링이나 검증 없이 $file 변수에 그대로 할당

이처럼 사용자 입력값을 직접 사용하는 경우, 파일 포함(File Inclusion) 취약점(예: LFI, RFI)이 발생

## Security Level : medium

### 풀이



