import java.util.Scanner;

public class HW2 {
	public static void main(String[] args) {
	System.out.println("[if , else 문을 사용해서 계산기 프로그램 만들기 실시]");
	

	int one = 0; 		
	int two = 0;
	
	
	String sign = "";
	
	
	Scanner scan = new Scanner(System.in);
	

	System.out.print("첫번째 값 : ");
	one = scan.nextInt();
	
	System.out.print("두번째 값 : ");
	two = scan.nextInt();
	
	System.out.print("사칙연산부호 (+,-,*,/) : ");
	sign = scan.next();
	
	
	if(sign.equals("+")) {
		System.out.println(one+"+"+two+"="+(one+two));
	}
	else if(sign.equals("-")) {
		System.out.println(one+"-"+two+"="+(one-two));
	}
	else if(sign.equals("*")) {
		System.out.println(one+"*"+two+"="+(one*two));
	}
	else if(sign.equals("/")) {
		System.out.println(one+"/"+two+"="+(one/two));
	}
	else {
		System.out.println("알수없는 연산자입니다 ... ");
	}
			
}
}



