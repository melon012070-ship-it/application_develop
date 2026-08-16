package hello;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Scanner;

public class PhoneBook {
public static void main(String[] args)
{
	Scanner scanner=new Scanner(System.in);
	String filepath="C:\\Users\\melon\\Desktop\\phone.txt";
	
	
	try {
		FileWriter writer=new FileWriter(filepath);
		System.out.println("전화번호 입력 프로그램입니다.");
		
	
	while(true) {
		System.out.println("이름 전화번호>>");
		String name=scanner.next();
		
		if(name.equals("그만")) {
			break;
		}
		
	
	String phone=scanner.next();
	writer.write(name+" "+phone+"\n");
	}
	
	writer.close();
	System.out.println(filepath+"에 저장하였습니다.");
	}
	
	catch(IOException e) {
		System.out.println("파일 저장 중 오류 발생"+e.getMessage());
		
	}
	
	scanner.close();
}
}

	
