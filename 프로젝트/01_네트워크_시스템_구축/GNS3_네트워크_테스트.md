---
# ACL
---
## Rule
<img src="https://github.com/user-attachments/assets/d7423734-08c6-416e-bd21-0c213e476ba2">

---
## Test
> GNS 버전 문제로 VPC의 telnet, http 기능에 제한이 있어 라우터로 대체했습니다.  
> ASAv에서 http는 이미지 파일 추가 다운로드가 필요하여 테스트는 telnet으로만 했습니다.
---

### 1. Firefox3(192.168.8.1, VPC 대신 라우터로 대체) -> inside(192.168.8.254) : telnet, http 접속  
<img src="https://github.com/user-attachments/assets/3f3cb8c4-ea25-4e98-bccc-52555caf5d56" width=500 height=300>  

### 2. Webterm2(192.168.16.1, R1 라우터(1.1.1.2)로 대체) -> dmz(1.1.1.1) : telnet 접속  
<img src="https://github.com/user-attachments/assets/0f392dd0-6518-4220-9aac-f5ad46a7aa6e" width=500 height=300>  

### 3. PC1(192.168.8.2) -> webterm1(192.168.24.1) : ping 가능  
<img src="https://github.com/user-attachments/assets/77fac993-641c-42ef-9550-641394483d52" width=500 height=200>  

### 4. webterm1(192.168.24.1, R2 라우터(2.2.2.2)로 대체) - R1(1.1.1.2) : http, telnet 가능  

**telnet**  
<img src="https://github.com/user-attachments/assets/e5a25c74-078d-4e24-99ff-7bbe886d1e39" width=500 height=300>  

**http**  
<img src="https://github.com/user-attachments/assets/a809c977-406a-4149-a120-7fee8173453e" width=500 height=200>

### 5. webterm2(192.168.16.1) -> PC1(192.168.8.2) : ping 가능  
<img src="https://github.com/user-attachments/assets/619145f3-3eab-49c8-aef0-c238c5615c00" width=500 height=300>  

---
# HSRP
---
## 라우터 설정
---

### R4
<img src="https://github.com/user-attachments/assets/747516f8-d1e9-45a9-a597-fb3a74e585ff" width=500 height=300>  

### R3
<img src="https://github.com/user-attachments/assets/e119ac4c-817a-43d4-81d9-981956b6c587" width=500 height=300>  

---
## 테스트
---
### 평상시
---

#### R4
<img src="https://github.com/user-attachments/assets/8c42ba25-e52c-4405-b923-c031cb664d6c" width=500 height=150>  

#### R3
<img src="https://github.com/user-attachments/assets/08ce5d9b-2675-4de2-8829-558438446eb4" width=500 height=150>  

#### tracert
<img src="https://github.com/user-attachments/assets/c9d0ddb9-6927-4239-8c2c-08e6f124ace5" width=500 height=100>  

---
### 장애 발생 시(f0/0 shutdown)
---

#### R4
<img src="https://github.com/user-attachments/assets/2f84f2b4-9d3e-4c83-b950-b3a1f0c1edd5" width=500 height=150>  

#### R3
<img src="https://github.com/user-attachments/assets/7f6da9ba-155d-4114-b422-88d888a50c8e" width=500 height=150>  

#### tracert
<img src="https://github.com/user-attachments/assets/e26d16f9-23b5-4675-98a2-8a823924daa2" width=500 height=100>  
