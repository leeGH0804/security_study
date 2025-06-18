
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

![image](https://github.com/user-attachments/assets/cef3ec15-cbdc-4d57-956e-6b8c412208cc)

이미지와 같이 특수문자를 이용하여 다중 명령을 실행하려고 하면 ERROR: You have entered an invalid IP 와 같은 오류 메시지가 나타남.

### 페이지 소스

<img src=https://github.com/user-attachments/assets/13ffe219-aef0-4b78-bc0b-7b2c1d513999 width=600>

$target = stripslashes( $target );

입력한 값(target)에서 \(역슬래시) 값을 제거하고,  

$octet = explode(".", $target);  

.(마침표)를 기준으로 입력한 값을 나눔.  

if ((is_numeric($octet[0])) && (is_numeric($octet[1])) && (is_numeric($octet[2])) && (is_numeric($octet[3])) && (sizeof($octet) == 4)  ) {   

나눈 값들이 숫자인지 확인  

$target = $octet[0].'.'.$octet[1].'.'.$octet[2].'.'.$octet[3];  

나눈 값을 .(마침표)로 이어 붙임.  

is_numeric 이라는 함수 때문에 특수문자를 사용하면 조건에 만족하지 않아 에러 메시지가 출력됨.

※ is_numeric 우회

is_numeric 함수의 결과가 true 값이 나와야 $cmd = shell_exec( 'ping  ' . $target ); 코드가 실행될 수 있음.  

그래서 우회할 수 있는지 여부에 대해 알기 위해 is_numeric 함수에 대해 조사.  

https://www.php.net/manual/en/function.is-numeric.php  

PHP 홈페이지에서 is_numeric 함수에 대해 찾아보면 Returns true if value is a number or a **numeric string**, false otherwise. 라고 나옴.

**테스트**

![image](https://github.com/user-attachments/assets/87d67559-b701-4413-9606-eed916990456)

16진수(Hex)도 입력하면 통과됨. 근데 10진수로 변환하므로 command injection으로 이어지기는 어려워보임.

![image](https://github.com/user-attachments/assets/dff46931-f49a-4951-bbd2-3a3f35ae7479)

.(마침표)로 나눴을 때 제일 앞의 숫자에 공백을 넣어도 ping 함수가 실행됨. 반면, 첫번째 이외에 숫자에는 공백을 넣으면 오류 메세지를 포함해서 아무런 출력이 되지 않음.  

예를 들어, 12. 12.12.12를 입력하면 ping 12. 12.12.12 이 되어 함수 실행에 오류가 발생해 아무런 출력이 되지 않는 것으로 보임.  

is_numeric 함수로 인해 ;(세미클론)과 같은 특수문자나 알파벳이 필터링되어 대부분의 command injection 공격을 차단될 것으로 보임.

다만, PHP 홈페이지에서 is_numeric 예제 중에

foreach ($tests as $element) {
    if (is_numeric($element)) {
        echo var_export($element, true) . " is numeric", PHP_EOL;
    } else {
        echo var_export($element, true) . " is NOT numeric", PHP_EOL;
    }
}
 
코드에서 '1337e0' is numeric 로 보아 지수 표현을 허용하는 것을 알 수 있음. 그래서 지수 표현식 + 형 변환 과정(1.234e+5)을 통해 특정 조건에 맞는 숫자를 입력하여 우회할 수 있음.






