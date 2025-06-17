
DVWA v1.0.7

# Command_Execution

## Security Level : low

### 풀이

![image](https://github.com/user-attachments/assets/2a842393-5cd1-4c5e-99f4-76f68f0a20f6)

IP 주소를 입력했을 때 ping 명령어가 실행되어 출력되는 것을 알 수 있음.

![image](https://github.com/user-attachments/assets/df6497e8-c419-40ee-9d64-1a9886a7953e)

;(세미클론)을 이용해서 여러 개의 명령어 입력. cat /etc/passwd 명령어를 이용하여 계정 정보를 확인 가능.

### 페이지 소스

<img src="https://github.com/user-attachments/assets/7cad35e4-ab19-409d-ac8b-2a18ebbcc27c" width=600>

$target = $_REQUEST[ 'ip' ];

$cmd = shell_exec( 'ping  ' . $target );

$cmd = shell_exec( 'ping  -c 3 ' . $target );

사용자로부터 입력받은 IP 주소 $target 값을 별도의 필터링 없이 shell_exec() 함수에 직접 전달하고 있으며, 입력값 검증이 없기 때문에 공격자는 ;(세미클론) 문자를 이용해 여러 명령어를 연속으로 실행 가능.  

이로 인해 시스템 명령어를 삽입하는 명령어 삽입(Command Injection) 공격이 발생.  

## Security : medium

### 풀이

![image](https://github.com/user-attachments/assets/1dc7c001-222e-42b0-b36e-d7963cd794b8)

;(세미클론) 와 &&(더블 엠퍼센트) 는 되지 않지 다중 명령을 사용할 수 있도록 해주는 다른 특수 문자인 |(버티컬 바) 와 &(엠퍼센트) 를 이용하면 명령어 삽입(Command Injection) 성공.

### 페이지 소스

<img src=https://github.com/user-attachments/assets/a91ed6a9-8a1e-4535-a171-cf84d2aa77da width=600>

$substitutions = array(
        '&&' => '',
        ';' => '',
    );

로 보아 &&(더블 엠퍼센트)와 ;(세미클론)만을 공백으로 대체하는 것을 알 수 있음.  

따라서, &&(더블 엠퍼센트)와 ;(세미클론)을 제외한 특수 문자를 이용하여 다중 명령 실행 가능.

## Security : high

### 풀이



### 페이지 소스

<img src=https://github.com/user-attachments/assets/13ffe219-aef0-4b78-bc0b-7b2c1d513999 width=600>




